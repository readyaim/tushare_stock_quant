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
from functools import wraps
from threading import Timer

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
myTokenStr = "c67582e89f032796a3ff49f4554d9833026c35209f648bee80ef645b"
import tushare as ts
ts.set_token(myTokenStr)
api = ts.pro_api(myTokenStr)
pro = ts.pro_api(myTokenStr)
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

def log_time_delta(func):
    """Log function running time"""
    @wraps(func)
    def deco(*args, **kwargs):
        start = datetime.now()
        res = func(*args, **kwargs)
        end = datetime.now()
        delta = end - start
        logger.debug("Tushare download time is %s", delta)
        return res
    return deco

def log_memory_usage(func):
    """Log memory and time usage"""
    @wraps(func)
    def deco(*args, **kwargs):
        memInfo = psutil.virtual_memory()
        startMemUsage = psutil.Process(os.getpid()).memory_info().rss
        start = time.time()
        func(*args, **kwargs)
        logger.debug("Caculation is finished!! Time used: %.2fs",(time.time()-start))
        endMemUsage = psutil.Process(os.getpid()).memory_info().rss
        logger.info("memory usage: start=%sKB, end=%sKB, diff = %sKB", format(startMemUsage/1000,',.0f'),\
                                 format(endMemUsage/1000,',.0f'), format((endMemUsage-startMemUsage)/1000,',.0f'))
        gc.collect()
#        return res
    return deco


def time_limit(interval):
    """raise an TimeoutError if timeout"""
    @wraps(interval)
    def deco(func):
        def time_out():
            logger.debug("timeout %d for function ", interval)
            raise TimeoutError()
            #return pd.DataFrame()

        @wraps(func)
        def deco(*args, **kwargs):
            timer = Timer(interval, time_out)
            #print(interval)
            timer.start()
            res = func(*args, **kwargs)
            timer.cancel()
            return res
        return deco
    return deco
        




class Sqlite3Handler(object):
    def __init__(self, pubMsg_Source, autypeStr='qfq'):
        self.pubMsg_Source = pubMsg_Source
        self.sql_filename_base = 'hqData.db'
        self.sql_filename = self.sql_filename_base
        self.autypeStr = autypeStr
        self.set_DBname_and_autype(self.autypeStr)
        self.hq_codes = self.get_codes()
        self.tablenm_hqall='hqall_t'
        self.date_tail = '00:00:00.000000'
        self.tablenm_rawdata = 'rawdata_t'
        self.holidayDateStrs = ['20181005', '20181004', '20181003', '20181002', '20181001', \
                         '20180924', '20180618', '20180501', '20180430', '20180406', \
                         '20180405', '20180221', '20180220', '20180219', '20180216', \
                         '20180215', '20180105', '20180104', '20180103', '20180101', \
                         '20171006', '20171005', '20171004', '20171003', '20171002', \
                         '20170530', '20170529', '20170501', '20170404', '20170403', \
                         '20170202', '20170201', '20170131', '20170130', '20170127', \
                         '20170102']

    def isHoliday(self, targetdate):
        if targetdate.isoweekday() in [6,7]:
            return True
        dateStr = targetdate.strftime("%Y%m%d")
        if dateStr in self.holidayDateStrs:
            return True
        else:
            return False
            
    def get_startdate_byworkday(self, eDateStr, forwardays):
        eDate = datetime.strptime(eDateStr, "%Y%m%d")
        step = 1 if forwardays>=0 else -1
        while (self.isHoliday(eDate)):
            eDate = eDate-timedelta(step)
        # init 
        dayCounter = 0
    #    eDate = eDate-timedelta(1)
        while (dayCounter< abs(forwardays)):
            if (not self.isHoliday(eDate)):
                dayCounter+=1
            eDate = eDate-timedelta(step)
        return eDate.strftime("%Y%m%d")

    def updateMaxDateInDB(self, dateRange):
        maxDateStr, minDateStr = dateRange
        cmd = "UPDATE attr_t SET maxdate = '%s' , mindate='%s' "%(maxDateStr, minDateStr)
        ##self.que.put(('cmd', cmd))
        self.engine.execute(cmd)
        logger.debug("set %s to attr_t maxdate, %s to attr_t mindate", maxDateStr, minDateStr)
    
    def checkTableExists(self, tablenm):
        cmd = "select count(*)  from sqlite_master where type='table' and name = '%s'"%tablenm
        if ((self.engine.execute(cmd).fetchall()[0][0])==0):
            logger.debug("%s NOT exist in %s", tablenm, self.sql_filename)
            return False
        else:
            #logger.debug("%s exists in %s", tablenm, self.sql_filename)
            return True
    def delTableData(self, tablenm):
        """ Del all data in table, keep the table itself"""
        if self.checkTableExists(tablenm):
            logger.debug("deleting all data in %s", tablenm)
            cmd = "delete from %s"%tablenm
            self.engine.execute(cmd)
            #logger.debug("delete all data in %s", tablenm)

    def readMaxDateInAttr_t(self):
        cmd = "SELECT maxdate FROM %s "%('attr_t')
        maxDate = self.engine.execute(cmd).fetchone()[0]
        #cmd = "SELECT mindate FROM %s "%('attr_t')
        #minDate = self.engine.execute(cmd).fetchone()[0]
        return maxDate

    def readMinDateInAttr_t(self):
        cmd = "SELECT mindate FROM %s "%('attr_t')
        minDate = self.engine.execute(cmd).fetchone()[0]
        #cmd = "SELECT mindate FROM %s "%('attr_t')
        #minDate = self.engine.execute(cmd).fetchone()[0]
        return minDate
    def getMaxDateInDB(self):
        if self.checkTableExists(self.tablenm_hqall):
            #TODO: get code from database, not use '000001.SZ'
            cmd = "SELECT MAX(%s), MIN(%s) FROM %s WHERE ts_code='%s'"%("trade_date","trade_date", self.tablenm_hqall, "000001.SZ")
            try:
                #dateStr = self.engine.execute(cmd).fetchone()[0].split(" ")[0]
                maxDateStr, minDateStr = self.engine.execute(cmd).fetchone()
                logger.info("maxinum date is %s, minimum date is %s", maxDateStr, minDateStr)
            except Exception as e:
                logger.error("Error to read max/min date!\n, %s",e)
                maxDateStr, minDateStr = '19700101', '19700101'
        else:
            logger.error("failed to read max/min Date in %s, because %s is not existed in %s\n",self.tablenm_hqall, self.tablenm_hqall, self.sql_filename)
            maxDateStr, minDateStr = '19700101', '19700101'
        return maxDateStr, minDateStr

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
        #print(codes)
        return list(codes)
    def initDB(self):
        """Generate 'codes_t', which has all stock codes, into sqlite_db if there is no 'codes_t' in sqlite_db"""
        # 1. check if 'stock_basic_t' exists
        cmd = "select count(*)  from sqlite_master where type='table' and name = '%s'"%'stock_basic_t'
        if ((self.engine.execute(cmd).fetchall()[0][0])==0):
            # 2. 'stock_basic_t' not exists, check if 'stock_basic.csv' exists. Try to generate 'stock_basic_t' from 'stock_basic.csv'
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

    def getDataFromOneTableByCmd(self, tablenm, cmd):
        if self.checkTableExists(tablenm):
            try:
                df=pd.read_sql_query(cmd, self.engine)
            except Exception as e:
                logger.debug("%s",e)
                df = pd.DataFrame()
            return df
        else:
            return pd.DataFrame()
    
    def getAllDataFromTables(self, cmds):
        df = pd.DataFrame()
        for key in cmds:
            df1 = self.getDataFromOneTableByCmd(key, cmds[key])
            if not df1.empty:
                df = pd.concat([df, df1], ignore_index=True, sort = False)
        return df
    def getDataByCode(self, tscode):
        logger.debug("run getDatabyCode: %s"%tscode)
        params = (tscode,)
        cmd1="SELECT * FROM %s WHERE ts_code = '%s' "%(self.tablenm_hqall, tscode)
        cmd2="SELECT * FROM %s WHERE ts_code = '%s' "%(self.tablenm_rawdata, tscode)
        cmds = {self.tablenm_hqall: cmd1, self.tablenm_rawdata:cmd2}
        
