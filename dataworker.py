# !/usr/bin/env python
'''This is the wxPython for stock quant
stock_quant.py
add model to 'updateData'
add threading.event to 'stop' button
'''

import sys
import os
import gc
import wx
from wx.lib.pubsub import pub
from datetime import datetime, timedelta
from time import ctime, sleep
import threading
from random import randint
from queue import Queue
import logging
#from socket import *
#from twisted.internet import reactor
import time
from time import ctime
import sqlite3

import pandas as pd
from pandas import Series, DataFrame
import numpy as np

#to draw K-line
import mpl_finance as mpf
from matplotlib.pylab import date2num
import matplotlib.pyplot as plt
import matplotlib  

import psutil

   
# matplotlib采用WXAgg为后台,将matplotlib嵌入wxPython中  
#matplotlib.use("WXAgg")  
#from matplotlib.backends.backend_wxagg 
#import FigureCanvasWxAgg as FigureCanvas  
#from matplotlib.figure import Figure  
#from matplotlib.backends.backend_wx 
#import NavigationToolbar2Wx as NavigationToolbar  

#from twisted.internet import protocol, reactor, task
#from twisted.internet import defer
#import requests
#from twisted.web.client import Agent
#from twisted.web.http_headers import Headers
#from twisted.protocols.basic import LineReceiver
#from twisted.internet import reactor
#from twisted.internet.protocol import Factory, Protocol
#from twisted.python import log
#log.startLogging(sys.stdout)

#import struct
#import json

import tushare as ts
api = ts.pro_api('9f81ed0d75c3c8d15a81ae3be09a2e81f9637b464ba510aea6f64c16')
pro = ts.pro_api('9f81ed0d75c3c8d15a81ae3be09a2e81f9637b464ba510aea6f64c16')
from sqlite3 import dbapi2 as sqlite
from sqlalchemy import create_engine
from sqlalchemy.dialects.sqlite import TIME, DATE, DATETIME
from sqlalchemy import create_engine, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy import MetaData, Sequence
from sqlalchemy.orm import sessionmaker, relationship


import wx
import os
import wx.grid
#import hqdata
from datetime import datetime,timedelta
import threading
from wx.lib.pubsub import pub
import wx.adv
from wx.lib.splitter import MultiSplitterWindow


from viewer import logger
class Sqlite3Handler(object):
    def __init__(self, autypeStr='qfq'):
        self.sql_filename_base = 'hqData.db'
        self.sql_filename = self.sql_filename_base
        self.autypeStr = autypeStr
        self.set_DBname_and_autype(self.autypeStr)
        self.hq_codes = self.get_codes()
        self.tablenm_hqall='hqall_t'
        self.date_tail = '00:00:00.000000'
        
        

    def set_DBname_and_autype(self, autypeStr):
        if (autypeStr == 'nfq'):
            self.autype=None
            self.autypeStr='nfq'
        elif (autypeStr == 'hfq'):
            self.autype='hfq'
            self.autypeStr='hfq'
        elif (autypeStr == 'qfq'):
            self.autype='qfq'
            self.autypeStr='qfq'
        self.sql_filename = autypeStr+'_'+self.sql_filename_base
        self.engine = create_engine('sqlite+pysqlite:///%s'%self.sql_filename, module=sqlite)
        self.initDB()
        logger.debug("change to %s database and engine",self.sql_filename)
#        self.engine.dispose()
    
    def updateEngine(self):
        self.engine = create_engine('sqlite+pysqlite:///%s'%self.sql_filename, module=sqlite)
        logger.debug("create engine to %s database",self.sql_filename)
        
    def get_codes(self,table_nm=None):
        codes = []
        if (table_nm==None):
            #table_nm = datetime.now().strftime("%Y%m%d")
            table_nm = "stock_basic_t"
        sqlcmd_get_codes = "SELECT ts_code FROM '%s'"%table_nm
        try: 
            r = self.engine.execute(sqlcmd_get_codes)
        except Exception as e:
            logger.debug(e)
            self.initDB()
            #self.saveCodes_fromCSV_toDB()
            r = self.engine.execute(sqlcmd_get_codes)
        #for i in r.fetchall():
        codes = map((lambda x:x[0]),r)
#        for i in r:
#            codes.append(list(i)[0])
        print(codes)
        return list(codes)
    def initDB(self):
        """Generate 'codes_t', which has all stock codes, into sqlite_db if there is no 'codes_t' in sqlite_db"""
        # 1. check if 'codes_t' exists
        cmd = "select count(*)  from sqlite_master where type='table' and name = '%s'"%'stock_basic_t'
        if ((self.engine.execute(cmd).fetchall()[0][0])==0):
            # 2. 'codes_t' not exists, check if 'codes_table.csv' exists. Try to generate 'codes_t' from 'codes_table.csv'
            # 2.1 check if 'codes_table.csv' exists, generate one if not using get_today_all()
            if (not os.path.isfile('stock_basic.csv')):
                #generate 'codes_table.csv' using get_today_all()
                self.generate_codes_csv('stock_basic.csv', 5)
            # 2.2 check if 'codes_table.csv' exists, generate 'codes_t' in DB if exists, raise an error if not.
            if (os.path.isfile('stock_basic.csv')):
                # generate 'codes_t' from 'codes_table.csv'
                names = ['ts_code','symbol','name','area','industry','fullname','enname','market','exchange','curr_type','list_status','list_date','delist_date','is_hs']
                codes_df = pd.read_csv('stock_basic.csv', dtype='str',names=names)
                try:
                    codes_df.to_sql('stock_basic_t', self.engine, index=False)
                except ValueError as e:
                    logger.info(e)
                except Exception as e:
                    logger.info(e)
            else: 
                # raise an error, 'codes_table.csv' fails, try again
                logger.error('fail to generate codes_table.csv, try again')
                assert (1==0)
    

class CalcRPS_Model(Sqlite3Handler):
    
    def __init__(self):

        self.rpsStartDate = datetime.now().strftime("%Y%m%d")
        #self.rpsStartDate = '20181022'
        self.rpsEndDate = datetime.now().strftime("%Y%m%d")
        self.rpsNChoices=['50','120', '250']
