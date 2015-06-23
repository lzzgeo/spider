#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys,os
import urllib2,urllib,httplib,socket
import re
import MySQLdb

import time,threading,thread
import string,StringIO
import Queue
import traceback
import gzip
import chardet

from spider_proxyip import ProxyIP_Mgr_Thread

reload(sys)
sys.setdefaultencoding('utf-8')

from logManager import *
from bs4 import *


httplib.HTTPConnection._http_vsn = 10 
httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'



class Downloader:
    def __init__(self, logMgr, proxy_mgr, verify_word):
        self.logMgr = logMgr
        self.verify_word = verify_word  #verify.baidu.com
        self.try_404 = -1 
        self.proxy_mgr = proxy_mgr
    def getUrlContent(self, url, keyword):
        proxy_ip = ''
        content = ''
        #surl = urllib.quote(url+keyword, ':?=/')
        surl = url+keyword
        err_code = ''
        try:
            response = None
            request = urllib2.Request(surl)
            request.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')
            request.add_header('X-Forwarded-For','x.x.x.x')
            request.add_header('Referer',surl)
            #request.add_header('Accept-encoding', 'gzip')

            if (self.proxy_mgr!=None):
                proxy_ip = self.proxy_mgr.getProxy()
            else:
                proxy_ip=''
            if (len(proxy_ip)>0):
                proxy_support = urllib2.ProxyHandler({'http':proxy_ip})
                opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler)
                response = opener.open(request)
                if ( self.proxy_mgr!=None ):
                    self.proxy_mgr.putProxy(proxy_ip)
            else:
                response = urllib2.urlopen(request)
        
            if response.info().get('Content-Encoding') == 'gzip':
                buf = StringIO.StringIO(response.read())
                f = gzip.GzipFile(fileobj=buf)
                content = f.read()
            else:
                content = response.read()
               
            if (len(self.verify_word)>0):
                while (content.find(verify_word)!=-1):
                    self.logMgr.write(proxy_ip + "  need to verify\n")
                    time.sleep(300)
                    return self.getUrlContent(url, keyword)

            detect_char=chardet.detect(content)
            #print detect_char
            c_set=detect_char['encoding']
            if (c_set=='GB2312'):
                content = content.decode('GB18030','ignore')
            elif c_set != 'utf-8' and c_set != 'UTF-8':
                #content = content.decode(c_set,'ignore')
                content = content.decode('GB18030','ignore')

        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                self.logMgr.write('urlerror  %d:\n %s\n proxyip is %s\n' % (e.code, url+keyword, proxy_ip))
                err_code = e.code
            else:
                self.logMgr.write('urlerror:\n %s\n proxyip is %s\n %s\n' % (url+keyword, proxy_ip, e.reason))
                err_code = 'urlerror'
        except:
            self.logMgr.write('except error:\n %s\n proxyip is %s\n %s\n' % (url+keyword, proxy_ip, traceback.format_exc()))
            err_code = 'other except'
        finally:
            if err_code=='':
                return (content, '')
            else:
                return self.getUrlContent(url, keyword)


    def getUrlContent2(self, url, keyword, num):
        if num<1:
            return ('', '')
        num = num - 1

        proxy_ip = ''
        content = ''
        surl = url+keyword
        err_code = ''
        try:
            response = None
            request = urllib2.Request(surl)
            request.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')
            request.add_header('X-Forwarded-For','x.x.x.x')
            request.add_header('Referer',surl)
            #request.add_header('Accept-encoding', 'gzip')

            if (self.proxy_mgr!=None):
                proxy_ip = self.proxy_mgr.getProxy()
            else:
                proxy_ip=''
            if (len(proxy_ip)>0):
                proxy_support = urllib2.ProxyHandler({'http':proxy_ip})
                opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler)
                response = opener.open(request)
                if ( self.proxy_mgr!=None ):
                    self.proxy_mgr.putProxy(proxy_ip)
            else:
                response = urllib2.urlopen(request)
        
            if response.info().get('Content-Encoding') == 'gzip':
                buf = StringIO.StringIO(response.read())
                f = gzip.GzipFile(fileobj=buf)
                content = f.read()
            else:
                content = response.read()
               
            if (len(self.verify_word)>0):
                while (content.find(verify_word)!=-1):
                    self.logMgr.write(proxy_ip + "  need to verify\n")
                    time.sleep(300)
                    return self.getUrlContent(url, keyword, num)

            detect_char=chardet.detect(content)
            #print detect_char
            c_set=detect_char['encoding']
            if (c_set=='GB2312'):
                content = content.decode('GB18030','ignore')
            elif c_set != 'utf-8' and c_set != 'UTF-8':
                #content = content.decode(c_set,'ignore')
                content = content.decode('GB18030','ignore')

        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                self.logMgr.write('urlerror  %d:\n %s\n proxyip is %s\n' % (e.code, url+keyword, proxy_ip))
                err_code = e.code
            else:
                self.logMgr.write('urlerror:\n %s\n proxyip is %s\n %s\n' % (url+keyword, proxy_ip, e.reason))
                err_code = 'urlerror'
        except:
            self.logMgr.write('except error:\n %s\n proxyip is %s\n %s\n' % (url+keyword, proxy_ip, traceback.format_exc()))
            err_code = 'other except'
        finally:
            if err_code=='':
                return (content, '')
            else:
                return self.getUrlContent2(url, keyword, num)

def Usage():
    print 'extract proxy ip:'
    print '--threadnum: '
    print '--host: '
    print '--dbname: '
    print '--user: '
    print '--pwd: '

if __name__ == '__main__':

    threadnum = 1
    host_ = ''
    port_ = ''
    dbname_ = ''
    user_ = ''
    pwd_ = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], ':', ['threadnum=', 'host=', 'port=', 'dbname=', 'user=', 'pwd='])
    except getopt.GetoptError, err:
        print str(err)
        Usage()
        sys.exit(2)
    for o, a in opts:
        if o in ('--threadnum='):
            threadnum = int(str(a))
        elif o in ('--host='):
            host_ = a
        elif o in ('--port='):
            port_ = a
        elif o in ('--dbname='):
            dbname_ = a
        elif o in ('--user='):
            user_ = a
        elif o in ('--pwd='):
            pwd_ = a
        else:
            print 'unhandled option'
            Usage()

	# test to get proxyip from pool
    logMgr = LogManager('/downloader_test')
    logMgr.out_screen = True
    p_thread = ProxyIP_Mgr_Thread(logMgr, host_, port_, dbname_, user_, pwd_)
    p_thread.start()
    time.sleep(5)

    dloader = Downloader(logMgr, p_thread, '')
    i = 0;
    while (True):
        time.sleep(20);
        content = dloader.getUrlContent('http://blog.csdn.net/', '')
        print i
        i += 1;

    p_thread.job_nums = 0

    sys.exit()