#        params = ('ts_code','trade_date','open','high','low','close','vol','turnover_rate','turnover_rate_f','weighted_close')
#        cmd="SELECT ?,?,?,?,?,?,?,?,?,? FROM %s WHERE ts_code = %s "%(self.tablenm_hqall, tscode)
        try:
#            df=pd.read_sql_query(cmd, self.engine, params= params)
            df=self.getAllDataFromTables(cmds)
            
        except Exception as e:
            logger.error("read data by ts_code from %s error", self.tablenm_hqall)
            logger.error(e)
            pub.sendMessage(self.pubMsg_Source, msg="end_getDataByCode")
            return
        if (len(df)!=0):
            df_sorted = df.sort_values(by='trade_date', ascending=True)
            #只截取self.rpsDayCount天
#            df_sorted['ma20'] = pd.rolling(df_sorted).mean()
            dayCount = self.cvrDisplayDay  #getattr(self, self.cvrDisplayDay, 150)
            
            #计算均值
            df_sorted['ma5'] = df_sorted.weighted_close.rolling(5).mean().to_frame()
            df_sorted['ma30'] = df_sorted.weighted_close.rolling(30).mean().to_frame()
            df_sorted['ma60'] = df_sorted.weighted_close.rolling(60).mean().to_frame()
            df_sorted=df_sorted.iloc[-int(dayCount):,:]
            # Start, sorted and add idx to DF to draw k-line without blank day
            df_sorted.index = range(0, len(df_sorted))
            df_sorted['date_idx'] = np.arange(len(df_sorted))
            
            # end
            logger.debug('read data by ts_code from base to dataframe success! len = %d', len(df))
            pub.sendMessage(self.pubMsg_Source, msg=("end_getDataByCode", df_sorted))
            
        else:
            logger.debug('Error, database read data error, len = %d', len(df))
            pub.sendMessage(self.pubMsg_Source, msg="end_getDataByCode")     