#        self.rpsMktChoices = [u'全部', u'深市', u'沪市', u'创业板' ]
#        self.rpsRangeChoices = [u'全部', u'一年以上']
        self.rpsN = '20'
        self.rpsMktValue = u'深市'
        self.rpsRangeValue = u'一年以上'
        self.rpsLow = '95'
        self.rpsHigh = '100'
        self.rpsDayCount='120'
        self.rpsNList=[]
        
        self.onoff=1
        self.rpsCbxPctRankStatus = False
        self.pctRank_startdate = datetime.now().strftime("%Y%m%d")
        self.rps_enddate = datetime.now().strftime("%Y%m%d")
        #self.autype='qfq'
        super(CalcRPS_Model, self).__init__("hfq")
        self.maxDateInDBStr = self.readMaxDateInAttr_t()
        logger.debug("maxDateInDBStr is %s", self.maxDateInDBStr)

    def readMaxDateInAttr_t(self):
        cmd = "SELECT maxdate FROM %s "%('attr_t')
        return self.engine.execute(cmd).fetchone()[0]
    def getMaxDateInDB(self):
        cmd = "SELECT MAX(%s) FROM %s WHERE ts_code='%s'"%("trade_date", self.tablenm_hqall, "000001.SZ")
        try:
            dateStr = self.engine.execute(cmd).fetchone()[0].split(" ")[0]
            logger.info("maxinum date in database is %s", dateStr)
        except Exception as e:
            logger.error("Error to read max Date in getRPSbyDate!\n, %s",e)
            return None
        return dateStr
        
    def getClippedMaxDate(self, dateStr):
        """Return the clipped (smaller) Max Date between(date in database, dateStr)
        """
        maxDateInDB = datetime.strptime(self.maxDateInDBStr, "%Y%m%d")
        if (maxDateInDB<datetime.strptime(dateStr, "%Y%m%d")):
            return self.maxDateInDBStr
        else:
            return dateStr

    def createColumnIfnotExist(self):
        self.rpsN='20'  #for debug only
        colnames = []
        rpsColnm="rps%s"%self.rpsN
        pctColnm = "pct%s"%self.rpsN
        #colnames.append([rpsColnm, 'Integer'])
        colnames.append([pctColnm,'float'])
        for col, col_type in colnames:
            cmd="ALTER TABLE %s ADD %s %s"%(self.tablenm_hqall, col, col_type)
            logger.debug("%s", cmd)
            try:
                self.engine.execute(cmd)
                logger.debug("creat new column: %s %s", col , col_type)
            except Exception as e:
                logger.debug("%s (%s) already exists", col , col_type)
                print(e)
    
    def saveSelectedCodesToFavorite(self, selectedCodes):
        filename = "favorite.csv"
        mytime = datetime.now().strftime("%Y%m%d")
        try:
            with open (filename, 'a+') as fw:
                fw.write(mytime+':')
                for i in selectedCodes:
                    fw.write(i+',')
                fw.write('\n')
            rlt=True
        except Exception as e:
            logger.error(e)
            rlt = False
        pub.sendMessage("pubMsg_CalcRPS_Model", msg=("end_saveSelectedCodesToFavorite", rlt))
    
    def getRPSbyCode(self, tscode):
        print("run getRPSbyCode: %s"%tscode)
        pct_nm = 'pct%s'%self.rpsN
        rps_nm = 'rps%s'%self.rpsN
        rpsN = int(self.rpsN)
#        self.rpsStartDate='2018-10-22'
#        self.targe_date = self.rpsStartDate+' '+self.date_tail
        params = (tscode,)
        cmd="SELECT * FROM %s WHERE ts_code = ? "%self.tablenm_hqall
        try:
            df=pd.read_sql_query(cmd, self.engine, params= params)
            
        except Exception as e:
            logger.error("read rps data by ts_code from %s error", self.tablenm_hqall)
            logger.error(e)
            pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")
            return
        if (len(df)!=0):
            df_sorted = df.sort_values(by='trade_date', ascending=True)
            #只截取self.rpsDayCount天
            df_sorted=df_sorted.iloc[-int(self.rpsDayCount):,:]
            # Start, sorted and add idx to DF to draw k-line without blank day
            df_sorted.index = range(0, len(df_sorted))
            df_sorted['date_idx'] = np.arange(len(df_sorted))
            # end
            logger.debug('read rps data by ts_code from base to dataframe success! len = %d', len(df))
            self.rpsNList = list(set(self.rpsNList))
            self.rpsNList.append(rps_nm)
            pub.sendMessage("pubMsg_CalcRPS_Model", msg=("end_getRPSbyCode", (df_sorted, self.rpsNList)))
            # Cannot be deleted. In case: N50 is checked. N is changed from 20 to 50.
            self.rpsNList.remove(rps_nm)
        else:
            logger.debug('Error, database read rps error, len = %d', len(df))
            pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_getRPSbyDate")
#        pub.sendMessage("pubMsg_CalcRPS_Model", msg=("end_getRPSbyCode", df_sorted[['date',rps_nm,'code']]))
        
#        pub.sendMessage("pubMsg_CalcRPS_Model", msg=("end_getRPSbyCode", df))
        #pub.sendMessage("pubMsg_RPSRightUpPanel", msg=df_pct)
        
    
    def sortExistedRPSdata(self, para):
        df=para[0]
        colname = para[1]
        direction = para[2]
        df = df.sort_values(by=colname, ascending=direction)
        pub.sendMessage("pubMsg_CalcRPS_Model", msg=("end_getRPSbyDate", df))


    
    def getRPSbyDate(self):
        pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", 10))
        rpsLow = int(self.rpsLow)
        rpsHigh = int(self.rpsHigh)
        if (rpsHigh>=rpsLow):
    #        self.rpsStartDate='20181022'
            if (self.rpsCbxPctRankStatus == True):
                # 阶段涨幅, 需要load数据重新计算rps
                pct_nm = '_pct'
                rps_nm = '_rps'
                # for RPS Percentage Rank with 2 days
                startdate_fullStr = self.rpsStartDate
                enddate_fullStr = self.rpsEndDate
                params = (startdate_fullStr,enddate_fullStr)
                #cmd="SELECT * FROM %s WHERE trade_date = '%s' or trade_date = '%s'"%(self.tablenm_hqall, startdate_fullStr, enddate_fullStr)
                cmd="SELECT * FROM %s WHERE trade_date = ? or trade_date = ? "%self.tablenm_hqall
            else:
                # 常规RPS50, 120, 250
                # for rps50, rps120, rps250
                pct_nm = 'pct%s'%self.rpsN
                rps_nm = 'rps%s'%self.rpsN
                rpsN = int(self.rpsN)
                #self.targe_date = self.getClippedMaxDate(self.rpsStartDate)
                self.targe_date = self.getClippedMaxDate(self.rpsStartDate)
                #cmd1="SELECT * FROM %s WHERE trade_date = '%s'"%(self.tablenm_hqall, self.targe_date)
                params = (self.targe_date,)
                cmd  = "SELECT * FROM %s WHERE trade_date = ? "%self.tablenm_hqall
            try:
                df=pd.read_sql_query(cmd, self.engine, params=params)
                pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", 30))
            except Exception as e:
                logger.error("failed to read data from splite3 database, table :%s ", self.tablenm_hqall)
                logger.error(e)
                pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")
                return
            if (len(df)!=0 and (rps_nm in df.columns or self.rpsCbxPctRankStatus == True)):
                logger.debug('read data from sqlite3 database to dataframe success! len = %d', len(df))    
                if (self.rpsCbxPctRankStatus == True):
                # Caculation _rps for requested (day1, day2)
                    if (startdate_fullStr in df.trade_date.values and enddate_fullStr in df.trade_date.values):
                        df.groupby('ts_code').apply(lambda x: x.sort_values(by='trade_date', ascending=False))
                        df[pct_nm]= (df.groupby('ts_code')['weighted_close'].apply(lambda x: x.pct_change(-1))).round(4)
                        df[rps_nm] = (df.groupby('trade_date')[pct_nm].apply(lambda x: x.rank(pct=True))*100).round(1)
                        df = df[df['trade_date']==self.rpsStartDate]
                        pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", 60))
                    else:
                        # no data for requested dates. Invalid dates!
                        logger.debug("No data found for requested trade_date (%s, %s)", self.rpsStartDate, self.rpsEndDate)
                        pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")
                        return
                # Pick rps between (rpsLow, rpsHigh)    
                df_pct_A = df[df[rps_nm]>rpsLow]
                df_pct = df_pct_A[df_pct_A[rps_nm]<rpsHigh]
                df_pct = df_pct.sort_values(by=pct_nm, ascending=False)
                pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", 100))
                #send out result
                pub.sendMessage("pubMsg_CalcRPS_Model", msg=("end_getRPSbyDate", df_pct))
            else:
                logger.debug('Error, database read rps error, len = %d', len(df))
                #exception, terminate, and set panel on by sending msg="end_calcAllRPS"
                pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")
                return 
        else:
            #rpsHigh<rpsLow
            pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")
        
    
    
