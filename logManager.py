#!/usr/bin/python
# -*- coding: utf-8 -*-
# Filename: logManager.py

import sys,os
import urllib2,urllib,httplib,socket
import re
import MySQLdb

import time,threading,thread
import string
import Queue
import traceback

httplib.HTTPConnection._http_vsn = 10 
httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'

g_mutex_log = threading.Lock()

class LogManager:
    def __init__(self, base_name):

        self.logInfo =  u''
        self.base_name = base_name
        self.out_screen = False
        self.f_name = base_name + u'_0.log'
        self.f_index=0
        try:
            self.logFile = open( self.f_name, 'a')
        except:
            traceback.print_exc()
            sys.exit()
    
    def __del__(self):
        if (self.logInfo!=0):
            self.logFile.write(self.logInfo.encode('utf8'))
        self.logFile.close()
    
    def write(self, info):
        if self.out_screen:
            print info
        global g_mutex_log
        try:
            g_mutex_log.acquire()
            # when the physical file size >1 GB, create a new file to store log info
            if (os.path.getsize(self.f_name)>1024*1024*1024):
                self.logFile.close()
                f_index += 1
                self.f_name = u"%s_%d.log" (self.base_name,self.f_index)
                self.logFile = open(self.f_name, 'a')

            self.logInfo += (time.strftime(u'%Y-%m-%d %A %X %Z',time.localtime(time.time())) + '  ' + info)

            # when the log info in memory > 1KB, then store into physical disk
            if (len(self.logInfo)>1024):
                self.logFile.write(self.logInfo.encode('utf8'))
                self.logFile.flush()
                self.logInfo = ''
        except:
            print u'error: cannot write info to logfile'
            traceback.print_exc()
            return  
        finally:
            g_mutex_log.release()
    
