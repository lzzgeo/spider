#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import re
import sys,getopt
import traceback
import threading
import time
import MySQLdb
import Queue
from logManager import *

g_rawProxy = Queue.Queue()
g_checkedProxy = Queue.Queue() 


# 定时器，定时从proxy_ip中获取最新的proxy ip
class ProxyIP_Mgr_Thread(threading.Thread):
    def __init__(self, logMgr, ip, port, db, user, pwd):
        threading.Thread.__init__(self)
        
        self.proxy_pool = Queue.Queue()
        self.logMgr = logMgr

        self.job_nums = 1;
    
        #休眠5分钟后，查看是否任务都完成，则退出线程
        self.sleep_times = 60*1
        
        self.ip = ip
        self.port = port
        self.db = db
        self.user = user
        self.pwd = pwd
    def getProxy(self):
        print "@@@@@@@@@@@@@@", self.proxy_pool.qsize()
        if (self.proxy_pool.qsize()>0):
            return self.proxy_pool.get()
        else:
            return ''
    def putProxy(self, proxyip):
        return self.proxy_pool.put(proxyip)
    def run(self):
        while self.job_nums>0:
            try:
                if (self.proxy_pool.qsize()<10):
                    conn=MySQLdb.connect(host=self.ip,user=self.user,passwd=self.pwd,port=self.port)
                    cur=conn.cursor()
                    conn.select_db(self.db)
                    cur.execute('SELECT * FROM ProxyIP_Pool GROUP BY IP,Port')
                    results=cur.fetchall()
                    self.logMgr.write('get availabe proxy ip count: %d\n' % len(results))
                    for r in results:
                        proxy_ip = "%s:%d" % (r[0],r[1])
                        self.proxy_pool.put(proxy_ip)
    
                    conn.commit()
                    cur.close()

            except:
                self.logMgr.write(traceback.format_exc())

            finally:
                time.sleep(self.sleep_times)

        self.logMgr.write('exit proxyip manager thread\n')


class ProxyGet(threading.Thread):
    def __init__(self):

        threading.Thread.__init__(self)

        #对每个目标网站开启一个线程负责抓取代理
        self.main_page = 'http://www.proxy360.cn/'
        self.targets = ['http://www.proxy360.cn/Region/Brazil','http://www.proxy360.cn/Region/China','http://www.proxy360.cn/Region/America','http://www.proxy360.cn/Region/Taiwan',
          'http://www.proxy360.cn/Region/Japan','http://www.proxy360.cn/Region/Thailand','http://www.proxy360.cn/Region/Vietnam','http://www.proxy360.cn/Region/bahrein']

        #正则
        retext = '''<span class="tbBottomLine" style="width:140px;">[\r\n\s]*(.+?)[\r\n\s]+</span>[\r\n\s]*'''
        retext += '''<span class="tbBottomLine" style="width:50px;">[\r\n\s]*(.+?)[\r\n\s]*</span>[\r\n\s]*'''
        retext += '''<span class="tbBottomLine " style="width:70px;">[\r\n\s]*.+[\r\n\s]*</span>[\r\n\s]*'''
        retext += '''<span class="tbBottomLine " style="width:70px;">[\r\n\s]*(.+?)[\r\n\s]*</span>[\r\n\s]*'''
        self.p = re.compile(retext,re.M)

    def run(self):
        global g_rawProxy
        proxy_count = 0;
        try:
            for target in self.targets:
                print "目标网站： " + target
                req = urllib2.urlopen(target, timeout=50)
                #req = urllib2.urlopen("http://www.proxy360.cn/Region/Brazil", timeout=200)
                result = req.read()
                matchs = self.p.findall(result)
                for row in matchs:
                    ip = row[0]
                    port = row[1]
                    address = row[2].decode("utf-8").encode("gbk")
                    proxy = [ip,port,address]
                    g_rawProxy.put(proxy)
                    proxy_count += 1
        except:
            #print 'error: %s\n %s' % (self.main_page, traceback.format_exc())
            print 'error: %s\n %s' % (target, traceback.format_exc())
        finally:
            print 'info: %s  >>>>>>>   proxycount: %d' % (self.main_page, proxy_count)

# extract proxy ip from webpage
class ProxyGet2(threading.Thread):
    def __init__(self):

        threading.Thread.__init__(self)
        self.main_page = "http://www.youdaili.cn/Daili/"
        print self.main_page

        #正则
        retext = "<li><a href=\"http://www.youdaili.cn/Daili/http/(.*?)\.html\".*?【HTTP代理】.*?images/hot.gif"
        self.re1 = re.compile(retext,re.M)

        retext = "((?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)):(\d*)@HTTP#"
        self.re2 = re.compile(retext,re.M)

    def run(self):
        global g_rawProxy
        s_page = ''
        url = ''
        proxy_count = 0;
        try:
            url = self.main_page
            req = urllib2.urlopen(url)
            result = req.read()
            rs = self.re1.search(result)
            if rs==None:
                return

            s_page = rs.group(1)


            i = 1
            while True:
                if i == 1:
                    url = "http://www.youdaili.cn/Daili/http/%s.html" % s_page
                else:
                    url = "http://www.youdaili.cn/Daili/http/%s_%d.html" % (s_page,i)

                i = i+1

                req = urllib2.urlopen(url)
                result = req.read()
                matchs = self.re2.findall(result)
                for row in matchs:
                    ip = row[0]
                    port = row[1]
                    proxy = [ip,port,'']
                    g_rawProxy.put(proxy)
                    proxy_count += 1
        except:
            print 'error: %s\n %s' % (url, traceback.format_exc())
        finally:
            print 'info: %s  >>>>>>>   proxycount: %d' % (self.main_page, proxy_count)