#    def caculateOneCodeRPS(self, code="603999"):
#        logger.debug("run caculateOneCodeRPS()")
#        #self.createColumnIfnotExist()
#        para_getData = (self.tablenm_hqall, code)
#        cmd="SELECT * FROM %s WHERE code='%s'"%para_getData
#        print(cmd)
##        df=pd.read_sql_query(cmd, self.engine, params=para_getData)
#        df=pd.read_sql_query(cmd, self.engine)
#        #print(df)
#        diff_nm = 'diff%s'%self.rpsN
#        pct_nm = 'pct%s'%self.rpsN
#        rps_nm = 'rps%s'%self.rpsN
#        #print(diff_nm, pct_nm, rps_nm)
#        df[diff_nm]=df['close'].diff(-int(self.rpsN))
#        df[pct_nm]=(df[diff_nm]/(df['close']+df[diff_nm])).round(4)
#        df[rps_nm]=df[pct_nm].rank(method="first")
#        # rate, code, date
#        c = df.apply(lambda x:(x[pct_nm],x['code'],x['date']), axis=1)
#        #c = df.apply(lambda x:(x[pct_nm],x[rps_nm],x['code'],x['date']), axis=1)
        
#        para=tuple(c)
#        #print(para)
#        cmd = "UPDATE hqall_t SET %s = ? WHERE code = ? AND date = ?"%(pct_nm)
#        #cmd = "UPDATE hqall_t SET %s = ? %s = ?WHERE code = ? AND date = ?"%(pct_nm, rps_nm)
#        a = self.engine.execute(cmd, para)
#        logger.debug("end of %s",__class__)
          
#    def calcAllRPS_old(self):
#        i=0
#        preStopMarker=200
#        memInfo = psutil.virtual_memory()
#        startMemUsage = psutil.Process(os.getpid()).memory_info().rss
#        start = time.time()
#        self.createColumnIfnotExist()
#        for code in self.hq_codes:
            
#            if (self.onoff==1):
#                if (i>=preStopMarker):
#                    try:
#                        self.caculateOneCodeRPS(code)
#                    except Exception as e:
#                        logger.debug(e)
#            else:
#                break
#            i+=1
#            if (i>=preStopMarker):
#                #gc.collect()
#                logger.info("memory usage: %s", format(psutil.Process(os.getpid()).memory_info().rss,','))
#                logger.info("total: %s, usage: %f%%, cpu: %d", format(memInfo.total,','), memInfo.percent, psutil.cpu_count())
#                logger.debug("i=%d",i)
##            if (i>=10):
##                break
#        logger.debug("time: %.2fs, i = %d",(time.time()-start), i)
#        endMemUsage = psutil.Process(os.getpid()).memory_info().rss
#        logger.info("memory usage: start=%sKB, end=%sKB, diff = %sKB", format(startMemUsage/1000,',.0f'),\
#                             format(endMemUsage/1000,',.0f'), format((endMemUsage-startMemUsage)/1000,',.0f'))
#        pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")
        
    def calcAllRPS(self):
        '''Read out all data from sql database, transfer, and generate 'pctN' and 'rpsN' two columns.
        Then write back to database
        '''
        counter = 10
        pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", counter))
        memInfo = psutil.virtual_memory()
        startMemUsage = psutil.Process(os.getpid()).memory_info().rss
        start = time.time()
        #self.rpsN = '20'        #TODO: this is only for debug, should be removed in formal useage
        logger.debug("calculation RPS start!")
        logger.debug("database =%s", self.sql_filename)

        #self.createColumnIfnotExist()
        if self.rpsN not in self.rpsNChoices:
            self.rpsNChoices.append(self.rpsN)
        pct_nm = 'pct%s'%self.rpsN
        rps_nm = 'rps%s'%self.rpsN
        rpsN = int(self.rpsN)
        cmd="SELECT * FROM %s"%self.tablenm_hqall
        logger.debug("sql cmd: %s", cmd)
        try:
            df=pd.read_sql_query(cmd, self.engine)
            counter += 10
            pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", counter))
        except Exception as e:
            logger.debug('line 260')
            logger.error("read data from %s error", self.tablenm_hqall)
            logger.error(e)
            pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")
            return
        #df[pct_nm] = df.groupby('code')['weighted_close'].pct_change(20)   #not working, a bug for groupy pct_change. use below apply
        if (len(df)==0):
            logger.debug('Error, database read error, len = %d', len(df))
            pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")
        else:    
            logger.debug('read data from base to dataframe success! len = %d', len(df))
            try:
                df = df.groupby('ts_code').apply(lambda x: x.sort_values(by='trade_date', ascending=False))
                for rpsNstr in self.rpsNChoices:
                    rps_nm = 'rps%s'%rpsNstr
                    pct_nm = 'pct%s'%rpsNstr
                    rpsN = int(rpsNstr)
                    logger.debug("caculating %s", rps_nm)
#                    if rps_nm in list(df.columns):
#                        logger.debug("%s existed in database, continue", rps_nm)
#                        continue
                    df[pct_nm]= (df.groupby('ts_code')['weighted_close'].apply(lambda x: x.pct_change(-rpsN))).round(4)
                    df[rps_nm] = (df.groupby('trade_date')[pct_nm].apply(lambda x: x.rank(pct=True))*100).round(1)
                    counter += 15
                    pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", counter))
                logger.debug('caculation is done! Start saving...')
            except Exception as e:
                logger.error("dataframe caculation is wrong!")
                logger.error(e)
                pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")
                return
#            print(df)
            try:
                pd.io.sql.to_sql(df, self.tablenm_hqall, self.engine, if_exists='replace',index=False, chunksize= 10000)
                counter = 100
                pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", counter))
            except Exception as e:
                logger.error(e)
                
            logger.debug("Caculation for %s is finished!! Time used: %.2fs",rps_nm,(time.time()-start))
            
            endMemUsage = psutil.Process(os.getpid()).memory_info().rss
            logger.info("memory usage: start=%sKB, end=%sKB, diff = %sKB", format(startMemUsage/1000,',.0f'),\
                                 format(endMemUsage/1000,',.0f'), format((endMemUsage-startMemUsage)/1000,',.0f'))
            gc.collect()
            #close engine
           # self.engine.dispose()   
#            conn.commit()
#            conn.close()
            pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")

class DnldHQDataModel(Sqlite3Handler):
    def __init__(self):
        
        self.start_date='2018086'
        #self.end_date = '20180813'
        if (datetime.now().hour>16):
            self.end_date = datetime.now().strftime("%Y%m%d")
        else:
            self.end_date = (datetime.now()-timedelta(days=1)).strftime("%Y%m%d")
        self.current_date = datetime.now().strftime("%Y%m%d")
        self.days_num=''
        self.HQonoff=0      #default off
#        self.engine = create_engine('sqlite+pysqlite:///%s'%self.sql_filename, module=sqlite)
        #self.engine = create_engine('sqlite+pysqlite:///nfq_hqData.db', module=sqlite)
#        self.engine = create_engine('sqlite+pysqlite:///file.db', module=sqlite)
        name = __class__
        super(DnldHQDataModel, self).__init__('hfq')

        #self.maxDateInDBStr = self.getMaxDateInDB()

    def getMaxDateInDB(self):
        cmd = "SELECT MAX(%s) FROM %s WHERE ts_code='%s'"%("trade_date", self.tablenm_hqall, "000001.SZ")
        try:
            dateStr = self.engine.execute(cmd).fetchone()[0].split(" ")[0]
            logger.info("maxinum date in database is %s", dateStr)
        except Exception as e:
            logger.error("Error to read max Date in getRPSbyDate!\n, %s",e)
            return None
        return dateStr
    
    def readMaxDateInAttr_t(self):
        cmd = "SELECT maxdate FROM %s "%('attr_t')
        return self.engine.execute(cmd).fetchone()[0]
        
    def updateMaxDateInDB(self, dateStr):