#    def get_startdate_byworkday(self,end_date_str, numofdays):
#        end_date = datetime.strptime(end_date_str, "%Y%m%d")
#        if end_date.isoweekday() in [6,7]:
#            preDate = end_date-timedelta(end_date.isoweekday()-5)
#        else:
#            preDate = end_date
#        while (numofdays>1):
#            if (preDate.isoweekday() not in [6,7]):
#                numofdays-=1
#                preDate = preDate-timedelta(days=1)
#            else:
#                preDate = preDate-timedelta(days=1)
#        while(preDate.isoweekday() in [6,7]):
#            preDate = preDate-timedelta(days=1)
#        return preDate.strftime("%Y%m%d")
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
        self.pFuncCalcRPS = self.calcNewAddedRPS
        super(CalcRPS_Model, self).__init__("pubMsg_CalcRPS_Model", "hfq")
    
    def showMsgDialog(self):
        dlg = wx.MessageDialog(None, u"数据库没有找到attr_t表格, 请重新任意一天数据即可修复", u"数据库缺失表格", wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            self.Close(True)
        dlg.Destroy()
    
    def getClippedMaxDate(self, dateStr):
        """Return the clipped (smaller) Max Date between(date in database, dateStr)
        """
        try:
            self.maxDateInDBStr = self.readMaxDateInAttr_t()
        except Exception as e:
            logger.debug(e)
            self.maxDateInDBStr, self.minDateInDBStr = self.getMaxDateInDB()
        logger.debug("maxDateInDBStr is %s", self.maxDateInDBStr)
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

    def readDataFromTable(self, tablenm, *args):
        if self.checkTableExists(tablenm):
            cmd = "select * from %s"%tablenm
            if (len(args)>0):
                #cmd = "select * from %s where trade_date between '%s' and '%s'"%(tablenm, args[0], args[1])
                cmd = "select trade_date, ts_code, weighted_close from %s where trade_date between '%s' and '%s'"%(tablenm, args[0], args[1])
            try:
                df=pd.read_sql_query(cmd, self.engine)
            except Exception as e:
                logger.debug("%s",e)
                df = pd.DataFrame()
            return df
        else:
            return pd.DataFrame()
    
    @log_memory_usage  
    def calcNewAddedRPS(self):
        logger.debug("run calcNewAddedRPS() method")
        counter = 10
        pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", counter))
#        memInfo = psutil.virtual_memory()
#        startMemUsage = psutil.Process(os.getpid()).memory_info().rss
#        start = time.time()
        #self.rpsN = '20'        #TODO: this is only for debug, should be removed in formal useage
        #logger.debug("calculation RPS start!")
        logger.debug("database =%s", self.sql_filename)
        if self.rpsN not in self.rpsNChoices:
            self.rpsNChoices.append(self.rpsN)
        logger.debug("reading df_rawdata_t...")
        df_rawdata_t = self.readDataFromTable(self.tablenm_rawdata)
        

        if (not df_rawdata_t.empty):
            rpsColNames = ['trade_date', 'ts_code']
            logger.debug("len of df_rawdata_t is %s", len(df_rawdata_t))
            newDates = list(df_rawdata_t.trade_date.values)
            eDates = min(newDates)
            sDates = self.get_startdate_byworkday(eDates, 350)
            logger.debug("reading df_hqall_t...")
            
            df_hqall_t = self.readDataFromTable(self.tablenm_hqall, sDates, eDates)
            if (not df_hqall_t.empty):
                logger.debug("len of df_hqall_t is %s", len(df_hqall_t))
                df = pd.concat([df_hqall_t, df_rawdata_t], ignore_index=True, sort = False)
            else:
                logger.debug("len of df_hqall_t is 0")
                df = df_rawdata_t.copy()
            try:
                logger.debug("start caculating...")
                df = df.sort_values(by='trade_date', ascending=False)
                #df = df.groupby(df['ts_code'], as_index =False).apply(lambda x: x.sort_values(by='trade_date', ascending=False))
                for rpsNstr in self.rpsNChoices:
                    rps_nm = 'rps%s'%rpsNstr
                    pct_nm = 'pct%s'%rpsNstr
                    rpsN = int(rpsNstr)
                    rpsColNames.extend([rps_nm, pct_nm])
                    
                    logger.debug("caculating %s", rps_nm)
#                    if rps_nm in list(df.columns):
#                        logger.debug("%s existed in database, continue", rps_nm)
#                        continue
                    df[pct_nm]= (df.groupby(df['ts_code'])['weighted_close'].apply(lambda x: x.pct_change(-rpsN))).round(4)
                    df[rps_nm] = (df.groupby(df['trade_date'])[pct_nm].apply(lambda x: x.rank(pct=True))*100).round(1)
                    counter += 15
                    pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", counter))
                logger.debug('caculation is done! Start saving...')
            except Exception as e:
                logger.error("dataframe caculation is wrong!")
                logger.error(e)
                pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")
                return
            #df = df.groupby(df['ts_code'], as_index =False).apply(lambda x: x.sort_values(by='trade_date', ascending=False))
            #df[pct_nm]= (df.groupby(df['ts_code'])['weighted_close'].apply(lambda x: x.pct_change(-rpsN))).round(4)
            #df[rps_nm] = (df.groupby(df['trade_date'])[pct_nm].apply(lambda x: x.rank(pct=True))*100).round(1)
            #a = ['trade_date', 'ts_code', 'rps20, rps50, rps']
            df_rps = pd.merge(df_rawdata_t,df[rpsColNames],how='inner', on = ['trade_date', 'ts_code'])
            #pd.io.sql.to_sql(df3, 'hqall_t', engine, if_exists='append',index=False, chunksize= 10000)

            pd.io.sql.to_sql(df_rps, self.tablenm_hqall, self.engine, if_exists='append',index=False, chunksize= 10000)
            self.delTableData(self.tablenm_rawdata)

            #更新maxdate in attr_t
            self.updateMaxDateInDB(self.getMaxDateInDB())
            counter = 100
            pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", counter))
#            logger.debug("Caculation is finished!! Time used: %.2fs",(time.time()-start))
#            endMemUsage = psutil.Process(os.getpid()).memory_info().rss
#            logger.info("memory usage: start=%sKB, end=%sKB, diff = %sKB", format(startMemUsage/1000,',.0f'),\
#                                 format(endMemUsage/1000,',.0f'), format((endMemUsage-startMemUsage)/1000,',.0f'))
#            gc.collect()
            pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")
        else:
            logger.debug("No new data to calculate")
            pub.sendMessage("pubMsg_CalcRPS_Model", msg="end_calcAllRPS")
    
    @log_memory_usage
    def calcAllRPS(self):
        '''Read out all data from sql database, transfer, and generate 'pctN' and 'rpsN' two columns.
        Then write back to database
        '''
        counter = 10
        pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", counter))
#        memInfo = psutil.virtual_memory()
#        startMemUsage = psutil.Process(os.getpid()).memory_info().rss
#        start = time.time()
        #self.rpsN = '20'        #TODO: this is only for debug, should be removed in formal useage
        logger.debug("calculation RPS start!")
        logger.debug("database =%s", self.sql_filename)

        #self.createColumnIfnotExist()
        if self.rpsN not in self.rpsNChoices:
            self.rpsNChoices.append(self.rpsN)
#        pct_nm = 'pct%s'%self.rpsN
#        rps_nm = 'rps%s'%self.rpsN
#        rpsN = int(self.rpsN)
#        cmd="SELECT * FROM %s"%self.tablenm_hqall
        #params = ('ts_code', 'trade_date', 'weighted_close')
        #cmd="SELECT ?,?,? FROM %s"%self.tablenm_hqall
#        logger.debug("sql cmd: %s", cmd)
        cmd1="SELECT * FROM %s"%(self.tablenm_hqall)
        cmd2="SELECT * FROM %s"%(self.tablenm_rawdata)
        cmds = {self.tablenm_hqall: cmd1, self.tablenm_rawdata:cmd2}
        
        try:
#            df=pd.read_sql_query(cmd, self.engine)
            df=self.getAllDataFromTables(cmds)
#            df = pd.read_sql_table('hqall_t', self.engine)
            #df=pd.read_sql_query(cmd, self.engine, params = params)
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
#                df = df.groupby('ts_code').apply(lambda x: x.sort_values(by='trade_date', ascending=False))
                df = df.sort_values(by='trade_date', ascending=False)
                for rpsNstr in self.rpsNChoices:
                    rps_nm = 'rps%s'%rpsNstr
                    pct_nm = 'pct%s'%rpsNstr
                    rpsN = int(rpsNstr)
                    logger.debug("caculating %s", rps_nm)
#                    if rps_nm in list(df.columns):
#                        logger.debug("%s existed in database, continue", rps_nm)
#                        continue
                    df[pct_nm]= (df.groupby(df['ts_code'])['weighted_close'].apply(lambda x: x.pct_change(-rpsN))).round(4)
                    df[rps_nm] = (df.groupby(df['trade_date'])[pct_nm].apply(lambda x: x.rank(pct=True))*100).round(1)
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
                
#                # udpate table instead of replacing all. Really slow...
#                df.fillna(0, inplace=True)
#                params = df[[rps_nm, 'ts_code', 'trade_date']].values.tolist()
#                cmd = "UPDATE hqall_t SET rps20 = ? WHERE ts_code = ? AND trade_date = ?"
#                engine.execute(cmd, params)
                counter = 100
                pub.sendMessage("pubMsg_CalcRPS_Model", msg=("nmRpsGauage", counter))
            except Exception as e:
                logger.error(e)
                
#            logger.debug("Caculation for %s is finished!! Time used: %.2fs",rps_nm,(time.time()-start))
#            
#            endMemUsage = psutil.Process(os.getpid()).memory_info().rss
#            logger.info("memory usage: start=%sKB, end=%sKB, diff = %sKB", format(startMemUsage/1000,',.0f'),\
#                                 format(endMemUsage/1000,',.0f'), format((endMemUsage-startMemUsage)/1000,',.0f'))
#            gc.collect()
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
        super(DnldHQDataModel, self).__init__("pubMsg_DnldHQDataModel", 'hfq')
        self.que = Queue()
        self.enableQue = False
        
    def buildAttrTableIfNotExist(self):
        if (not self.checkTableExists('attr_t')):
            try:
                maxDateStr, minDateStr = self.getMaxDateInDB()
            except Exception as e:
                logger.error(e)
                maxDateStr="19700101"
            logger.debug("creat attr_t and init maxdate= %s", maxDateStr)
            #df = pd.DataFrame([maxDateStr, minDateStr], columns=['maxdate', 'mindate'],index=['info'])
            df=pd.DataFrame({'maxdate':[maxDateStr], 'mindate':[minDateStr]})
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

    @log_time_delta
    #@time_limit(15)
    def getOneDayHQdata(self, que, ts_date):
        #某天换手率
        df1 = pro.daily_basic(ts_code='', trade_date=ts_date)
        #某天日线数据
        df2 = pro.daily(trade_date=ts_date)
        #某天复权因子
        df3 = pro.adj_factor(ts_code='', trade_date=ts_date)
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
        #return df
        que.put((ts_date, df))
        logger.debug("download thread: put %s to queue",ts_date)
        return True

    @log_memory_usage
    def updateHQdataByDate(self):
        #启动save sqlite3线程
        self.enableQue = True
        t = threading.Thread(target=self.writeSqlThread, args=())
        t.setDaemon(True)   #非重要线程
        t.start()

        #TODO: can be added to deco
#        start = time.time()
#        memInfo = psutil.virtual_memory()
#        startMemUsage = psutil.Process(os.getpid()).memory_info().rss
        # TODO end
        #pro = ts.pro_api('03ccb16bb841e50fb10cdcdcc53bf6bd13fab450d4b8f872b66744d1')
        pub.sendMessage("pubMsg_DnldHQDataModel", msg="disableMenu")
        logger.debug("download data start now ......")
        #TODO: verify validation of start_date, end_date
        gaugeCounter = 0
        try:
            ts_dates=list(self.getDateStrListToDnld(self.start_date, self.end_date))
            #print(ts_dates)
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
        logger.debug("minDateStr = %s", self.readMinDateInAttr_t())
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
                        m = threading.Thread(target = self.getOneDayHQdata, args=(self.que, ts_date))
                        m.setDaemon(True)
                        m.start()
                        
                        m.join(timeout = 25)        #wait for 25s, then skip
                        gaugeCounter += gaugeStep*3

                else:
                    #(self.HQonoff==0):        #stop
                    self.enableQue=False
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
        #t.join()
        # wait for queue is empty, then sqlite3 can be accessed
        while (not self.que.empty()):
            pass
        self.enableQue = False
        self.updateMaxDateInDB(self.getMaxDateInDB())
#        logger.debug("Time used: %.2fs. Download %d days data",(time.time()-start), len(ts_dates))
#        endMemUsage = psutil.Process(os.getpid()).memory_info().rss
#        logger.info("memory usage: start=%sKB, end=%sKB, diff = %sKB", format(startMemUsage/1000,',.0f'),\
#                                 format(endMemUsage/1000,',.0f'), format((endMemUsage-startMemUsage)/1000,',.0f'))
#        gc.collect()      
        pub.sendMessage("pubMsg_DnldHQDataModel", msg="endHQupdate")
        
        return True
    def writeSqlThread(self):
        print("writeSqlThread start...")
        que = self.que
        while self.enableQue:
            if (not que.empty()):
                data = que.get()
                if (data[0] =="cmd"):
                    self.engine.execute(data[1])
                else:
                    df = data[1]
                    #print(df.head(2))
                    #df.to_sql("%s"%self.tablenm_hqall,self.engine, if_exists='append',index=False)
                    df.to_sql("%s"%self.tablenm_rawdata, self.engine, if_exists='append',index=False)
                    logger.debug("sqlite3 thread: write %s to database",data[0])
                #que
            #time.sleep(0.2)
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
    

            
    def getDateStrListToDnld(self, sDateStr, eDateStr):
        holidays = ['20181005', '20181004', '20181003', '20181002', '20181001', \
                         '20180924', '20180618', '20180501', '20180430', '20180406', \
                         '20180405', '20180221', '20180220', '20180219', '20180216', \
                         '20180215', '20180105', '20180104', '20180103', '20180101', \
                         '20171006', '20171005', '20171004', '20171003', '20171002', \
                         '20170530', '20170529', '20170501', '20170404', '20170403', \
                         '20170202', '20170201', '20170131', '20170130', '20170127', \
                         '20170102']

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
        
        if (self.checkTableExists(self.tablenm_hqall)):
            # get sqlite3 time in str
            cmd = "SELECT trade_date FROM %s where ts_code = '000001.SZ'"%(self.tablenm_hqall)            #all codes in 1 table
            try:
                df=pd.read_sql_query(cmd, self.engine)
            except Exception as e:
                #7. No data in dB
                logger.debug("getDateStrListToDnld read database error: %s",e)
                # blank database
                df=pd.DataFrame(columns=['trade_date'])
        else:
            df=pd.DataFrame(columns=['trade_date'])
        # get existed dates, in string list.
        storedDateStrList = list(df.trade_date.values)

        #rawdata_t
        if self.checkTableExists(self.tablenm_rawdata):
            cmd = "SELECT trade_date FROM %s where ts_code = '000001.SZ'"%(self.tablenm_rawdata)            #all codes in 1 table
            df=pd.read_sql_query(cmd, self.engine)
            rawdataDateStrList = list(df.trade_date.values)
            storedDateStrList.extend(rawdataDateStrList)
        storedDateStrList.extend(holidays)          #add holiday to storedDates
        # remove the dates that existed in database, in iteration
        datesStrIter = filter(lambda x: x not in storedDateStrList, datesIter)  #remove weekend
        #datesStrIter = filter(lambda x: x not in holidays, datesStrIter)        #remove holiday
        
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

    def isWeekDay(self, str_time):
        date = datetime.strptime(str_time, "%Y%m%d")
        return date.isoweekday()
    def generate_codes_csv(self, filename, maxcounter=5):
        assert(isinstance(filename, str))
        assert(isinstance(maxcounter, int))
        repeat_counter = 0
        ret = False
        while True:
            try:
                repeat_counter +=1
                data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,fullname,enname, market, exchange, curr_type, list_status, list_date, delist_date, is_hs')
                # success
                logger.debug("pro.stock_basic success! save to stock_basic.csv")

                data.to_csv(filename, index=False)
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
        self.cvrStartDate = "20161010"
        self.cvrEndDate = "20181110"
        super(CVRatioModel, self).__init__("pubMsg_CVRatioModel", 'hfq')
        self.cvrDays = 5
        self.preCond = self.getInitPreCondData()
        self.cond = self.getInitCondData()
        self.cvrThreshold=80
        self.cvrEndCond=self.getInitEndCondData()
        self.cvrEndDayRange = 100
        self.cvrEndDays=5
        self.runCvrAllowed = True
        self.gauagecounter=0
        self.cvrDisplayDay = 120
        
        
    def getInitPreCondData(self):
        return {'Cbx':True, "MAdir":u'高于', "MAdays":'30', "DiffDir":u'至少', "DiffValue":'10'}

    def getInitCondData(self):
        return {'1': {'Cbx':True, "MAdir":u'高于', "MAdays":'5', "DiffDir":u'至少', "DiffValue":'10'},
                    '2': {'Cbx':True, "MAdir":u'高于', "MAdays":'20', "DiffDir":u'至少', "DiffValue":'10'},
                    '3': {'Cbx':False, "MAdir":u'高于', "MAdays":'60', "DiffDir":u'至少', "DiffValue":'10'},
                    '4': {'Cbx':False, "MAdir":u'高于', "MAdays":'60', "DiffDir":u'至少', "DiffValue":'10'},
                    '5': {'Cbx':False, "MAdir":u'高于', "MAdays":'60', "DiffDir":u'至少', "DiffValue":'10'},
                    '6': {'Cbx':False, "MAdir":u'高于', "MAdays":'60', "DiffDir":u'至少', "DiffValue":'10'} }

    def getInitEndCondData(self):
        return {'Cbx':True, "MAdir":u'高于', "MAdays":'60', "DiffDir":u'至少', "DiffValue":'10'}
    
    def addMAvaluesToDF(self, df):
        MAdays = self.getMAdaysList()
        for maday in set(MAdays):
            logger.debug("maday is %s", maday)
            #df['ma%s'%maday] = df.groupby(df['ts_code']).rolling(maday).weighted_close.mean()
            df['ma%s'%maday]= df.groupby('ts_code')['weighted_close'].apply(lambda x: x.rolling(maday).mean())
    def cleanDFbyPreCond(self,df):
        if (self.preCond['Cbx']==True):
            preMAday = int(self.preCond["MAdays"])
            preDiffValue = float(self.preCond["DiffValue"])/100
            cvrDays = int(self.cvrDays)
            df['pre']=(df['weighted_close']-df['ma%s'%preMAday]*(1+preDiffValue))>0
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
            #df['end']= df.groupby('ts_code')['weighted_close'].apply(lambda x: x.rolling(cvrEndMAdays).mean())
            df['end']=(df['weighted_close']-df['ma%s'%cvrEndMAdays]*(1-cvrEndDiffValue))<0
            #移动和
            df['end']= df.groupby(['ts_code'])['end'].apply(lambda x: x.rolling(cvrEndDays).sum())
            #收盘价连续大于MA20 5天
            df['end']=(df['end']>=cvrEndDays)
            #将首次满足终止条件后的每一天都标注True
            df['end']= df.groupby(df['ts_code'])['end'].apply(lambda x: x.cumsum())
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
                #df['cond']= df.groupby('ts_code')['weighted_close'].apply(lambda x: x.rolling(MAdays).mean())
                #选择weighted_close > 移动平均
                df['cond']=(df['weighted_close']-df['ma%s'%MAdays]*(1+DiffValue))>0
                #df['cond'].to_csv(r'data/cond.csv', index=False)
                #df['condFlag'].to_csv(r'data/condFlag.csv', index=False)
                df['condFlag'] = df['condFlag'] & df['cond']
                #df['condFlag'].to_csv(r'data/condFlag_rlt.csv', index=False)
        #求移动和(连续M天True)
        df['condFlag']= df.groupby(df['ts_code'])['condFlag'].apply(lambda x: x.rolling(MAdays).sum())
        df['condFlag']=df['condFlag']>=cvrDays
        #将满足连续"M天Cond"之后的日期都标记为True
        df['condFlag']= df.groupby(df['ts_code'])['condFlag'].apply(lambda x: x.cumsum())
        df['condFlag'] = df['condFlag']>0
        #删除不满足条件的行
        df.drop(df.index[df['condFlag']==False], inplace=True)
    
    def startCVRcaculation(self,df):
        cvrThreshold = int(self.cvrThreshold )
        #量能开始
        #rslt = pd.DataFrame(index=df.groupby('ts_code', as_index=False).first().index)
        rslt = df.groupby(df['ts_code'], as_index=False)['trade_date'].first()
        #1st CV, start date 
        #rslt = pd.merge(rslt,dfCodeDate,how='inner', on=['ts_code'])
        #量能结束        
        df['cv']= df.groupby(df['ts_code'])['turnover_rate'].apply(lambda x: x.cumsum())
        df['cvflag']=df['cv']>=cvrThreshold
        #df_reserved = df[df['cvflag']==False].copy()       #not used, drop
        df.drop(df.index[df['cvflag']==False], inplace=True)
        #dfCodeDateCV = df.groupby('ts_code')['trade_date', 'cv'].first()
        dfCodeDateCV = df.groupby(df['ts_code'], as_index=False)['trade_date', 'cv'].first()
        #print(dfCodeDateCV)
        #第一次量能筛选结果, how=inner, start date is del if end data not exist
        # 1st CV: startdate, end date, cv
        rslt = pd.merge(rslt,dfCodeDateCV,how='inner', on=['ts_code'], left_index=True)
        return rslt
    def getMAdaysList(self):
        MAdays = []
        if (self.preCond["Cbx"]==True):
            MAdays.append(int(self.preCond['MAdays']))
        if (self.cvrEndCond["Cbx"]==True):
            MAdays.append(int(self.cvrEndCond['MAdays']))
        for idx in self.cond:
            if(self.cond[idx]['Cbx']==True):
                MAdays.append(int(self.cond[idx]['MAdays']))
        return MAdays
    def getDataFromDB(self):
        MAdays = self.getMAdaysList()
        startDate = self.get_startdate_byworkday(self.cvrStartDate,max(MAdays))
        dateRange = (startDate, self.cvrEndDate)
        logger.debug(dateRange)
        cmd="SELECT trade_date,ts_code, weighted_close, turnover_rate FROM hqall_t where trade_date BETWEEN ? AND ?"
        df=pd.read_sql_query(cmd, self.engine, params = dateRange)
        logger.debug("the len of df is:  %d",  len(df))
        self.gauagecounter += 12
        pub.sendMessage("pubMsg_CVRatioModel", msg=("updateGaugeCounter", self.gauagecounter))
        return df

    def getDataFromTables(self):
        MAdays = self.getMAdaysList()
        startDate = self.get_startdate_byworkday(self.cvrStartDate,max(MAdays))
        dateRange = (startDate, self.cvrEndDate)
        targetColnm = "turnover_rate"
        
        df1 = self.readDataFromTableForCVR('hqall_t', targetColnm, dateRange)
        logger.debug("the len of df1 in hqall_t is:  %d",  len(df1))
        df2 = self.readDataFromTableForCVR('rawdata_t', targetColnm, dateRange)
        logger.debug("the len of df2 in rawdata_t is:  %d",  len(df2))
        df = pd.concat([df1, df2], ignore_index=True, sort = False)
        logger.debug("the len of df is:  %d",  len(df))
        self.gauagecounter += 12
        pub.sendMessage("pubMsg_CVRatioModel", msg=("updateGaugeCounter", self.gauagecounter))
        return df

    def readDataFromTableForCVR(self, tablenm, targetColnm, dateRange):
        #MAdays = self.getMAdaysList()
        #startDate = self.get_startdate_byworkday(self.cvrStartDate,max(MAdays))
        #dateRange = (startDate, self.cvrEndDate)
        #targetColnm = "turnover_rate"
        if self.checkTableExists(tablenm):
            cmd="SELECT trade_date,ts_code, weighted_close, %s FROM %s where trade_date BETWEEN ? AND ?"%(targetColnm, tablenm)
            try:
                df=pd.read_sql_query(cmd, self.engine, params = dateRange)
            except Exception as e:
                logger.debug("%s",e)
                df = pd.DataFrame()
            return df
        else:
            return pd.DataFrame()
    
    @log_memory_usage
    def calcCVR(self):
        #时间 内存统计
#        begintime = time.time()
#        memInfo = psutil.virtual_memory()
#        startMemUsage = psutil.Process(os.getpid()).memory_info().rss

        starttime = time.time()
        self.gauagecounter = 5
        # start, init gauge
        pub.sendMessage("pubMsg_CVRatioModel", msg=("startCVRBtn", None))   #set panel off, start gauge
        pub.sendMessage("pubMsg_CVRatioModel", msg=("updateGaugeCounter", self.gauagecounter))
        #1. data init. outside the loop.
            #a. read all data from database, and sort by date
            #b. calc all MA values
        preMAday = int(self.preCond["MAdays"])
        preDiffValue = float(self.preCond["DiffValue"])/100
        cvrDays = int(self.cvrDays)
        
        #dateRange = (self.cvrStartDate, self.cvrEndDate)
        #cmd="SELECT trade_date,ts_code, weighted_close, turnover_rate FROM hqall_t where trade_date BETWEEN ? AND ?"
        #df=pd.read_sql_query(cmd, self.engine, params = dateRange)
        #logger.debug("the len of df is:  %d",  len(df))
        #self.gauagecounter += 12
        #pub.sendMessage("pubMsg_CVRatioModel", msg=("updateGaugeCounter", self.gauagecounter))
        
        #df = self.getDataFromDB()
        df = self.getDataFromTables()
        logger.debug("pd.read_sql_query: %s",  "%.2f"%(time.time()-starttime))
        starttime = time.time()

        #对时间排序
        df = df.sort_values(by='trade_date', ascending=True)
        self.gauagecounter += 7
        pub.sendMessage("pubMsg_CVRatioModel", msg=("updateGaugeCounter", self.gauagecounter))
        logger.debug("df.sort_values: %s",  "%.2f"%(time.time()-starttime))
        starttime = time.time()

        #添加所有移动平均到DataFrame
        self.addMAvaluesToDF(df)
        self.gauagecounter += 40
        pub.sendMessage("pubMsg_CVRatioModel", msg=("updateGaugeCounter", self.gauagecounter))
        logger.debug("addMAvaluesToDF: %s",  "%.2f"%(time.time()-starttime))
        starttime = time.time()

        #init 'condflag' column to True
        df['condFlag']=True
        #初始化最终结果
        finalRslt = pd.DataFrame()
        #满足量能次数
        cvrRltIdx=0
        while (not df.empty):
            cvrRltIdx+=1
            #df = df.sort_values(by='trade_date', ascending=True)

            logger.debug("df.sort_values: %s",  "%.2f"%(time.time()-starttime))
            starttime = time.time()

            #2. 1st loop, calc preCond, 
            self.cleanDFbyPreCond(df)
            if (cvrRltIdx==1):
                self.gauagecounter += 12
                pub.sendMessage("pubMsg_CVRatioModel", msg=("updateGaugeCounter", self.gauagecounter))
            logger.debug("cleanDFbyPreCond: %s",  "%.2f"%(time.time()-starttime))
            starttime = time.time()

            df_tailed = self.popDFbyEndCond(df)
            if (cvrRltIdx==1):
                self.gauagecounter += 10
                pub.sendMessage("pubMsg_CVRatioModel", msg=("updateGaugeCounter", self.gauagecounter))

            logger.debug("popDFbyEndCond: %s",  "%.2f"%(time.time()-starttime))
            starttime = time.time()

            #3. 2nd loop the "cond1-cond7", calc cond
            self.dropDFbyCond(df)
            
            logger.debug("dropDFbyCond: %s",  "%.2f"%(time.time()-starttime))
            starttime = time.time()

            #4. start caculation CV
            rslt = self.startCVRcaculation(df)
            #第4列转换为字符串: format函数
            rslt.iloc[:,3] = rslt.iloc[:,3].apply(lambda x: format(x,'.4f'))
            logger.debug("startCVRcaculation: %s",  "%.2f"%(time.time()-starttime))
            starttime = time.time()

            #最终结果
            if (not rslt.empty):
#                print("show cvrRltIdx result:")
#                print(rslt)
                #rslt.to_csv('rslt_%s.csv'%cvrRltIdx, index=False)
                #rslt.columns = ['ts_code',u'第%s次开始'%cvrRltIdx, u'第%s次结束'%cvrRltIdx, u'第%s次量能'%cvrRltIdx]
                if finalRslt.empty==True:
                    finalRslt = rslt.copy()
                else:
                    finalRslt = pd.merge(finalRslt,rslt,how='outer', on=['ts_code'])    #how='inner', 'left'
            logger.debug("length of df is %d, before attend", len(df))
            #将满足退出条件的数据恢复，重新循环计算CVR
            if (not df_tailed.empty):
                df = df.append(df_tailed, sort=False)
            logger.debug("length of df is %d, after attend", len(df))
            logger.debug("finalRslt: %s",  "%.2f"%(time.time()-starttime))
            starttime = time.time()        
        
        self.gauagecounter += 10
        pub.sendMessage("pubMsg_CVRatioModel", msg=("updateGaugeCounter", self.gauagecounter))
        # 转换格式，把第N次满足条件的数据向左对七
        finalRslt = self.adjustStyleOfCVRoutput(finalRslt)
        #删除表格的NaN值
        finalRslt.fillna('', inplace= True)
        finalRslt.to_csv(r'data/finalRslt.csv', index=False, encoding='utf_8_sig')
        pub.sendMessage("pubMsg_CVRatioModel", msg=("endCVRBtn", finalRslt))
        logger.debug("Caculation for %s is finished!",'CVR')

    def adjustStyleOfCVRoutput(self, df):
        """调整CVR输出格式，左对齐"""
        #1.将所有列合并成一行字符串，用逗号隔开
        df = df.apply(lambda x: x.str.cat(sep=','), axis=1).to_frame()
        #2. 列名
        df.columns = ['all']
        #3. 根据逗号分成不同的列，左对齐
        df = df['all'].apply(lambda x: pd.Series(x.split(',')))
        colnms = ['ts_code']
        #4. 生成列名
        for i in range((len(df.columns)-1)//3):
            colnms.append('第%s次开始'%(i+1))
            colnms.append('第%s次结束'%(i+1))
            colnms.append('第%s次量能'%(i+1))
        df.columns = colnms
        return df
    def sortExistedRPSdata(self, para):
        df=para[0]
        colname = para[1]
        direction = para[2]
        df = df.sort_values(by=colname, ascending=direction)
        pub.sendMessage("pubMsg_CVRatioModel", msg=("end_getDataByCode", df))
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

#cmd="SELECT * FROM hqall_t WHERE trade_date BETWEEN 20180810 AND 20180820"
params = ('20160810', '20180820')
cmd="SELECT * FROM hqall_t WHERE trade_date BETWEEN ? AND ?"
#cmd="SELECT * FROM hqall_t WHERE trade_date BETWEEN ? AND ? ORDER BY trade_date ASC"
df=pd.read_sql_query(cmd, engine, params=params)


#建立index
cmd = "CREATE INDEX date ON hqall_t (trade_date)"
cmd = "CREATE INDEX code ON hqall_t (ts_code)"
cmd = "DROP INDEX date"
cmd = "DROP INDEX code"
cmd = "DROP INDEX hqall_date_code"
cmd = "CREATE INDEX hqall_date_code ON hqall_t(trade_date,ts_code)"
engine.execute(cmd)

params1 = ('000001.SZ',)
cmd1="SELECT * FROM %s WHERE ts_code = ? "%"hqall_t"
df=pd.read_sql_query(cmd1, engine, params=params1)
df = df.sort_values(by='trade_date', ascending=True)


('ts_code','trade_date','open','high','low','close','vol','turnover_rate','turnover_rate_f','weighted_close')
params = ('ts_code', 'trade_date', '000001.SZ')
cmd="SELECT ?,? FROM %s WHERE ts_code = ? "%"hqall_t"

preMAday=30
preDiffValue=0.1
cvrDays = 5
maday=30
df['ma%s'%maday]= df.groupby('ts_code')['weighted_close'].apply(lambda x: x.rolling(maday).mean())

#修改字段名称
cmd = "ALTER TABLE hfq_hqData.db.pct_change RENAME TO pct_chg"

插入数据：
INSERT INTO [表名] (字段1,字段2) VALUES (100,\'51WINDOWS.NET\')

更新数据：
UPDATE [表名] SET [字段1] = 200,[字段2] = \'51WINDOWS.NET\' WHERE [字段三] = \'HAIWA\'

修改字段：
ALTER TABLE [表名] ALTER COLUMN [字段名] NVARCHAR (50) NULL

param
cmd = ""

for table in pd.read_sql_table('hqall_t', engine, chunksize=10000):
    df = pd.read_sql_table(table,engine)
#读取rps20字段为空白
cmd = "select * from hqall_t where rps20 is null and ts_code = '000001.SZ'"
cmd = "select * from hqall_t where rps20 is null and ts_code = '000001.SZ'"
df=pd.read_sql_query(cmd, engine)

cmd = "SELECT MAX(trade_date) FROM hqall_t WHERE ts_code='000001.SZ'"

dates = pro.trade_cal(exchange='', start_date='20100101', end_date='20181231')
pd.io.sql.to_sql(dates, 'tradedatesflag_t', engine, if_exists='replace',index=False, chunksize= 10000)

cmd = "SELECT * from hqall_t limit 10, 1"
cmd = "SELECT * from hqall_t group by ts_code order by trade_date ASC limit 10, 1"
cmd = "select * from hqall_t group by trade_date where trade_date = '20181129'"


cmd = "select * from hqall_t"
df1=pd.read_sql_query(cmd, engine)
len(df1)

cmd = "select * from rawdata_t"
df2=pd.read_sql_query(cmd, engine)
len(df2

df = pd.concat([df1, df2], ignore_index=True, sort = False)
df = df.groupby(df['ts_code'], as_index =False).apply(lambda x: x.sort_values(by='trade_date', ascending=False))
df[pct_nm]= (df.groupby(df['ts_code'])['weighted_close'].apply(lambda x: x.pct_change(-rpsN))).round(4)
df[rps_nm] = (df.groupby(df['trade_date'])[pct_nm].apply(lambda x: x.rank(pct=True))*100).round(1)
a = ['trade_date', 'ts_code', 'rps20, rps50, rps']
df3 = pd.merge(df2,df[a],how='inner', on = ['trade_date', 'ts_code'])


pd.io.sql.to_sql(df3, 'hqall_t', engine, if_exists='append',index=False, chunksize= 10000)

df1 = pd.read_csv('rslt_1.csv', dtype='str')
df2 = pd.read_csv('rslt_2.csv', dtype='str')
df3 = pd.read_csv('rslt_3.csv', dtype='str')
df = pd.merge(df1, df2, how='outer', on=['ts_code'])
df = pd.merge(df, df3, how='outer', on=['ts_code'])
df.fillna('', inplace= True)
df = df[df.notna()].astype('str')
df = df.apply(lambda x: x.str.cat(sep=','), axis=1).to_frame()
df.columns = ['all']
df = df['all'].apply(lambda x: pd.Series(x.split(',')))
colnms = ['ts_code']
for i in range((len(df.columns)-1)//3):
    colnms.append('第%s次开始'%(i+1))
    colnms.append('第%s次结束'%(i+1))
    colnms.append('第%s次量能'%(i+1))
df.columns = colnms

df = df['trade_date_x_x, '].apply(lambda x: pd.Series(x.split(',')))

df['all'] = 
df = df['City, State, Country'].apply(lambda x: pd.Series(x.split(',')))        
df['']    

'''