#
class ProxyGet3(threading.Thread):
    def __init__(self):

        threading.Thread.__init__(self)
        self.main_page = "http://www.ip-adress.com/proxy_list/"
        print self.main_page

        retext = "<td>((?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)):(\d*)</td>"
        self.re = re.compile(retext,re.M)

    def run(self):
        global g_rawProxy
        proxy_count = 0;
        try:
            headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20120101 Firefox23.0'}
            req = urllib2.Request(url = self.main_page,headers = headers)

            result = urllib2.urlopen(req).read()
            matchs = self.re.findall(result)
            for row in matchs:
                ip = row[0]
                port = row[1]
                proxy = [ip,port,'']
                g_rawProxy.put(proxy)
                proxy_count += 1
                #print '%s : %s' % (proxy[0], proxy[1])
        except:
            print 'error: %s\n %s' % (self.main_page, traceback.format_exc())
        finally:
            print 'info: %s  >>>>>>>   proxycount: %d' % (self.main_page, proxy_count)


class ProxyGet4(threading.Thread):
    def __init__(self):

        threading.Thread.__init__(self)
        self.main_page = "http://www.xici.net.co/"
        self.targets = ['http://www.xici.net.co/nn/','http://www.xici.net.co/nt/','http://www.xici.net.co/wn/','http://www.xici.net.co/wt/']

        print self.main_page
        retext = "<td>((?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d))</td>$\n^.*?<td>(\d*)</td>"
        self.re = re.compile(retext,re.M)

    def run(self):
        global g_rawProxy
        proxy_count = 0

        for target in self.targets:
            page_index = 1
            while page_index < 15:
                s_url = "%s%s" % (target, page_index)
                page_index = page_index + 1
                print s_url

                try:
                    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20120101 Firefox23.0'}
                    req = urllib2.Request(url = s_url, headers = headers)
                    result = urllib2.urlopen(req, timeout=30).read()

                    matchs = self.re.findall(result)
                    for row in matchs:
                        proxy = [row[0], row[1], '']
                        g_rawProxy.put(proxy)
                        proxy_count += 1
                        #print '%s : %s' % (proxy[0], proxy[1])
                except:
                    print 'error: %s\n %s' % (self.main_page, traceback.format_exc())

        print 'info: %s  >>>>>>>   proxycount: %d' % (self.main_page, proxy_count)


class ProxyGet5(threading.Thread):
    def __init__(self):

        threading.Thread.__init__(self)
        self.main_page = "http://www.veryhuo.com/res/ip/"
        print self.main_page

        #正则
        retext = "<td>((?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)).*?:\"(.*?)\)"
        self.re2 = re.compile(retext,re.M)

    def run(self):
        global g_rawProxy
        s_page = 'page'
        proxy_count = 0;
        try:
            i = 1
            while True:
                url = "http://www.veryhuo.com/res/ip/%s_%d.php" % (s_page,i)
                i = i+1

                req = urllib2.urlopen(url)
                result = req.read()
                matchs = self.re2.findall(result)
                for row in matchs:
                    ip = row[0]
                    port = row[1]
                    port = port.replace('+','')
                    port = port.replace('v','3')
                    port = port.replace('m','4')
                    port = port.replace('a','2')
                    port = port.replace('l','9')
                    port = port.replace('q','0')
                    port = port.replace('b','5')
                    port = port.replace('i','7')
                    port = port.replace('w','6')
                    port = port.replace('r','8')
                    port = port.replace('c','1')
                    proxy = [ip,port,'']
                    g_rawProxy.put(proxy)
                    proxy_count += 1
        except:
            print 'error: %s\n %s' % (url, traceback.format_exc())
        finally:
            print 'info: %s  >>>>>>>   proxycount: %d' % (self.main_page, proxy_count)