#        dateStr = '20181101'
        cmd = "UPDATE attr_t SET maxdate = '%s' "%dateStr
        self.engine.execute(cmd)
        
    def buildAttrTableIfNotExist(self):
        
        cmd = "select count(*)  from sqlite_master where type='table' and name = '%s'"%'attr_t'
        counter = list(self.engine.execute(cmd).fetchone())[0]
        if counter==0:
            
            try:
                maxDateStr = self.getMaxDateInDB()
            except Exception as e:
                logger.error(e)
                maxDateStr="19700101"
            logger.debug("creat attr_t and init maxdate= %s", maxDateStr)
            df = pd.DataFrame([maxDateStr], columns=['maxdate'],index=['info'])
            df.to_sql('attr_t',self.engine, if_exists="replace", index=True)
    def checkDateTableExist(self,date=None):
        if (date==None):
            date = datetime.now().strftime("%Y%m%d")
        query = "select count(*)  from sqlite_master where type='table' and name = '%s'"%date
        logger.debug("query = %s", query)
        counter = list(self.engine.execute(query).fetchone())[0]
        logger.debug("counter of %s is %d", date, counter)
        if counter>0:
            return True
        elif counter==0:
            return False
        
        for i in counter:
            print(i)

    def filter_date(self, startDateStr, endDateStr):
        """Return the list of modified date as [startdate as next workday, enddate as previous workday]
        """
        startDate = datetime.strptime(startDateStr, "%Y%m%d")
        endDate = datetime.strptime(endDateStr, "%Y%m%d")
        startDays = startDate.isoweekday()
        if (startDays in [6,7]):
            newStartStr = (startDate+timedelta(days=(8-startDays))).strftime("%Y%m%d")
        else:
            newStartStr=startDateStr
        # endDays        
        endDays = endDate.isoweekday()
        if (endDays in [6,7]):
            newEndStr = (endDate+timedelta(days=(5-endDays))).strftime("%Y%m%d")
        else:
            newEndStr=endDateStr
        logger.debug("filtered date: [%s, %s]",newStartStr, newEndStr)
        return [newStartStr, newEndStr]

#    def updateHQdata(self):
##        pub.sendMessage("update", msg="disableMenu")
#        pub.sendMessage("pubMsg_DnldHQDataModel", msg="disableMenu")
#        #TODO: verify validation of start_date, end_date
#        i=0
#        target_span=self.filter_date(self.start_date, self.end_date)
#        for code in self.hq_codes:
#            i+=1
#  #          pub.sendMessage("update", msg=i)
#            pub.sendMessage("pubMsg_DnldHQDataModel", msg=i)
#            #logger.debug("gauge=%d",i)
#            dateSpans=self.get_dateSpans(code, target_span)
#            try:
#                logger.debug("get %s hq data, start", code)
#                print(dateSpans)
#                for span in dateSpans:
#                    if (self.HQonoff==1):
#                        #TODO: use threading.event()?
#                        if (self.autype == 'qfq'):
#                            df = ts.get_h_data(code, start=span[0], end=span[1], retry_count=3, pause=5)
#                        else:
#                            df = ts.get_h_data(code, start=span[0], end=span[1], autype=self.autype, retry_count=3, pause=5)
##                        time.sleep(2)
#                        #add a columen code
#                        df['code']=code
#                        print(df)
#                        #df.to_sql("_%s"%code,self.engine, if_exists='append',index=True)
#                        df.to_sql("%s"%self.tablenm_hqall,self.engine, if_exists='append',index=True)
#                        logger.debug("write %s to DB",code)
#                    else:
#                        #(self.HQonoff==0):        #stop
##                        pub.sendMessage("update", msg="endHQupdate")        #clear gauage counter
#                        pub.sendMessage("pubMsg_DnldHQDataModel", msg="endHQupdate")        #clear gauage counter
#                        logger.info("updateHQdata() is stopped by Stop Button pressed, setting HQonoff 0")
#                        return
#                #delete duplicate line
#                cmd_del = "delete from _%s where rowid not in(select max(rowid) from _%s group by date)"%(code,code)
#                #self.engine.execute(cmd_del)
#                #TODO: need to check, enable or disable below
#            except OSError as e:
#                #network issue
#                logger.info(e)
#                time.sleep(60)
#            except Exception as e:
#                logger.info(e)
            
#            if (i>=G_NUM_OF_CODES):
##            if (i>=3):
#                logger.info("updateHQdata() is finished, i=%d",i)
#                break
# #       pub.sendMessage("update", msg="endHQupdate")            
#        pub.sendMessage("pubMsg_DnldHQDataModel", msg="endHQupdate")

    def updateHQdataByDate(self):
        start = time.time()
        memInfo = psutil.virtual_memory()
        startMemUsage = psutil.Process(os.getpid()).memory_info().rss
        pro = ts.pro_api('9f81ed0d75c3c8d15a81ae3be09a2e81f9637b464ba510aea6f64c16')
        pub.sendMessage("pubMsg_DnldHQDataModel", msg="disableMenu")
        logger.debug("download data start now ......")
        #TODO: verify validation of start_date, end_date
        gaugeCounter = 0
        try:
            ts_dates=list(self.getDateStrListToDnld(self.start_date, self.end_date))
        except Exception as e:
            logger.debug("generate ts_dates failure, %s",e)
        #logger.debug('ts_dates = %s ', list(ts_dates))
        if (len(ts_dates)==0):
            gaugeStep = 100
        else:
            gaugeStep = 100/(4*len(ts_dates))
        #print(ts_dates)
        
        #build attr_t table if not exist
        self.buildAttrTableIfNotExist()
        maxDateStr = self.readMaxDateInAttr_t()
        logger.debug("maxDateStr = %s", maxDateStr)
        for ts_date in ts_dates:
            gaugeCounter += gaugeStep
            #print(ts_date)
            pub.sendMessage("pubMsg_DnldHQDataModel", msg=round(gaugeCounter))
            #logger.debug("gaugeCounter = %d", gauageCounter)
            try:
                #logger.debug("get %s hq data, start...")
                if (self.HQonoff==1):
                    #TODO: use threading.event()?
                    if (self.autype == '1234qfq'):
                        df = pro.daily(trade_date=ts_date)
                    else:
                        #df = pro.daily(trade_date=ts_date)
                        #某天换手率
                        df1 = pro.daily_basic(ts_code='', trade_date=ts_date)
                        #某天日线数据
                        gaugeCounter += gaugeStep
                        df2 = pro.daily(trade_date=ts_date)
                        #某天复权因子
                        gaugeCounter += gaugeStep
                        df3 = pro.adj_factor(ts_code='', trade_date=ts_date)
                        gaugeCounter += gaugeStep
                        #df1.to_csv("df1.csv",index=false)
                        #df2.to_csv("df2.csv",index=false)
                        #df3.to_csv("df3.csv",index=false)
                        # Drop duplicated 'close'
                        df1.drop(['close'],axis=1, inplace=True)
                        df4 = pd.merge(df2,df1,on=['ts_code','trade_date'])
                        df = pd.merge(df4,df3,on=['ts_code','trade_date'])
                        # calc backward weighted close
                        df['weighted_close']=(df['close']*df['adj_factor']).round(2)
                        
                        ## caculate weighted high, open, low
                        #df['w_open'] = (df['weighted_close']*(1+(df['open']-df['close'])/df['close'])).round(2)
                        #df['w_high'] = (df['weighted_close']*(1+(df['high']-df['close'])/df['close'])).round(2)
                        #df['w_low'] = (df['weighted_close']*(1+(df['low']-df['close'])/df['close'])).round(2)

                    df.to_sql("%s"%self.tablenm_hqall,self.engine, if_exists='append',index=False)
                    logger.debug("write %s to database",ts_date)
                else:
                    #(self.HQonoff==0):        #stop
                    pub.sendMessage("pubMsg_DnldHQDataModel", msg="endHQupdate")        #clear gauage counter
                    logger.info("updateHQdata() is stopped by Stop Button pressed, setting HQonoff 0")
                    return
                #delete duplicate line
                #cmd_del = "delete from _%s where rowid not in(select max(rowid) from _%s group by date)"%(code,code)
                #self.engine.execute(cmd_del)
                #TODO: need to check, enable or disable below
            except OSError as e:
                #network issue
                logger.info(e)
                time.sleep(60)
            except Exception as e:
                logger.info(e)
        logger.debug("Time used: %.2fs. Download %d days data",(time.time()-start), len(ts_dates))
        endMemUsage = psutil.Process(os.getpid()).memory_info().rss
        logger.info("memory usage: start=%sKB, end=%sKB, diff = %sKB", format(startMemUsage/1000,',.0f'),\
                                 format(endMemUsage/1000,',.0f'), format((endMemUsage-startMemUsage)/1000,',.0f'))
        gc.collect()      
        pub.sendMessage("pubMsg_DnldHQDataModel", msg="endHQupdate")
            
    def read_from_DB(self):
        tablenm = self.tablenm_hqall
        date = "2018-10-18"
        #date_tail='00:00:00.000000'
        #tablenm = "hqall_t"
        # read DataFrame by code
        rd_cmd = "SELECT * FROM %s where code = %s"%(tablenm, code)
        df = pd.read_sql(rd_cmd, self.engine)
        
        # read DataFrame by 'TimeStr'
        rd_cmd = "SELECT * FROM %s where date = '%s %s'"%(tablenm, date, self.date_tail)
        df = pd.read_sql(rd_cmd, self.engine)
        
        print(df)
    
