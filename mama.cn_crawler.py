
# coding=utf-8

"""  
Created on 2017-07-13 
@author: SueWang
功能: 使用requests库爬取妈妈网一周内的搜索结果
网址：http://so.mama.cn/
"""
import os
import re
import time
import math
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
random.seed()

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
    
    TIMER = random.randint(2,5)
    time.sleep(TIMER)
    
    search_url = 'http://so.mama.cn/search'
    
#    参数
#    q: 搜索关键词
#    source: 搜索结果类别, 'mamaquan'是帖子
#    csite: 不知道是什么
#    size: 每页显示结果数量
#    sortMode: 也不知道是什么 改成2 3 4 好像也没变化
#    dateline: 搜索结果时间
#              all - 全部时间
#              year - 一年内
#              month - 一个月内
#              week - 一周内
#              day - 一天内
    
    param = {'q':keyword,'source':'mamaquan','csite':'all','size':'50',
             'sortMode':'1', 'dateline':'week'}
    header = {'User-Agent':'"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0)'+
              'Gecko/20100101 Firefox/52.0"'}

    html = requests.get(search_url, params = param, headers = header)   
    bs = BeautifulSoup(html.content,'lxml')
    total_result = bs.find(class_ = 'search-body__text').span.get_text()
    total_result = int(total_result[:len(total_result)-1])
    htmls = []
    
    if not total_result == 0:
       pageNum = math.ceil(total_result/50)
       
       pageLink = search_url + '?'
       
       for (key,value) in param.items():
           pageLink += (key + '=' + value + '&')
       
       htmls = [pageLink + 'page=' + str(i + 1) for i in range(pageNum)]
        
    return htmls
        
def getThreadUrl(keyword, url):
    
    TIMER = random.randint(5,10)
    time.sleep(TIMER)
    
    html = requests.get(url)
    bs = BeautifulSoup(html.content,'lxml')
    list = []
    
    if bs.find(class_ = 'search-body__text').span.text == '0个':
        print('no search result')
        return

    else:
        try:
            threads = bs.findAll(class_ = 'result-com__title')
            
            for thread in threads:
                if keyword in thread.text:
                    list.append(thread.a['href'])
        except:
            raise
    
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
        url_time = soup.find(class_='re_from').span.text
    except:
        pass
    try:
        url_author = soup.find(class_='user_name')['title']
    except:
        pass
    try:
        url_title = soup.find(class_='h1').text.strip()
    except:
        pass
    try:
        url_content = soup.find(class_='re_content').text.strip()
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
    if not os.path.isdir(folder_path + '/crawl_result/mama.cn'):
        os.makedirs(folder_path + '/crawl_result/mama.cn')
    
    for row in df_keys.iterrows():
        data = []
        try:
            keyword = row[1][0]
            print('开始抓取关键词：' + keyword + ' ...')
            start_time = datetime.datetime.now()
            today = start_time.strftime('%Y-%m-%d')    
            pageUrl = getPageUrl(keyword)
            
            producer_thread = []
            if pageUrl:
                for page in pageUrl:
                    t = urlProducer(keyword, page)
                    producer_thread.append(t)
                    t.start()
                for t in producer_thread:
                    t.join()
        
                print('帖子链接抓取完成，用时：'+ getUsedTime(start_time))
                threads = []
                while not q.empty():
                    for i in range(WORKER_NUM):
                        thread = urlConsumer()
                        threads.append(thread)
                        thread.start()
                    for thread in threads:
                        thread.join()
            else:
                print('无搜索结果')
            result = pd.DataFrame(data, columns = ['time','title','author','content'])
            file_path = folder_path + "/crawl_result/mama.cn/" + keyword + '_' + today + '.xlsx'
            result.to_excel(file_path,encoding = 'utf-8',index = False)
            print( "关键词 " + keyword + ' 帖子抓取完成' 
            + '\n总用时：'+ getUsedTime(start_time) + '\n')
            
            time.sleep(2)
        except Exception as e:
            raise
    print('抓取结束')        