# -*- coding: utf-8 -*-
"""
Created on Fri Jun 30 16:58:05 2017

@author: suewang
"""
import time
#import itchat
import random
import datetime
import requests
import smtplib
import itchat
from bs4 import BeautifulSoup
from email.mime.text import MIMEText


random.seed()
#获取场馆页面可选预订日期
def isOpen(date_string):
    try:
        time.strptime(date_string,'%Y-%m-%d')
    except:
        raise
    
    query_url = 'http://www.quntitong.cn/sport/stadium/query.do'
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0',
          'Referer': 'http://www.quntitong.cn/sport/stadium/selectStadium.do?stadiumResourceId=8a42f4874f8d5e8f014fabfba455118d'}
    
    datas = {}
    datas['stadiumResourceId'] = '8a42f4874f8d5e8f014fabfba455118d'
    datas['stadiumCode'] = '0020C062532'
    datas['site'] = '2'
    datas['period'] = '2'
    datas['sportCode'] = '002'
    datas['subscribeDate'] = date_string
    
    
    book_html = requests.post(query_url, data = datas,headers = header)
    bsObj = BeautifulSoup(book_html.text,'lxml')
    
    if bsObj.find('td'):
        return True
    
    else:
        return False


#判断日期是否为下周同一个周天
next_day = datetime.datetime.now() + datetime.timedelta(days = 7)
day = next_day.strftime('%Y-%m-%d')
canBook = isOpen(day)

while not canBook:
    timer = random.randint(30,50)
    time.sleep(timer)
    canBook = isOpen(day)

msg = "群体通网页已经更新！最新可定日期为： " + day + '\n更新时间: ' + datetime.datetime.now().strftime('%H:%M:%S')

# 发送邮件
message = MIMEText(msg)
message['Subject']='群体通更新至' + day
message['from']='suewang@live.hk'
message['to'] = 'suetsubasa1@yahoo.com'

mail_host = "smtp-mail.outlook.com:587"
mail_user = XXXX
mail_pw = XXXX


s = smtplib.SMTP(mail_host)
s.starttls()
s.login(mail_user,mail_pw)

s.send_message(message)
s.quit()
print('程序运行完毕')

# 发送微信
#itchat.auto_login(hotReload = True)
#receiver = itchat.search_friends('竹本')
#itchat.send(msg, toUserName = receiver[0]['UserName'])