#    def get_dateSpans(self, code=None, target_span=None):
#        dateSpans=[]
#        if (target_span==None):
#            start_date_menu = self.start_date
#            end_date_menu = self.end_date
#        else:
#            start_date_menu = target_span[0]
#            end_date_menu = target_span[1]
#        logger.debug("start_date_menu = %s, end_date_menu=%s",start_date_menu, end_date_menu)
#        try:
#            # get sqlite3 time in str
##            cmd1 = "SELECT MIN(date) FROM _%s"%code                                                                    #1 code in 1 table
#            cmd1 = "SELECT MIN(date) FROM %s where code = %s"%(self.tablenm_hqall, code)            #all codes in 1 table
#            start_date_db= self.engine.execute(cmd1).fetchall()[0][0][:10]
#            #days-1
#            start_date_db = (datetime.strptime(start_date_db, "%Y%m%d")+timedelta(days=-1)).strftime("%Y%m%d")
            
##            cmd2 = "SELECT MAX(date) FROM _%s"%code
#            cmd2 = "SELECT MAX(date) FROM %s where code = %s"%(self.tablenm_hqall, code)            #all codes in 1 table
#            end_date_db= self.engine.execute(cmd2).fetchall()[0][0][:10]
#            end_date_db = (datetime.strptime(end_date_db, "%Y%m%d")+timedelta(days=1)).strftime("%Y%m%d")
#            #end_date_db = datetime.strptime(b, "%Y%m%d")
#            logger.debug("start_date_db = %s, end_date_db=%s",start_date_db, end_date_db)
            
#            if (end_date_menu<=start_date_db):
#                #status 1:
#                logger.debug("status 1")
#                dateSpans.append([start_date_menu,end_date_menu])
#            elif (start_date_menu>=end_date_db):
#                # status 2, same as 1
#                logger.debug("status 2")
#                dateSpans.append([start_date_menu, end_date_menu])
#            elif (start_date_menu<start_date_db)&(end_date_menu>start_date_db)&(end_date_menu<end_date_db):
#                #status 5
#                logger.debug("status 5")
#                dateSpans.append([start_date_menu,start_date_db] )
#            elif (start_date_db<=start_date_menu)&(start_date_menu<=end_date_db)&(end_date_db<=end_date_menu):
#                #status 6
#                logger.debug("status 6")
#                dateSpans.append([end_date_db, end_date_menu])
#            elif (start_date_db<=start_date_menu)&(end_date_menu<=end_date_db):
#                #status 8
#                logger.debug("status 8")
#                pass
#            elif (start_date_menu<=start_date_db)&(end_date_db<=end_date_menu):
#                #status 9
#                logger.debug("status 9")
#                dateSpans.append([start_date_menu, start_date_db])
#                dateSpans.append([end_date_db, end_date_menu])
#        except Exception as e:
#            #7. No data in dB
#            logger.debug("status 9")
#            dateSpans.append([start_date_menu, end_date_menu])
        
#        # remove the day of week end
#        filtered_dateSpans=[]
#        for dateSpan in dateSpans:
#            filteredSpan = self.filter_date(dateSpan[0], dateSpan[1])
#            if filteredSpan[0]<=filteredSpan[1]:
#                filtered_dateSpans.append(filteredSpan)
        
#        return filtered_dateSpans
            
    def getDateStrListToDnld(self, sDateStr, eDateStr):
        dateStrLists=[]
        dnldStartDate = datetime.strptime(sDateStr.replace('-',''), "%Y%m%d")
        dnldEndDate = datetime.strptime(eDateStr.replace('-',''), "%Y%m%d")
#        dnldStartDate = '2018-08-05'
#        dnldEndDate = '2018-08-15'
        logger.debug("dnldStartDate = %s, dnldEndDate = %s", dnldStartDate, dnldEndDate)
        # get business day in list of dates index
        datesIndex = pd.bdate_range(dnldStartDate,dnldEndDate)
        #length = len(datesIndex)
        # format to string from date, in iteration type
        datesIter = map(lambda x: x.strftime("%Y%m%d"),datesIndex)
        try:
            # get sqlite3 time in str
            cmd = "SELECT trade_date FROM %s where ts_code = '000001.SZ'"%(self.tablenm_hqall)            #all codes in 1 table
            #cmd = "SELECT trade_date FROM hqall_t where ts_code = '000001.SZ'"
            df=pd.read_sql_query(cmd, self.engine)
        except Exception as e:
            #7. No data in dB
            logger.debug("getDateStrListToDnld read database error: %s",e)
            # blank database
            df=pd.DataFrame(columns=['trade_date'])
        # get existed dates, in string list.
        storedDateStrList = list(df.trade_date.values)
        #logger.debug('storedDateStrList = %s ', storedDateStrList)
        # remove the dates that existed in database, in iteration
        datesStrIter = filter(lambda x: x not in storedDateStrList, datesIter)
        #logger.debug('filtered dateStr list is %s', list(datesStrIter))
        return datesStrIter
    
    
    def getTodayAllData(self):
        date = datetime.now().strftime("%Y%m%d")
        filename = date+'.csv'
        repeat_counter = 0
        #if not os.path.exists(filename):
        if (not self.checkDateTableExist(date)):
            while True:
                try:
                    repeat_counter +=1
                    hqTodayDataAll = ts.get_today_all()
