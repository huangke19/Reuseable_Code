#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 author: 'huangke'
 date:    2019-04-26
 刷访问量的脚本

"""

import random

import requests

# PC端地址
URL = "http://www.nbd.com.cn/articles/2019-04-26/1325667.html"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    "Host": "www.nbd.com.cn",
}


class Crawler(object):
    count = 0
    filter_dic = set()

    def __init__(self, url, headers):
        self.url = url
        self.headers = headers

    def get_proxy_ip(self):
        response = requests.get(url="http://127.0.0.1:5010/get_all/")
        if response.status_code == 200 and response.json():
            return random.choice(response.json())
        else:
            print("没拿到IP")

    def fuck_nbd(self):
        proxy_ip = self.get_proxy_ip()
        if not proxy_ip:
            return 'ip fail'
        if proxy_ip in self.filter_dic:
            return 'duplicate'

        print(proxy_ip) 
        proxies = {"http": 'http://%s' % proxy_ip}

        try:
            response = requests.get(url=URL, headers=HEADERS, proxies=proxies, timeout=10)
        except requests.exceptions.ReadTimeout:
            return "time out fail"
        except requests.exceptions.ProxyError:
            return "proxy fail"
        except requests.exceptions.ConnectionError:
            return "connection fail"
        else:
            if response.status_code == 200:
                print("刷页面成功")
                self.count += 1
                self.filter_dic.add(proxy_ip)
                return "-------visti times %s " % self.count + "-" * 30 + "ip---%s" % proxy_ip
            else:
                print("fail")
                return "fail"

papaxia = Crawler(URL, HEADERS)

while True:
    with open('record.txt', 'a') as f:
        record = papaxia.fuck_nbd()
        print(record)
        f.write(record + "\n")
