
# coding=utf-8

"""  
Created on 2017-07-06 
@author: suewang
功能: 爬取搜狐微信的搜索结果
网址：http://weixin.sogou.com/
"""
import re
import time
import queue
import random
import datetime
import requests
import threading
from bs4 import BeautifulSoup
from selenium import webdriver        
from selenium.webdriver.common.keys import Keys        
import pandas as pd

# 线程锁 防止多线程同时读写数据
mutex = threading.RLock()
mutex2 = threading.Lock()
q = queue.Queue() #创建任务队列
WORKER_NUM = 4

# 继承Thread的worker类 负责爬取文章的信息
class contentWorker(threading.Thread):
    
    def __init__(self):
        super(contentWorker,self).__init__()
        
    def run(self):
        global data,q
        if mutex.acquire(1):
            if mutex2.acquire(1):
                if not q.empty():
                    url = q.get()
                    getPageContent(url)
                mutex2.release()
            mutex.release()
        
# 使用selenium搜索并获取微信文章链接
def GetSearchUrl(keyword):

    global q
    SEARCH_URL = "http://weixin.sogou.com/"
    driver.get(SEARCH_URL)

    print( '搜索：'+ keyword)

    #输入关键词并点击搜索
    # item_inp = driver.find_element_by_xpath("//input[@id='upquery']")
    # 2017-06-06 ID changed
    item_inp = driver.find_element_by_xpath("//input[@id='query']")
    item_inp.send_keys(keyword)
    item_inp.send_keys(Keys.RETURN)
    
    random.seed()
    TIMER = random.randint(5,10)
    start_time = datetime.datetime.now()
    
    #循环获取文章链接并翻页 直到最后一页
    while True:
        time.sleep(TIMER)
        hasResult = checkContent()
        hasNext = checkNext()
        if hasResult:
            article_nodes = driver.find_elements_by_xpath("//div[@class='txt-box']/h3/a")
            for node in article_nodes:

                try:
                    q.put(node.get_attribute("href"))
                except:
                    print("exception")
        #判断是否有下一页
        if hasNext:
            next_page_url = driver.find_element_by_xpath("//a[@id='sogou_next']").get_attribute("href")
            driver.get(next_page_url)
        else:
            use_time = (datetime.datetime.now() - start_time).total_seconds()
            m, s = divmod(use_time, 60)
            h, m = divmod(m, 60)
            print( "关键词 " + keyword + ' 路径抓取完成' 
            + '\n用时：'+ "%02d:%02d:%02d" % (h, m, s))
            break


#判断页面加载完成后是否有内容
def checkContent():
    try:
        # driver.find_element_by_xpath("//div[@class='no-sosuo']")
        # 2017-06-06 web page change
        driver.find_element_by_xpath("//div[@id='noresult_part1_container']")
        flag = False
    except:
        flag = True
    
    return flag

#判断是否有下一页按钮
def checkNext():
    try:
        driver.find_element_by_xpath("//a[@id='sogou_next']")
        flag = True
    except:
        flag = False
    #print("CHECKnext RESULT ==%s" %flag)

    return flag

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
        url_time = soup.find(id='post-date').text
    except:
        pass
    try:
        url_author = soup.find(id='post-user').text
    except:
        pass
    try:
        url_title = soup.find(id='activity-name').text.strip()
    except:
        pass
    try:
        url_content = soup.find(id='js_content').text.strip()
        url_content = re.sub("\\xa0", " ", url_content)
    except:
        pass
    
    result = {'time':url_time,'author':url_author,'title':url_title,
              'content':url_content}
    data.append(result)

#*******************************************************************************
#                                程序入口
#*******************************************************************************
if __name__ == '__main__':

    driver = webdriver.Firefox(executable_path = 
                               'C:/ProgramData/Anaconda3/selenium/webdriver/'+
                               'firefox/geckodriver.exe', log_path = None)
    
    folder_path = 'C:/Users/suewang/desktop/python/TM/milk_powder'
    df_keys = pd.read_excel(folder_path+'/search_keywords.xlsx', 
                            sheetname = 0,header = 0)
    j = 0
    for row in df_keys.iterrows():
        data = []
        try:
            keyword = row[1][0]
            threads = []
            start_time = datetime.datetime.now()
            today = start_time.strftime('%Y-%m-%d')
            GetSearchUrl(keyword)
            
            while not q.empty():
                for i in range(WORKER_NUM):
                    thread = contentWorker()
                    threads.append(thread)
                    thread.start()
                for thread in threads:
                    thread.join()
                    
            result = pd.DataFrame(data, columns = ['time','title',
                                                   'author','content'])
            file_path = (folder_path + "/crawl_result/wechat/" + keyword + '_' 
            + today + '.xlsx')
            result.to_excel(file_path,encoding = 'utf-8',index = False)
            use_time = (datetime.datetime.now() - start_time).total_seconds()
            m, s = divmod(use_time, 60)
            h, m = divmod(m, 60)
            print( "关键词 " + keyword + ' 文章抓取完成' 
            + '\n总用时：'+ "%02d:%02d:%02d\n" % (h, m, s))
            time.sleep(2)
        
        except Exception as e:
            print(e)
        
        finally:
            j = j+1
            if j > 7:
                print('休息中，开启新的浏览器...')
                driver.close()
                time.sleep(30)
                j = 0
                driver = webdriver.Firefox(executable_path = 
                               'C:/ProgramData/Anaconda3/selenium/webdriver/'+
                               'firefox/geckodriver.exe', log_path = None)
    
    print('抓取结束')
    driver.close()
        