#                    hqTodayDataAll = ts.get_k_data('000673', '2018-10-08', '2018-10-17')
                    hqTodayDataAll.to_csv(filename)
                    self.writeSqlite(hqTodayDataAll, date)
                    break
                except ValueError as e:
                    logger.info("Exception: %s",e)
                    break
                except Exception as e:
                    logger.info("Exception: %s",e)
                    if (repeat_counter >=5):
                        break   # fail to get data for 5 tries, raise an exception
                    else:
                        continue
        else:
            logger.debug("%s data already exists in %s", date, 'hsData.db')
        logger.debug("repeat_counter is %d", repeat_counter)
        pass
        
    def writeSqlite(self, df, table_nm=None):
        if (table_nm==None):
            table_nm = datetime.now().strftime("%Y%m%d")
        df.to_sql(table_nm, self.engine)
        logger.info("success: write hq date at %s",table_nm)
        
#    def get_codes(self,table_nm=None):
#        codes = []
#        if (table_nm==None):
#            #table_nm = datetime.now().strftime("%Y%m%d")
#            table_nm = "codes_t"
#        sqlcmd_get_codes = "SELECT code FROM '%s'"%table_nm
#        try: 
#            r = self.engine.execute(sqlcmd_get_codes)
#        except Exception as e:
#            logger.debug(e)
#            self.initDB()
#            #self.saveCodes_fromCSV_toDB()
#            r = self.engine.execute(sqlcmd_get_codes)
#        #for i in r.fetchall():
#        codes = map((lambda x:x[0]),r)
##        for i in r:
##            codes.append(list(i)[0])
#        #print(codes)
#        return list(codes)
    def isWeekDay(self, str_time):
        date = datetime.strptime(str_time, "%Y%m%d")
        return date.isoweekday()
    def generate_codes_csv(self, filename = 'codes_table.csv', maxcounter=5):
        assert(isinstance(filename, str))
        assert(isinstance(maxcounter, int))
        repeat_counter = 0
        ret = False
        while True:
            try:
                repeat_counter +=1
                hqDataAll = ts.get_today_all()
                # success
                logger.debug("get_today_all success!")
                df=hqDataAll['code']
                hqDataAll['code'].to_csv('codes_table.csv')
                ret = True
                break
            except ValueError as e: 
                logger.info(e)
                break
            except Exception as e:
                logger.debug(e)
                if (repeat_counter >=maxcounter):
                    break   # fail to get data for 5 tries, raise an exception
                else:
                    continue
        return ret

