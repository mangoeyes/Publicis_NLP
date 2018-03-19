
# coding=utf-8

"""  
Created on 2016-10-15 
@author: royrao
功能: 爬取新浪微博的搜索结果
网址：http://s.weibo.com/
实现：采取selenium测试工具，模拟微博登录，结合PhantomJS/Firefox，
分析DOM节点后，采用Xpath对节点信息进行获取，实现重要信息的抓取
"""
import re            
import os
import time
import datetime
from selenium import webdriver        
from selenium.webdriver.common.keys import Keys        
import pandas as pd

#先调用无界面浏览器PhantomJS或Firefox    
#driver = webdriver.PhantomJS()


#********************************************************************************
#                            第一步: 登陆login.sina.com
#                     这是一种很好的登陆方式，有可能有输入验证码
#                          登陆之后即可以登陆方式打开网页
#********************************************************************************

def LoginWeibo(username, password):
    try:
        #输入用户名/密码登录
        print('准备登陆Weibo.cn网站...')
        driver.get("http://login.sina.com.cn/")
        elem_user = driver.find_element_by_name("username")
        elem_user.clear()
        elem_user.send_keys(username) #用户名
        elem_pwd = driver.find_element_by_name("password")
        elem_pwd.clear()
        elem_pwd.send_keys(password)  #密码
        # elem_sub = driver.find_element_by_xpath("//input[@class='smb_btn']")
        # 2017-06-06 element class changed 
        elem_sub = driver.find_element_by_xpath("//input[@class='W_btn_a btn_34px']")        
        elem_sub.click()              #点击登陆 因无name属性

        try:
            #输入验证码
            time.sleep(5)
            elem_sub.click() 
        except:
            #不用输入验证码
            pass

        #获取Coockie 推荐资料：http://www.cnblogs.com/fnng/p/3269450.html
        print( 'Crawl in ' + driver.current_url)
        print('输出Cookie键值对信息:')
#        2017-06-29 stop printing cookie 
#        for cookie in driver.get_cookies():             
#            print(cookie)
#            for key in cookie:
#                print( key )
#                print( cookie[key] ) 
        print('登陆成功...')
    except Exception:      
        print( "Error: ")
    finally:    
        print('登入结束\n')


#********************************************************************************
#                  第二步: 访问http://s.weibo.com/页面搜索结果
#               输入关键词, 得到 搜索人的 ID, 粉丝数
#********************************************************************************    
# PYTHON 2 / 3 对字符 ENCODE 不同
# PYTHON 3 默认已是 UNICODE 编码

def GetSearchContent(key,pages):

    driver.get("http://s.weibo.com/")
   
    #输入关键词并点击搜索
    time.sleep(2)
    try:
        item_inp = driver.find_element_by_xpath("//input[@class='searchInp_form']")
        item_inp.send_keys(key)
        item_inp.send_keys(Keys.RETURN)#采用点击回车直接搜索
        
    except:
        print(" exception NO INPUT FORM " )
    time.sleep(10)#等待网页跳转
    
    start = datetime.datetime.now()
    content = []
    
    if checkContent():
        try:
            for i in range(pages): 
                page = getContent()
                content.extend(page)
                hasNext = checkNext()
                
                if hasNext:
                    time.sleep(2)
                    goToNextPage()
                else:
                    print("无下一页。总抓取页数: " + str(i+1))
                    usetime = (datetime.datetime.now() - start).total_seconds()
                    m, s = divmod(usetime, 60)
                    h, m = divmod(m, 60)
                    print('完成关键词 '+ key + ' 的抓取, 用时：' + "%02d:%02d:%02d" % (h, m, s))
                    break
                
        except Exception as e:
            print("exception in getSearchContent =="  + key + '\n')
            print(e)
            
    return content        
    
#********************************************************************************
#                  辅助函数，考虑页面加载完成后得到页面所需要的内容
#********************************************************************************   