class ProxyGet6(threading.Thread):
    def __init__(self):

        threading.Thread.__init__(self)
        self.main_page = "http://www.ip-daili.com/xw/?id=3"
        print self.main_page

        #正则
        retext = '<a href=\"(http://www.ip-daili.com/view/.*?)\".*?跳墙代理.*?>'.decode("utf-8").encode("gbk")
        self.re1 = re.compile(retext,re.M)

        retext = "((?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)):(\d*)@.*?<br"
        self.re2 = re.compile(retext,re.M)

    def run(self):
        global g_rawProxy
        url = ''
        proxy_count = 0;

        try:
            req = urllib2.urlopen(self.main_page, timeout=30)
            rs = self.re1.search( req.read() )
            if rs==None:
                return
            url = rs.group(1)
        except:
            print traceback.format_exc()
            return

        try:
            req = urllib2.urlopen(url, timeout=30)
            matchs = self.re2.findall(req.read())
            for row in matchs:
                ip = row[0]
                port = row[1]
                proxy = [ip,port,'']
                g_rawProxy.put(proxy)
                proxy_count += 1
                print ip, port
        except:
            print 'error: %s\n %s' % (url, traceback.format_exc())
        finally:
            print 'info: %s  >>>>>>>   proxycount: %d' % (self.main_page, proxy_count)

# http://pachong.org/

# check wheather the proxy ip still be available
class ProxyCheck(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.timeout = 15
        self.testUrl = "http://www.sogou.com/"

    def run(self):
        cookies = urllib2.HTTPCookieProcessor()
        while True:
            if ( g_rawProxy.qsize()<=0):
                break;
            try:
                proxy = g_rawProxy.get(False)
            except:
                break;
            try:
                proxyHandler = urllib2.ProxyHandler({"http" : r'http://%s:%s' %(proxy[0],proxy[1])})
                opener = urllib2.build_opener(cookies,proxyHandler)
                opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1')]

                t1 = time.time()
                req = opener.open(self.testUrl, timeout=self.timeout)
                result = req.read()
                if ( len(result)>100):
                    timeused = time.time() - t1
                    print "%s:%s is ok----- %d ms" % (proxy[0], proxy[1], timeused)
                    g_checkedProxy.put((proxy[0],proxy[1],timeused))
                else:
                    print 'open error'
                    continue
            except urllib2.URLError, e:
                if hasattr(e, 'code'):
                    print "url error: \n ProxyIP: %s:%s \n error code -->%d" % (proxy[0],proxy[1],e.code)
            except:
                print "ProxyIP: %s:%s " % (proxy[0],proxy[1])
                traceback.print_exc()
                continue

def Usage():
    print 'extract proxy ip:'
    print '--threadnum: '
    print '--host: '
    print '--dbname: '
    print '--user: '
    print '--pwd: '

if __name__ == "__main__":
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


    getThreads = []
    checkThreads = []

    t = ProxyGet()
    getThreads.append(t)

    t = ProxyGet4()
    getThreads.append(t)

    """
     not available for now :(
    t = ProxyGet2()
    getThreads.append(t)

    t = ProxyGet3()
     getThreads.append(t)

    t = ProxyGet5()
    getThreads.append(t)
    """
    
    t = ProxyGet6()
    getThreads.append(t)

    for i in range(len(getThreads)):
        getThreads[i].start()
    for i in range(len(getThreads)):
        getThreads[i].join()
    
    time.sleep(5)
    
  
    ss = set()
    temp_queue = Queue.Queue()
    while g_rawProxy.qsize()>0:
        proxy = g_rawProxy.get()
        ip = proxy[0]
        port = proxy[1]
        ip_port = ip + ':' + port
        if ip_port not in ss:
            ss.add(ip_port)
            temp_queue.put([ip,port,''])
    g_rawProxy = temp_queue

    str = time.strftime('%Y-%m-%d %A %X %Z',time.localtime(time.time())) 
    print "====%s   extract %d proxy ip" % (str, g_rawProxy.qsize())

    #sys.exit()

    # check proxy by using mutithread
    t_count = threadnum;
    for i in range(t_count):
        t = ProxyCheck()
        checkThreads.append(t)

    for i in range(len(checkThreads)):
        checkThreads[i].start()
    for i in range(len(checkThreads)):
        checkThreads[i].join()


    str = time.strftime('%Y-%m-%d %A %X %Z',time.localtime(time.time())) 
    print "====%s   %d are available" % (str, g_checkedProxy.qsize())
    time.sleep(5)

    

    # put proxy which have been check into database
    try:
        conn=MySQLdb.connect(host=host_,user=user_,passwd=pwd_,port=int(port_))
        cur=conn.cursor()
        conn.select_db(dbname_)
        cur.execute("INSERT INTO ProxyIP_Archive(IP, Port, Archive_Time) SELECT IP, Port, CONCAT(CURRENT_DATE, '  ', CURRENT_TIME) FROM ProxyIP_Pool")
    except MySQLdb.Error,e:
        print 'error: cannot backup the proxyip'
        traceback.print_exc()
    
    try:
        cur.execute('DROP TABLE IF EXISTS ProxyIP_Pool')
    except:
        traceback.print_exc()
    try:
        cur.execute('CREATE TABLE ProxyIP_Pool(IP VARCHAR(16), Port INT)')

        values=[]
        while (g_checkedProxy.qsize()>0):
            proxy = g_checkedProxy.get()
            values.append((proxy[0],proxy[1]))
        cur.executemany('INSERT INTO ProxyIP_Pool VALUES(%s,%s)',values)

        conn.commit()
        cur.close()
        conn.close()
    except MySQLdb.Error,e:
        traceback.print_exc()