class CVRatioModel(Sqlite3Handler):
    """Cumulated Volume Ratio Choosing Stock"""
    def __init__(self):
        self.cvrStartDate = "20181010"
        self.cvrEndDate = "20181110"
        super(CVRatioModel, self).__init__('hfq')
        self.cvrDays = 5
        self.preCond = self.getInitPreCondData()
        self.cond = self.getInitCondData()
        self.cvrThreshold=80
        self.cvrEndCond=self.getInitEndCondData()
        self.cvrEndDayRange = 100
        self.cvrEndDays=5
        self.runCvrAllowed = True
        
        
    def getInitPreCondData(self):
        return {'Cbx':True, "MAdir":u'高于', "MAdays":'30', "DiffDir":u'至少', "DiffValue":'10'}
    def getInitCondData(self):
        return {'1': {'Cbx':True, "MAdir":u'高于', "MAdays":'5', "DiffDir":u'至少', "DiffValue":'10'},
                    '2': {'Cbx':True, "MAdir":u'高于', "MAdays":'8', "DiffDir":u'至少', "DiffValue":'10'},
                    '3': {'Cbx':False, "MAdir":u'高于', "MAdays":'60', "DiffDir":u'至少', "DiffValue":'10'},
                    '4': {'Cbx':False, "MAdir":u'高于', "MAdays":'60', "DiffDir":u'至少', "DiffValue":'10'},
                    '5': {'Cbx':False, "MAdir":u'高于', "MAdays":'60', "DiffDir":u'至少', "DiffValue":'10'},
                    '6': {'Cbx':False, "MAdir":u'高于', "MAdays":'60', "DiffDir":u'至少', "DiffValue":'10'} }
    def getInitEndCondData(self):
        return {'Cbx':True, "MAdir":u'高于', "MAdays":'60', "DiffDir":u'至少', "DiffValue":'10'}
    
    def addMAvaluesToDF(self, df):
        MAdays = []
        MAdays.append(int(self.preCond['MAdays']))
        MAdays.append(int(self.cvrEndCond['MAdays']))
        for idx in self.cond:
            MAdays.append(int(self.cond[idx]['MAdays']))
        for maday in set(MAdays):
            df['ma%s'%maday]= df.groupby('ts_code')['close'].apply(lambda x: x.rolling(maday).mean())
    def cleanDFbyPreCond(self,df):
        if (self.preCond['Cbx']==True):
            preMAday = int(self.preCond["MAdays"])
            preDiffValue = float(self.preCond["DiffValue"])/100
            cvrDays = int(self.cvrDays)
            df['pre']=(df['close']-df['ma%s'%preMAday]*(1+preDiffValue))>0
            #移动和
            df['pre']= df.groupby('ts_code')['pre'].apply(lambda x: x.rolling(cvrDays).sum())
            #收盘价连续大于MA20 5天
            df['pre']=df['pre']>=cvrDays
            #将首次满足条件后的每一天都标注True
            df['pre']= df.groupby('ts_code')['pre'].apply(lambda x: x.cumsum())
            df['pre'] = df['pre']>0
            # drop row with df['pre']==False, which are not satisfied preCond
            df.drop(df.index[df['pre']==False], inplace=True)
    def popDFbyEndCond(self, df):
        if (self.cvrEndCond['Cbx']==True):
            cvrEndDays = int(self.cvrEndDays)
            cvrEndMAdays = int(self.cvrEndCond['MAdays'])
            cvrEndDiffValue = float(self.cvrEndCond['DiffValue'])/100
            #求移动平均
            #df['end']= df.groupby('ts_code')['close'].apply(lambda x: x.rolling(cvrEndMAdays).mean())
            df['end']=(df['close']-df['ma%s'%cvrEndMAdays]*(1-cvrEndDiffValue))<0
            #移动和
            df['end']= df.groupby('ts_code')['end'].apply(lambda x: x.rolling(cvrEndDays).sum())
            #收盘价连续大于MA20 5天
            df['end']=(df['end']>=cvrEndDays)
            #将首次满足终止条件后的每一天都标注True
            df['end']= df.groupby('ts_code')['end'].apply(lambda x: x.cumsum())
            df['end'] = (df['end']>0)
            # drop and reserved the data satisfied 'end' condition
            df_tailed = df[df['end']==True].copy()
            df.drop(df.index[df['end']==True], inplace=True)
            return df_tailed
        else:
            # return empty dataframe
            return pd.DataFrame()
    def dropDFbyCond(self, df):
        cvrDays = int(self.cvrDays)
        for idx in self.cond:
            if self.cond[idx]['Cbx']==True:
                MAdays=int(self.cond[idx]['MAdays'])
                DiffValue = float(self.cond[idx]['DiffValue'])/100
                print("cond%s MAdays = %d"%(idx,MAdays))
                #计算移动平均
                #df['cond']= df.groupby('ts_code')['close'].apply(lambda x: x.rolling(MAdays).mean())
                #选择Close > 移动平均
                df['cond']=(df['close']-df['ma%s'%MAdays]*(1+DiffValue))>0
                #df['cond'].to_csv(r'data/cond.csv', index=False)
                #df['condFlag'].to_csv(r'data/condFlag.csv', index=False)
                df['condFlag'] = df['condFlag'] & df['cond']
                #df['condFlag'].to_csv(r'data/condFlag_rlt.csv', index=False)
        #求移动和(连续M天True)
        df['condFlag']= df.groupby('ts_code')['condFlag'].apply(lambda x: x.rolling(MAdays).sum())
        df['condFlag']=df['condFlag']>=cvrDays
        #将满足连续"M天Cond"之后的日期都标记为True
        df['condFlag']= df.groupby('ts_code')['condFlag'].apply(lambda x: x.cumsum())
        df['condFlag'] = df['condFlag']>0
        #删除不满足条件的行
        df.drop(df.index[df['condFlag']==False], inplace=True)
    
    def startCVR(self,df):
        cvrThreshold = int(self.cvrThreshold )
        #量能开始
        rslt = pd.DataFrame(index=df.groupby('ts_code').first().index)
        dfCodeDate = df.groupby('ts_code')['trade_date'].first()
        #1st CV, start date 
        rslt = pd.merge(rslt,dfCodeDate.to_frame(),how='inner', on=['ts_code'])
        #量能结束        
        df['cv']= df.groupby('ts_code')['turnover_rate'].apply(lambda x: x.cumsum())
        df['cvflag']=df['cv']>=cvrThreshold
        #df_reserved = df[df['cvflag']==False].copy()       #not used, drop
        df.drop(df.index[df['cvflag']==False], inplace=True)
        dfCodeDateCV = df.groupby('ts_code')['trade_date', 'cv'].first()
        #第一次量能筛选结果, how=inner, start date is del if end data not exist
        # 1st CV: startdate, end date, cv
        rslt = pd.merge(rslt,dfCodeDateCV,how='inner',on=['ts_code'])
        return rslt

    def calcCVR(self):
        starttime = time.time()

        # start, init gauge
        pub.sendMessage("pubMsg_CVRatioModel", msg=("startCVRBtn", None))   #set panel off, start gauge
        pub.sendMessage("pubMsg_CVRatioModel", msg=("updateGaugeCounter", 5))
        #1. data init. outside the loop.
            #a. read all data from database, and sort by date
            #b. calc all MA values
        preMAday = int(self.preCond["MAdays"])
        preDiffValue = float(self.preCond["DiffValue"])/100
        cvrDays = int(self.cvrDays)
        
        
        cmd="SELECT trade_date,ts_code, close, turnover_rate FROM hqall_t"
        df=pd.read_sql_query(cmd, self.engine)

        logger.debug("pd.read_sql_query: %s",  "%.2f"%(time.time()-starttime))
        starttime = time.time()

        #对时间排序
        df = df.sort_values(by='trade_date', ascending=True)

        logger.debug("df.sort_values: %s",  "%.2f"%(time.time()-starttime))
        starttime = time.time()

        #添加所有移动平均到DataFrame
        self.addMAvaluesToDF(df)
        ##df['pre']= df.groupby('ts_code')['close'].apply(lambda x: x.rolling(preMAday).mean())
        
        logger.debug("addMAvaluesToDF: %s",  "%.2f"%(time.time()-starttime))
        starttime = time.time()

        #init 'condflag' column to True
        df['condFlag']=True
        #最终结果
        finalRslt = pd.DataFrame(index=df.groupby('ts_code').first().index)
        #满足量能次数
        cvrRltIdx=0
        while (not df.empty):
            cvrRltIdx+=1
            df = df.sort_values(by='trade_date', ascending=True)

            logger.debug("df.sort_values: %s",  "%.2f"%(time.time()-starttime))
            starttime = time.time()

            #2. 1st loop, calc preCond, 
            self.cleanDFbyPreCond(df)

            logger.debug("cleanDFbyPreCond: %s",  "%.2f"%(time.time()-starttime))
            starttime = time.time()

            df_tailed = self.popDFbyEndCond(df)

            logger.debug("popDFbyEndCond: %s",  "%.2f"%(time.time()-starttime))
            starttime = time.time()

            #3. 2nd loop the "cond1-cond7", calc cond
            self.dropDFbyCond(df)
            
            logger.debug("dropDFbyCond: %s",  "%.2f"%(time.time()-starttime))
            starttime = time.time()

            #4. start caculation CV
            rslt = self.startCVR(df)

            logger.debug("startCVR: %s",  "%.2f"%(time.time()-starttime))
            starttime = time.time()
            ##量能开始
            #rslt = pd.DataFrame(index=df.groupby('ts_code').first().index)
            #dfCodeDate = df.groupby('ts_code')['trade_date'].first()
            ##1st CV, start date 
            #rslt = pd.merge(rslt,dfCodeDate.to_frame(),how='inner', on=['ts_code'])

            ##量能结束        
            #df['cv']= df.groupby('ts_code')['turnover_rate'].apply(lambda x: x.cumsum())
            #df['cvflag']=df['cv']>=cvrThreshold
            #df_reserved = df[df['cvflag']==False].copy()
            #df.drop(df.index[df['cvflag']==False], inplace=True)
            #dfCodeDateCV = df.groupby('ts_code')['trade_date', 'cv'].first()
            ##第一次量能筛选结果, how=inner, start date is del if end data not exist
            ## 1st CV: end date, cv
            #rslt = pd.merge(rslt,dfCodeDateCV,how='inner',on=['ts_code'])
            
            #rslt.rename(columns={'A':'a', 'B':'b', 'C':'c'}, inplace = True)
            #print(rslt)


            #最终结果
            if finalRslt.empty==True:
                howPara='inner'
                # add code column to DF
                finalRslt['ts_code']=finalRslt.index
            else:
                howPara='left'
            if (not rslt.empty):
                rslt.columns = [u'第%s次开始'%cvrRltIdx, u'第%s次结束'%cvrRltIdx, u'第%s次量能'%cvrRltIdx]
                finalRslt = pd.merge(finalRslt,rslt,how=howPara, on=['ts_code'])
            print(finalRslt)
            # resume dropped data, for next preCond detect

            print("length of df is %d, before attend"%len(df))
            if (not df_tailed.empty):
                df = df.append(df_tailed, sort=False)
            print("length of df is %d, after attend"%len(df))
            logger.debug("finalRslt: %s",  "%.2f"%(time.time()-starttime))
            starttime = time.time()        
        #finalRslt.to_csv(r'data/finalRslt.csv', index=False, encoding='utf_8_sig')
        

        #for i in range(10):
        #    if self.runCvrAllowed:
        #        time.sleep(1)
        #        pub.sendMessage("pubMsg_CVRatioModel", msg=("updateGaugeCounter", i*10))
        #    else:
        #        break
        pub.sendMessage("pubMsg_CVRatioModel", msg=("endCVRBtn", None))
    

        

def main():
    pass
if __name__ == '__main__':
    main()


