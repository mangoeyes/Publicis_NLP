# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 10:15:24 2017

@author: suewang
"""

import jieba
import os
import codecs
import re
import string
import csv
import sys
import seaborn as sns
import matplotlib as mpl
import numpy as np
import pandas as pd
from pandas import Series, DataFrame
from zhon.hanzi import punctuation
    
#%%
################################################################################
#判断文本是否为数字
################################################################################
def isNum(string):
    if not isinstance(string, str):
        raise TypeError('bad operand type')
    try:    
        float(string)
    except:
        isFloat = False
    else:
        isFloat = True
    return isFloat

#%%
################################################################################
#       对文本分词，去重，去停词及标点，返回以词为key,词频为value的dict
################################################################################
def getWordDict(text):
    if not isinstance(text, str):
        raise TypeError('Wrong input type')
    
    morePun = '\-~@+='
    pun = string.punctuation + punctuation + morePun
    
    stpwrdpath = "C:/Users/suewang/Desktop/Python/TM/stop_words.txt"
    with open(stpwrdpath,'r',encoding = 'ANSI') as swfile:
        content = swfile.read()
        sw_list = content.splitlines()
    
   
    word_list = {}
    str_list = text.splitlines()
    for line in str_list:
        line = line.strip()
        line = re.sub('Oral-B', 'OralB', line, flags=re.IGNORECASE)
        seg_list = jieba.cut(line,cut_all = False)
        for seg in seg_list:
            seg = seg.strip()
            if seg in word_list:
                word_list[seg] = word_list[seg] + 1
            elif not (seg.isspace() or isNum(seg) 
            or re.search('^['+pun+']+$',seg) or seg in sw_list):
                word_list[seg] = 1
    
    return word_list
                
            
#%%

################################################################################
#                       返回词频最高的词列表
################################################################################
def getTopKeyword(dictionary,num):
    if not (isinstance(dictionary, dict) and isinstance(num,int)):
        raise TypeError('bad operand type')
    elif num > len(dictionary):
        raise IndexError('required number exceeds dict length')
    
    dictionary = { k : v for k,v in dictionary.items() if len(k) > 1}
    rank_list = sorted(dictionary.items(),key = lambda x: x[1],reverse = True)
    rank_list = rank_list[:num]
    rt_list = [i[0] for i in rank_list]
    return rt_list

################################################################################
#               返回列表 判断每段文本是否含有关键词
#               以文本作者及发布时间作为primary key
################################################################################
def getOccurList(text_df, kw_list):
    if not (isinstance(text_df,pd.DataFrame) and isinstance(kw_list,list)):
        raise TypeError('wrong input type')
    
    all_list = []
    for row in text_df.iterrows():
        dict = {}
        dict['time'] = row[1]['time']
        dict['account'] = row[1]['author']
        
        for token in kw_list:
           if token in row[1]['content']:
               dict[token] = 1
           else:
               dict[token] = 0
        all_list.append(dict)
        
    column = ['account','time']
    column.extend(kw_list)
    df = pd.DataFrame(all_list, columns = column)
    return df


#%%
################################################################################
#               生成同时包含两个关键词的文本数量矩阵
################################################################################
def genMatrix(text,kw_list):
    if not (isinstance(text,list) and isinstance(kw_list,list)):
        raise TypeError('wrong input type')
    
    mtr = {}
    for token in kw_list:
        mtr[token] = {}
    for keys in mtr:
        for token in kw_list:
            mtr[keys][token] = 0

    for corpus in text:
        corpus = str(corpus)
        term_list = getWordDict(corpus)
        for token1 in kw_list:
            for token2 in kw_list:
                if (token1 == token2 and term_list.get(token1,0) > 1) or (token1 != 
                   token2 and term_list.get(token1,0)*term_list.get(token2,0) > 0):
                    mtr[token1][token2] += 1
            
    
    return mtr
 

#%%
###############################################################################
#                           主程序入口
###############################################################################

path = "C:/Users/suewang/Desktop/Python/TM/milk_powder/crawl_result/weibo"

file_list = os.listdir(path)
text_list = []

for file in file_list:
    filepath = path+'/'+file
    if os.path.isfile(filepath):
        with open(filepath,'r',encoding = 'utf-8') as ftr:
                df_raw = pd.read_excel(filepath, sheetname=0,header=0)
                comment = list(df_raw['content'])
                text_list.extend(comment)

#添加自备词表
jieba.load_userdict('C:/Users/suewang/Desktop/Python/TM/tooth/user_dict.txt')
raw = " ".join(map(str,text_list))
all_kw_dict = getWordDict(raw)

word_list = getTopKeyword(all_kw_dict,100)

mm = getOccurList(df_raw,word_list)
df1 = pd.DataFrame(mm)
df1.to_csv('C:/Users/suewang/Desktop/Python/TM/milk_powder/biao.csv',index = True, header = True)

#draw heatmap
#########################################################################
#mpl.rcParams['font.sans-serif'] = ['simhei']
#mpl.rcParams['axes.unicode_minus'] = False
#sns.set_style('whitegrid',{'font.sans-serif':['SimSun','Arial']})
#
#f, ax = mpl.subplots(figsize = (10, 10))
#cmap = sns.cubehelix_palette(dark = 0, light = 1, as_cmap = True)
#sns.heatmap(df1, cmap = cmap, linewidths = 0.05,annot = True)
#ax.set_title('Keyword Heatmap')
#
#f.savefig('sns_heatmap.jpg', bbox_inches='tight')
#########################################################################


    