#判断页面加载完成后是否有内容
def checkContent():
    #有内容的前提是有“导航条”？错！只有一页内容的也没有导航条
    #但没有内容的前提是有“pl_noresult”
    try:
        driver.find_element_by_xpath("//div[@class='pl_noresult']")
        flag = False
    except:
        flag = True
    return flag

#爬取并获得一页搜索微博博文
def getContent():
    result = []
    
    if checkContent():
        try:
            acc_nodes = driver.find_elements_by_xpath('//div[@id = "pl_weibo_direct"]//dl[@class = "feed_lists W_texta"]//div[@class = "feed_content wbcon"]/a[@class="W_texta W_fb"]')
            
            wb_nodes = driver.find_elements_by_xpath('//div[@id = "pl_weibo_direct"]//dl[@class = "feed_lists W_texta"]//div[@class = "feed_content wbcon"]/p[@class="comment_txt"]')
            time_nodes = driver.find_elements_by_xpath('//div[@id = "pl_weibo_direct"]//dl[@class = "feed_lists W_texta"]//a[@class="W_textb"]')
            fw_nodes = driver.find_elements_by_xpath('//div[@id = "pl_weibo_direct"]//div[@class = "feed_action clearfix"]')
            
            for (n1,n2,n3,n4) in zip(acc_nodes, wb_nodes, time_nodes, fw_nodes):
                dict = {}
                dict['content'] = n2.text
                dict['author'] = n1.text
                dict['time'] = n3.get_attribute('title')
                
                info = n4.text
                try:
                    dict['forward'] = re.search("转发[0-9]*\n",info).group().replace("转发","").strip()
                except:
                    dict['forward'] = ''
                try:
                    dict['comment'] = re.search("评论[0-9]*\n",info).group().replace("评论","").strip()
                except:
                    dict['comment'] = ''
                try:
                    dict['like'] = re.search("\n[0-9]*$",info).group().strip()
                except:
                    dict['like'] = ''
                    
                result.append(dict)
              
        except Exception as e:
            print(e)
    return result

def goToNextPage():
    if checkContent():
        try:
            node = driver.find_element_by_xpath('//a[@class = "page next S_txt1 S_line1"]')
            nextPage = node.get_attribute('href')
            driver.get(nextPage)
        except Exception as e:
            raise
            
#判断是否有下一页按钮
def checkNext():
    try:
        driver.find_element_by_xpath('//a[@class = "page next S_txt1 S_line1"]')
        flag = True
    except:
        flag = False

    return flag

#*******************************************************************************
#                                程序入口
#*******************************************************************************
if __name__ == '__main__':
    

    #定义变量
    username = XXXX             #输入你的用户名
    password = XXXX              #输入你的密码
    driver = webdriver.Firefox(executable_path = 'C:/ProgramData/Anaconda3/' + 
                               'selenium/webdriver/firefox/geckodriver.exe', 
                               log_path = None)
    
    #操作函数
    LoginWeibo(username, password)       #登陆微博
    
    #搜索微博
    
    #读取关键词，新建文件夹
    folder_path = 'C:/Users/suewang/desktop/python/TM/milk_powder'
    df_keys = pd.read_excel(folder_path+'/search_keywords.xlsx', sheetname=0,header = 0)
    if not os.path.exists(folder_path+"/crawl_result/weibo"):
        os.makedirs(folder_path+'/crawl_result/weibo')
    
    #将搜索结果输出为xlsx文件
    for row in df_keys.iterrows():
        try:
            keyword = row[1][0]
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            result = GetSearchContent(keyword,50)
            df = pd.DataFrame(result,columns = ['author','content','time','forward','comment','like'])
            file_path = folder_path + "/crawl_result/weibo/" + keyword + '_' + today + '.xlsx'
            df.to_excel(file_path,encoding = 'utf-8',index = False)
            time.sleep(3)
        except Exception as e:
            print(e)
    print('抓取结束')
    driver.close()
    
    
    
    
    
    
    
    
    
    
    