'''

engine = create_engine('sqlite+pysqlite:///nfq_hqData.db', module=sqlite)
df = ts.get_k_data('000673', '2018-09-08', '2018-10-17')
df.to_csv('000673.csv')
N=20
df['diffN']=df['close'].diff(N)

#RPS caculation
df = ts.get_k_data('000673', '2018-09-08', '2018-10-17')
df['diff20']=df['close'].diff(20)
df['rate']=df['diff20']/(df['close']+df['diff20'])
df['rps20']=df['rate'].sort_values(ascending=False).index

api = ts.pro_api('ded43ecfd7bc26fa6938e63d9578d44d00fba560859a900654b46687')
df = ts.pro_bar(pro_api=api, ts_code='000571.SZ', adj='qfq', start_date='20180101', end_date='20181011')
df.to_csv('000571.SZ.csv')

#add a new column
cmd="ALTER TABLE hqall_t ADD pct_5 float"   
2018-10-23 00:00:00.000000
603999
#change a column values
cmd = "UPDATE hqall_t SET pct_5 = 0.22 WHERE code = '603999' AND date = '2018-10-23 00:00:00.000000'"
cmd = "UPDATE %s SET %s = %f WHERE code = '%s' AND date = '%s'"%(table_nm, column_nm, data, code, date)


# Get num of rows 
cmd = "SELECT COUNT(code) FROM hqall_t WHERE code='603999'"
#[(112)]

#order
cmd="SELECT date, close FROM hqall_t WHERE code='603999' ORDER BY date "

# get '603999' from sqlite3 data, not order
cmd="SELECT date, close FROM hqall_t WHERE code='603999'"
a=engine.execute(cmd)
b=a.fetchall()
N=20
c=b[20][1]

#search the No mth data, m=20
cmd="SELECT date, close FROM hqall_t WHERE code='603999' limit 20,1"
a=engine.execute(cmd)
b=a.fetchall()

#use cmd like this:
my_code=('603999',)
cmd = "SELECT * FROM hqall_t WHERE code = ?"
a=engine.execute(cmd,my_code)
df=pd.read_sql_query(cmd, engine, params=my_code)

df['diff20']=df['close'].diff(-20)
df['rate']=df['diff20']/(df['close']+df['diff20'])
df['rps20']=df['rate'].rank(method="first")
 c = df.apply(lambda x:(x[10],x[7],x[0]), axis=1)
 d=tuple(c)
cmd="ALTER TABLE hqall_t ADD rps20 Integer" 
a = engine.execute(cmd)
cmd = "UPDATE hqall_t SET rps20 = ? WHERE code = ? AND date = ?"

a = engine.execute(cmd, d)
value, code, date

#pandas read_sql
cmd="SELECT date, close FROM hqall_t WHERE code='603999'"
df=pd.read_sql_query(cmd, engine)


engine = create_engine('sqlite+pysqlite:///nfq_hqData.db', module=sqlite)
cmd="SELECT * FROM hqall_t WHERE code='603999'"
df=pd.read_sql_query(cmd, engine)
df['diff20']=df['close'].diff(-20)
df['rate']=df['diff20']/(df['close']+df['diff20'])
df['rps20']=df['rate'].rank(method="first")
 c = df.apply(lambda x:(x[10],x[7],x[0]), axis=1)
 d=tuple(c)

diff_nm='diff20'
rpsN='20'
pct_nm='rate20'
rps_nm='rps20'
df[diff_nm]=df['close'].diff(-int(rpsN))
df[pct_nm]=df[diff_nm]/(df['close']+df[diff_nm])
df[rps_nm]=df[pct_nm].rank(method="first")
c = df.apply(lambda x:(x[pct_nm],x['code'],x['date']), axis=1)



#查询字段名称是否存在
cmd="SELECT COUNT('pct20') from hqall_t"

cmd = "if not exist SELECT pct240 from hqall_t limit 0,1 ALTER TABLE hqall_t ADD pct240 float"

 cmd = "select *  from sqlite_master"
  cmd = "select sql  from sqlite_master"^M
 b=engine.execute(cmd).fetchall()
 for i in b[2]:
     if isinstance(i, str):
         if ('pct20' in i):
             print(True)
https://www.cnblogs.com/hbtmwangjin/p/7941403.html

通过reset_index()函数可以将groupby()的分组结果转换成DataFrame对象，这样就可保存了！！

#load all data
engine = create_engine('sqlite+pysqlite:///nfq_hqData.db', module=sqlite)
cmd="SELECT * FROM hqall_t"
df=pd.read_sql_query(cmd, engine)
dfg = df.groupby([df['code'],df['date']])
df['pct20']=df['close'].groupby([df['code'], df['date']]).pct_change(20)


df[['code','date','close']]
df.set_index(['code', 'date'])
dfg = ddf.groupby([ddf['code'],ddf['date']])


engine = create_engine('sqlite+pysqlite:///nfq_hqData.db', module=sqlite)
#cmd="SELECT * FROM hqall_t where code='600999' or code ='000703' "
cmd="SELECT * FROM hqall_t"
df=pd.read_sql_query(cmd, engine)
#dff = df.groupby('code')['close'].apply(lambda x: x.pct_change(20))
df['pct20']= df.groupby('code')['close'].apply(lambda x: x.pct_change(20))
df['rps20'] = df.groupby('date')['pct20'].apply(lambda x: x.rank(pct=True))*100
df.to_sql('hqall_t', engine, if_exists='replace',index=True)

#排序 
df.sort_values(by='code')
#转换 date'
df['date_parsed'] = pd.to_datetime(df['date'], format = "%Y%m%d", errors = 'coerce')
data['date_parsed'] = pd.to_datetime(data['Date'],infer_datetime_format=True)

#选择数据库日期最大值
engine = create_engine('sqlite+pysqlite:///nfq_hqData.db', module=sqlite)
cmd = "SELECT MAX(%s) FROM %s WHERE code='%s'"%("date", "hqall_t", "600703")

cmd="SELECT * FROM hqall_t where date='2018-10-22 00:00:00.000000' or date ='2018-09-07 00:00:00.000000' "
df=pd.read_sql_query(cmd, engine)
df["_pct"]= (df.groupby('code')['close'].apply(lambda x: x.pct_change(-1))).round(4)
df["_pct"]= (df.groupby('code')['close'].apply(lambda x: x.pct_change(-1))).round(4)
df["_rps"] = (df.groupby('date')["_pct"].apply(lambda x: x.rank(pct=True))*100).round(1)
df[df['date']=='2018-10-22 00:00:00.000000']['close']  - df[df['date']=='2018-09-07 00:00:00.000000']['close']

#Tushare, New API
pro = ts.pro_api()
df = pro.daily(trade_date='20180810')
df = ts.pro_bar(pro_api=api, ts_code='000001.SZ', adj='qfq', start_date='20160101', end_date='20181111')

#下载某天全部数据
 df1 = pro.daily(trade_date='20180726')

 #获取股票列表
 data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,fullname,enname, market, exchange, curr_type, list_status, list_date, delist_date, is_hs')


 cmd = "SELECT trade_date FROM %s where ts_code = '%s'"%('hqall_t', '000001.SZ')            #all codes in 1 table
 df=pd.read_sql_query(cmd, engine)

 #某天换手率
 df1 = pro.daily_basic(ts_code='', trade_date='20180726')
 #某天日线数据
 df2 = pro.daily(trade_date='20180726')

 #某天复权因子
 df3 = pro.adj_factor(ts_code='', trade_date='20180726')

 df1.to_csv("df1.csv",index=False)
 df2.to_csv("df2.csv",index=False)
 df3.to_csv("df3.csv",index=False)

 df1.drop(['code'],axis=1, inplace=True)
 df4 = pd.merge(df2,df1,on=['ts_code','trade_date'])
 df5 = pd.merge(df4,df3,on=['ts_code','trade_date'])
 df5['weighted_close']=(df5['close']*df5['adj_factor']).round(2)
 ++++++++++++++++++

engine = create_engine('sqlite+pysqlite:///nfq_hqData.db', module=sqlite) 
engine = create_engine('sqlite+pysqlite:///hfq_hqData.db', module=sqlite)
cmd="SELECT trade_date,ts_code, close, turnover_rate FROM hqall_t"
df=pd.read_sql_query(cmd, engine)
#对时间排序
df = df.sort_values(by='trade_date', ascending=True)
#求移动平均
df['ma30']= df.groupby('ts_code')['close'].apply(lambda x: x.rolling(30).mean())
df['diff']=(df['close']-df['ma30']*1.1)>0
#移动和
df['A']= df.groupby('ts_code')['diff'].apply(lambda x: x.rolling(5).sum())
df['B']=df['A']>4
#收盘价连续大于MA20 5天
df['C']= df.groupby('ts_code')['B'].apply(lambda x: x.cumsum())
#保存000001.SZ到csv
df[df['ts_code']=='000001.SZ'].to_csv('000001.csv', index=False)
'''