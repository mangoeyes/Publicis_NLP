
# coding=utf-8

"""  
Created on 2017-07-17 
@author: SueWang
功能: 使用requests库爬取宝宝树网的搜索结果，抓取最近一天内发布的帖子
网址：http://www.babytree.com/
2017-07-25 注意IP访问问题 防止被封
继续添加注释
"""
import os
import re
import time
import queue
import random
import datetime
import requests
import threading
from bs4 import BeautifulSoup
import pandas as pd

# 线程锁 防止多线程同时读写数据
mutex = threading.RLock()
mutex2 = threading.Lock()
q = queue.Queue() #创建任务队列
WORKER_NUM = 4


#继承Thread的Producer类 负责将从网站抓取到的链接放入队列
class urlProducer(threading.Thread):
    
    def __init__(self,keyword, url):
        super(urlProducer,self).__init__()
        self.keyword = keyword
        self.url = url
        
        
    def run(self):
        global q
        if not (isinstance(self.keyword, str) and isinstance(self.url,str)):
            raise TypeError('parameter is not str')

        l = getThreadUrl(self.keyword,self.url)
        if mutex2.acquire(1):
            a = list(map(q.put, l))
            mutex2.release()
 

# 继承Thread的Consumer类 负责从队列中取出链接 爬取文章的信息
class urlConsumer(threading.Thread):
    
    def __init__(self):
        super(urlConsumer,self).__init__()
        
    def run(self):
        global q
        if mutex.acquire(1):
            if mutex2.acquire(1):
                if not q.empty():
                    url = q.get()
                    getPageContent(url)
                mutex2.release()
            mutex.release()

def getPageUrl(keyword):
    random.seed()
    TIMER = random.randint(5,10)
    time.sleep(TIMER)
    
    search_url = 'http://www.babytree.com/s.php'
    
#    q:搜索关键词
#    c:搜索结果类型，'community'为帖子
#    cid:搜索圈子类型（在页面左侧）
#    range:d - 最近一天    w - 最近一周    m - 最近一月
    param = {'q':keyword,'c':'community','cid':'0','range':'w'}
    header = {'User-Agent':'"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0)'+
              'Gecko/20100101 Firefox/52.0"'}

    html = requests.get(search_url, params = param, headers = header)        
    bs = BeautifulSoup(html.content,'lxml')
    htmls = [html.url]
    page_url = search_url + '?'
    for key,value in param.items():
        page_url += key + '=' + value + '&'
    if bs.find(class_ = 'page-number'):
        totalPageNum = bs.find(class_ = 'page-number').text
        totalPageNum = int(totalPageNum[1:len(totalPageNum)-1])
        htmls.pop(0)
        htmls = [page_url + 'pg=' + str(i+1) for i in range(totalPageNum)]
    return htmls
        
def getThreadUrl(keyword, url):
    
    TIMER = random.randint(5,10)
    time.sleep(TIMER)
    
    html = requests.get(url)
    bs = BeautifulSoup(html.content,'lxml')
    list = []
    
    if bs.find(class_ = 'search_result'):
        print('no search result')
        return

    else:
        try:
            posts = bs.findAll(class_ = 'search_item_tit')
            
            for post in posts:
                if keyword in post.text:
                    list.append(post.a['href'])
                    
        except Exception as e:
            print(e)
    
    return list
    
#在页面有内容的前提下，获取内容
def getPageContent(url):
    
    global data
    html = requests.get(url)
    soup = BeautifulSoup(html.content,'lxml')
    
    url_time = ""
    url_author = ""
    url_title = ""
    url_content = ""
    
    try: 
        url_time = soup.find(class_='postTime').text
        pattern = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}')
        url_date = re.findall(pattern, url_date)[0]
    except:
        pass
    try:
        url_author = soup.find(class_='userName').a.text
        pattern = re.compile(r"'.+'")
        url_author = re.findall(pattern, url_author)[0]
        url_author = re.sub("'","",url_author)
    except:
        pass
    try:
        url_title = soup.find(id = 'DivHbbs').text.strip()
    except:
        pass
    try:
        url_content = soup.find(id = 'topic_content').text.strip()
        url_content = re.sub('[(\r)|(\n)]+',"",url_content)
    except:
        pass
    
    result = {'time':url_time,'author':url_author,'title':url_title,'content':url_content}
    data.append(result)

#获取当前用时
def getUsedTime(start_time):
    
    if not isinstance(start_time,datetime.datetime):
        raise TypeError('start time is not a datetime.datetime')
        
        
    use_time = (datetime.datetime.now() - start_time).total_seconds()
    m, s = divmod(use_time, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)

#*******************************************************************************
#                                程序入口
#*******************************************************************************
if __name__ == '__main__':

    folder_path = 'C:/Users/suewang/desktop/python/TM/milk_powder'
    df_keys = pd.read_excel(folder_path+'/search_keywords.xlsx', sheetname = 0,header = 0)
    if not os.path.isdir(folder_path + '/crawl_result/babytree'):
        os.makedirs(folder_path + '/crawl_result/babytree')
    
    for row in df_keys.iterrows():
        data = []
        try:
            keyword = row[1][0]
            print('开始抓取关键词：' + keyword + ' ...')
            start_time = datetime.datetime.now()
            today = start_time.strftime('%Y-%m-%d')    
            pageUrl = getPageUrl(keyword)
            
            producer_thread = []
            for page in pageUrl:
                t = urlProducer(keyword, page)
                producer_thread.append(t)
                t.start()
            for t in producer_thread:
                t.join()
    
            print('帖子链接抓取完成，用时：'+ getUsedTime(start_time) + 
                  '\n共有' + str(len(pageUrl)) + '页帖子')
            threads = []
            while not q.empty():
                for i in range(WORKER_NUM):
                    thread = urlConsumer()
                    threads.append(thread)
                    thread.start()
                for thread in threads:
                    thread.join()
                    
            result = pd.DataFrame(data, columns = ['time','title','author','content'])
            file_path = folder_path + "/crawl_result/babytree/" + keyword + '_' + today + '.xlsx'
            result.to_excel(file_path,encoding = 'utf-8',index = False)
            print( "关键词 " + keyword + ' 帖子抓取完成' 
            + '\n总用时：'+ getUsedTime(start_time) + '\n')
            
            time.sleep(2)
        except Exception as e:
            print(e)
    print('抓取结束')        