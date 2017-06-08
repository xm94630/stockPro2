#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#上面的注释是用来支持中文，没有就会出错


from __future__ import division


#这个需要先 pip install requests
import requests
import json
import math
import time


#头信息
cookie = 'aliyungf_tc=AQAAAPmR3X3Y0QwAopuP2+mfwa3X68B9; xq_a_token=876f2519b10cea9dc131b87db2e5318e5d4ea64f; xq_a_token.sig=dfyKV8R29cG1dbHpcWXqSX6_5BE; xq_r_token=709abdc1ccb40ac956166989385ffd603ad6ab6f; xq_r_token.sig=dBkYRMW0CNWbgJ3X2wIkqMbKy1M; u=571496720504862; s=f811dxbvsv; Hm_lvt_1db88642e346389874251b5a1eded6e3=1495547353,1496562578,1496717217,1496718108; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1496806200; __utma=1.1590213924.1496727484.1496757368.1496806200.6; __utmc=1; __utmz=1.1496727484.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)';
userAgent  = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36';


#配置
config = [
    'category=SH',
    'exchange=',
    'areacode=',
    'indcode=',
    'orderby=symbol',
    'order=desc',
    'current=ALL',
    'pct=ALL',
    'pb=0_2',           #PB
    'pettm=0_20',       #PE/TTM
    'pelyr=0_20',       #PE/LYR
    '_=1496806580260',
];
config2  = [
    'period=1day',
    'type=before',
    '_=1496850179732',
];


#需要抓取的数据源
baseUrl     = 'https://xueqiu.com/stock';
screenerAPI = baseUrl+'/screener/screen.json';
stockAPI    = baseUrl+'/forchartk/stocklist.json';


#所有的数据列表
stockArr = [];


#股票类
class Stock:
    def __init__(self, name=0, symbol=1):
        self.name = name
        self.symbol = symbol


#解析json
class Payload(object):
    def __init__(self, j):
        self.__dict__ = json.loads(j)


#获取第N页数据
def getScreenerData(url,config,page):
    _headers = {
        "User-Agent":userAgent,
        "Cookie":cookie
    }
    _params = "&".join(config);
    _params = _params + '&page=' + str(page);
    res = requests.get(url=url,params=_params,headers=_headers)
    return res.text;


#递归获取全部数据
def getAllData(page=0):
    json = getScreenerData(screenerAPI,config,page);
    data = Payload(json);
    arr  = data.list;

    # 股票总条数
    count = data.count;
    totalPages = int(math.ceil(count/30)) 
    if page == 0:
        page = 1;
    else:
        page = page+1;
        #获取一页的数据
        for one in arr:
            name = one['name']; 
            symbol = one['symbol']; 
            stockArr.append(Stock(name,symbol));
       
    if page<=totalPages:
        getAllData(page);


#某个股 N年内 每天价格集合
def getStockDetail(url,config,symbol,nYear):

    _year     = nYear;
    _interval = int(_year * 31536000 * 1000);
    _end      = int(time.time() * 1000);  #坑 一定要转成整数，否者后来都会是float类型
    _begin    = _end - _interval;

    _headers = {
        "User-Agent":userAgent,
        "Cookie":cookie
    }
    _params = "&".join(config);
    
    _params = _params+'&symbol='+symbol;
    _params = _params+'&end='+ str(_end);
    _params = _params+'&begin='+ str(_begin);

    #print(_params)

    res = requests.get(url=url,params=_params,headers=_headers)
    return res.text;


#某个股 第N年内 最低点
def getLowPrice(symbol,nth):
    lows = []
    stockInfo = getStockDetail(stockAPI,config2,symbol,nth);
    arr = Payload(stockInfo).chartlist;

    for one in arr:
        low = one['low'];  
        lows.append(low);

    m = sorted(lows)[:1];

    #这里返回最低点、和总数据条数
    #总数据条数 会用来判断，这个股票是否不足六年（比如第4年和第3年数据一样多，说明其实不存在第四年的数据！）
    return [m[0],len(arr)];  


#调整数据
#比如有数据为：[[18.91, 241], [18.91, 486], [11.11, 732], [10.51, 732], [9.68, 732], [9.68, 732]]
#从第4年开始数据长度就没有发生改变了，就说明不存在第四年的数据，后面的年份就更加不存在了，要调整数据为：
#调整目标数据为：[[18.91, 241], [18.91, 486], [11.11, 732], [0, 732], [0, 732], [0, 732]]
#进一步提取为：[18.91, 18.91, 11.11, 0, 0, 0]
def modData(arr):

    #arr = [[18.91, 241], [18.91, 486], [11.11, 732], [10.51, 732], [9.68, 732], [9.68, 732]];
    newArr = [];
    length = len(arr);
    for i in range(0,length-1):
        if arr[i][1]==arr[i+1][1]:
            #不存在的年份用-999填空，为何不是0呢？因为0不好区分，这中情况可是正常存在的，包括出现 -4 这样子也是合理的（因为前赋权）
            arr[i+1][0] = -999;  

    for i in range(0,length):
        newArr.append(arr[i][0]);
    return newArr;


#获取 N年内 每一年的低点，以数组返回
def getLowPriceArr(symbol,nYear):
    total = nYear;
    arr   = [];
    while nYear>0:
        low = getLowPrice(symbol,total+1-nYear);
        nYear = nYear-1;
        arr.append(low)

    arr = modData(arr);
    return arr;




arr = getLowPriceArr('SZ000550',6);
print(arr)
#getAllData();

#获取数据的总长度
#print(len(stockArr))




















