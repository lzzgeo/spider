#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys,os
import urllib2,urllib,httplib,socket
import re

import time,threading,thread
import string,StringIO
import Queue
import traceback
import gzip
import chardet
import json
import math


reload(sys)
sys.setdefaultencoding('utf-8')


httplib.HTTPConnection._http_vsn = 10 
httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'

"""
1. 弧度与角度转换
2. 球面坐标计算
3. 百度坐标加密、解密
4. 字符串距离计算
"""
class Utils:
    def __init__(self):
        self.minor_semi_axis    = 6356.755 * 1000.0 * math.pi * 2.0/360.0
        self.major_semi_axis    = 6378.113649 * 1000.0 * math.pi * 2.0/360.0
        self.EARTH_RADIUS_METER = 6378137.0 

        self.x_pi = 3.14159265358979324 * 3000.0 / 180.0;

    def deg2rad( self, d ): 
        return d*math.pi/180.0

    def rad2deg( self, r ): 
        return 180.0 * r/ math.pi

    def spherical_distance( self, lon1, lat1, lon2, lat2 ): 
        flon = self.deg2rad(lon1)
        flat = self.deg2rad(lat1)
        tlon = self.deg2rad(lon2) 
        tlat = self.deg2rad(lat2)
        con = math.sin(flat)*math.sin(tlat)
        con += math.cos(flat)*math.cos(tlat)*math.cos(flon - tlon) 

        return float(math.acos(con)*self.EARTH_RADIUS_METER)

    def calcGeoDelta( self, geodist, lat ):
        lon_delta = geodist/math.fabs(math.cos(self.deg2rad(lat))*self.minor_semi_axis)
        lat_delta = geodist/self.major_semi_axis
        
        return (lon_delta,lat_delta)
  
    def bd_encrypt(self, gg_lat, gg_lon):
        bd_lat = 0.0
        bd_lon = 0.0  
        x = gg_lon
        y = gg_lat 
        z = math.sqrt(x * x + y * y) + 0.00002 * math.sin(y * self.x_pi)
        theta = math.atan2(y, x) + 0.000003 * math.cos(x * self.x_pi)
        bd_lon = z * math.cos(theta) + 0.0065
        bd_lat = z * math.sin(theta) + 0.006

        return (bd_lon, bd_lat)
    
    def bd_decrypt(self, bd_lon, bd_lat):
        gg_lat = 0.0
        gg_lon = 0.0  
        x = bd_lon - 0.0065
        y = bd_lat - 0.006
        z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * self.x_pi)
        theta = math.atan2(y, x) - 0.000003 * math.cos(x * self.x_pi)
        gg_lon = z * math.cos(theta)
        gg_lat = z * math.sin(theta)

        return (gg_lon, gg_lat)

    def string_distance( self, n1, n2 ):
        n1 = n1.decode("utf-8")
        n2 = n2.decode("utf-8")
        n1 = self.standard_name( n1 )
        
        c1 = len(n1)
        c2 = len(n2)

        if c1==0 or c2==0:
            return float(0.0)


        dict_2 = {}
        for c in n2:
            dict_2[c] = 1

        score = 0
        for c in n1:
            if dict_2.has_key(c):
                score = score+1

        return float(float(score)/float(c1))

if __name__=='__main__':
    ut = Utils()
    print ut.bd_decrypt( float(sys.argv[1]), float(sys.argv[2]))

    sys.exit()
