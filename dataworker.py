# !/usr/bin/env python
'''This is the wxPython for stock quant
stock_quant.py
add model to 'updateData'
add threading.event to 'stop' button
'''

import sys
import os
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


import pandas as pd
from pandas import Series, DataFrame

#to draw K-line
import mpl_finance as mpf
from matplotlib.pylab import date2num
import matplotlib.pyplot as plt
import matplotlib  


   
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
api = ts.pro_api('ded43ecfd7bc26fa6938e63d9578d44d00fba560859a900654b46687')
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


G_NUM_OF_CODES = 3      #3625
from viewer import logger
class Sqlite3Handler(object):
    def __init__(self, autype='qfq'):
        self.autypeStr = autype
        self.set_DBname_and_autype(self.autypeStr)
        self.hq_codes = self.get_codes()
        self.tablenm_hqall='hqall_t'

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
    
    def get_codes(self,table_nm=None):
        codes = []
        if (table_nm==None):
            #table_nm = datetime.now().strftime("%Y-%m-%d")
            table_nm = "codes_t"
        sqlcmd_get_codes = "SELECT code FROM '%s'"%table_nm
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
        # 1. check if 'codes_t' exists
        cmd = "select count(*)  from sqlite_master where type='table' and name = '%s'"%'codes_t'
        if ((self.engine.execute(cmd).fetchall()[0][0])==0):
            # 2. 'codes_t' not exists, check if 'codes_table.csv' exists. Try to generate 'codes_t' from 'codes_table.csv'
            # 2.1 check if 'codes_table.csv' exists, generate one if not using get_today_all()
            if (not os.path.isfile('codes_table.csv')):
                #generate 'codes_table.csv' using get_today_all()
                self.generate_codes_csv('codes_table.csv', 5)
            # 2.2 check if 'codes_table.csv' exists, generate 'codes_t' in DB if exists, raise an error if not.
            if (os.path.isfile('codes_table.csv')):
                # generate 'codes_t' from 'codes_table.csv'
                codes_df = pd.read_csv('codes_table.csv', dtype='str',names=['id','code'])
                try:
                    codes_df["code"].to_sql('codes_t', self.engine)
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
        self.start_date = datetime.now().strftime("%Y-%m-%d")
        self.rpsNChoices=['120', '240']
        self.rpsMktChoices = [u'全部', u'深市', u'沪市', u'创业板' ]
        self.rpsRangeChoices = [u'全部', u'一年以上']
        self.rpsN = 240
        self.rpsMktIdx = 0
        self.rpsRangeIdx = 0
        #self.autype='qfq'
        super(DnldHQDataModel, self).__init__('qfq')
        

class DnldHQDataModel(Sqlite3Handler):
    def __init__(self):
        self.sql_filename_base = 'hqData.db'
        self.sql_filename = self.sql_filename_base
        self.date_tail = '00:00:00.000000'
        self.start_date='2018-10-15'
        self.end_date = datetime.now().strftime("%Y-%m-%d")
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.days_num=''
        self.HQonoff=0      #default off
#        self.engine = create_engine('sqlite+pysqlite:///%s'%self.sql_filename, module=sqlite)
        #self.engine = create_engine('sqlite+pysqlite:///nfq_hqData.db', module=sqlite)
#        self.engine = create_engine('sqlite+pysqlite:///file.db', module=sqlite)
        super(DnldHQDataModel, self).__init__('qfq')
#        
#        self.autypeStr = 'qfq'
#        self.set_DBname_and_autype(self.autypeStr)
#        self.hq_codes = self.get_codes()
#        self.tablenm_hqall='hqall_t'

        pass
        
    
#    def set_DBname_and_autype(self, autypeStr):
#        if (autypeStr == 'nfq'):
#            self.autype=None
#            self.autypeStr='nfq'
#        elif (autypeStr == 'hfq'):
#            self.autype='hfq'
#            self.autypeStr='hfq'
#        elif (autypeStr == 'qfq'):
#            self.autype='qfq'
#            self.autypeStr='qfq'
#        self.sql_filename = autypeStr+'_'+self.sql_filename_base
#        self.engine = create_engine('sqlite+pysqlite:///%s'%self.sql_filename, module=sqlite)
#        self.initDB()
#        logger.debug("change to %s database and engine",self.sql_filename)
#        
#    def get_hist_k_data(self):
#        pass
#    #engine = create_engine("sqlite:///:memory:", echo=True)
#        f = ts.get_k_data('000673', '2018-10-08', '2018-10-17')
    
    def checkDateTableExist(self,date=None):
        if (date==None):
            date = datetime.now().strftime("%Y-%m-%d")
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
        startDate = datetime.strptime(startDateStr, "%Y-%m-%d")
        endDate = datetime.strptime(endDateStr, "%Y-%m-%d")
        startDays = startDate.isoweekday()
        if (startDays in [6,7]):
            newStartStr = (startDate+timedelta(days=(8-startDays))).strftime("%Y-%m-%d")
        else:
            newStartStr=startDateStr
        # endDays        
        endDays = endDate.isoweekday()
        if (endDays in [6,7]):
            newEndStr = (endDate+timedelta(days=(5-endDays))).strftime("%Y-%m-%d")
        else:
            newEndStr=endDateStr
        logger.debug("filtered date: [%s, %s]",newStartStr, newEndStr)
        return [newStartStr, newEndStr]

    def updateHQdata(self):
#        pub.sendMessage("update", msg="disableMenu")
        pub.sendMessage("pubMsg_DnldHQDataModel", msg="disableMenu")
        #TODO: verify validation of start_date, end_date
        i=0
        target_span=self.filter_date(self.start_date, self.end_date)
        for code in self.hq_codes:
            i+=1
  #          pub.sendMessage("update", msg=i)
            pub.sendMessage("pubMsg_DnldHQDataModel", msg=i)
            #logger.debug("gauge=%d",i)
            dateSpans=self.get_dateSpans(code, target_span)
            try:
                logger.debug("get %s hq data, start", code)
                print(dateSpans)
                for span in dateSpans:
                    if (self.HQonoff==1):
                        #TODO: use threading.event()?
                        if (self.autype == 'qfq'):
                            df = ts.get_h_data(code, start=span[0], end=span[1], retry_count=3, pause=5)
                        else:
                            df = ts.get_h_data(code, start=span[0], end=span[1], autype=self.autype, retry_count=3, pause=5)
#                        time.sleep(2)
                        #add a columen code
                        df['code']=code
                        print(df)
                        #df.to_sql("_%s"%code,self.engine, if_exists='append',index=True)
                        df.to_sql("%s"%self.tablenm_hqall,self.engine, if_exists='append',index=True)
                        logger.debug("write %s to DB",code)
                    else:
                        #(self.HQonoff==0):        #stop
#                        pub.sendMessage("update", msg="endHQupdate")        #clear gauage counter
                        pub.sendMessage("pubMsg_DnldHQDataModel", msg="endHQupdate")        #clear gauage counter
                        logger.info("updateHQdata() is stopped by Stop Button pressed, setting HQonoff 0")
                        return
                #delete duplicate line
                cmd_del = "delete from _%s where rowid not in(select max(rowid) from _%s group by date)"%(code,code)
                #self.engine.execute(cmd_del)
                #TODO: need to check, enable or disable below
            except OSError as e:
                #network issue
                logger.info(e)
                time.sleep(60)
            except Exception as e:
                logger.info(e)
            
            if (i>=G_NUM_OF_CODES):
#            if (i>=3):
                logger.info("updateHQdata() is finished, i=%d",i)
                break
 #       pub.sendMessage("update", msg="endHQupdate")            
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
    
    def get_dateSpans(self, code=None, target_span=None):
        dateSpans=[]
        if (target_span==None):
            start_date_menu = self.start_date
            end_date_menu = self.end_date
        else:
            start_date_menu = target_span[0]
            end_date_menu = target_span[1]
        logger.debug("start_date_menu = %s, end_date_menu=%s",start_date_menu, end_date_menu)
        try:
            # get sqlite3 time in str
#            cmd1 = "SELECT MIN(date) FROM _%s"%code                                                                    #1 code in 1 table
            cmd1 = "SELECT MIN(date) FROM %s where code = %s"%(self.tablenm_hqall, code)            #all codes in 1 table
            start_date_db= self.engine.execute(cmd1).fetchall()[0][0][:10]
            #days-1
            start_date_db = (datetime.strptime(start_date_db, "%Y-%m-%d")+timedelta(days=-1)).strftime("%Y-%m-%d")
            
#            cmd2 = "SELECT MAX(date) FROM _%s"%code
            cmd2 = "SELECT MAX(date) FROM %s where code = %s"%(self.tablenm_hqall, code)            #all codes in 1 table
            end_date_db= self.engine.execute(cmd2).fetchall()[0][0][:10]
            end_date_db = (datetime.strptime(end_date_db, "%Y-%m-%d")+timedelta(days=1)).strftime("%Y-%m-%d")
            #end_date_db = datetime.strptime(b, "%Y-%m-%d")
            logger.debug("start_date_db = %s, end_date_db=%s",start_date_db, end_date_db)
            
            if (end_date_menu<=start_date_db):
                #status 1:
                logger.debug("status 1")
                dateSpans.append([start_date_menu,end_date_menu])
            elif (start_date_menu>=end_date_db):
                # status 2, same as 1
                logger.debug("status 2")
                dateSpans.append([start_date_menu, end_date_menu])
            elif (start_date_menu<start_date_db)&(end_date_menu>start_date_db)&(end_date_menu<end_date_db):
                #status 5
                logger.debug("status 5")
                dateSpans.append([start_date_menu,start_date_db] )
            elif (start_date_db<=start_date_menu)&(start_date_menu<=end_date_db)&(end_date_db<=end_date_menu):
                #status 6
                logger.debug("status 6")
                dateSpans.append([end_date_db, end_date_menu])
            elif (start_date_db<=start_date_menu)&(end_date_menu<=end_date_db):
                #status 8
                logger.debug("status 8")
                pass
            elif (start_date_menu<=start_date_db)&(end_date_db<=end_date_menu):
                #status 9
                logger.debug("status 9")
                dateSpans.append([start_date_menu, start_date_db])
                dateSpans.append([end_date_db, end_date_menu])
        except Exception as e:
            #7. No data in dB
            logger.debug("status 9")
            dateSpans.append([start_date_menu, end_date_menu])
        
        # remove the day of week end
        filtered_dateSpans=[]
        for dateSpan in dateSpans:
            filteredSpan = self.filter_date(dateSpan[0], dateSpan[1])
            if filteredSpan[0]<=filteredSpan[1]:
                filtered_dateSpans.append(filteredSpan)
        
        return filtered_dateSpans
            
    def getTodayAllData(self):
        date = datetime.now().strftime("%Y-%m-%d")
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
            table_nm = datetime.now().strftime("%Y-%m-%d")
        df.to_sql(table_nm, self.engine)
        logger.info("success: write hq date at %s",table_nm)
        
#    def get_codes(self,table_nm=None):
#        codes = []
#        if (table_nm==None):
#            #table_nm = datetime.now().strftime("%Y-%m-%d")
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
        date = datetime.strptime(str_time, "%Y-%m-%d")
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
#    def initDB(self):
#        """Generate 'codes_t', which has all stock codes, into sqlite_db if there is no 'codes_t' in sqlite_db"""
#        # 1. check if 'codes_t' exists
#        cmd = "select count(*)  from sqlite_master where type='table' and name = '%s'"%'codes_t'
#        if ((self.engine.execute(cmd).fetchall()[0][0])==0):
#            # 2. 'codes_t' not exists, check if 'codes_table.csv' exists. Try to generate 'codes_t' from 'codes_table.csv'
#            # 2.1 check if 'codes_table.csv' exists, generate one if not using get_today_all()
#            if (not os.path.isfile('codes_table.csv')):
#                #generate 'codes_table.csv' using get_today_all()
#                self.generate_codes_csv('codes_table.csv', 5)
#            # 2.2 check if 'codes_table.csv' exists, generate 'codes_t' in DB if exists, raise an error if not.
#            if (os.path.isfile('codes_table.csv')):
#                # generate 'codes_t' from 'codes_table.csv'
#                codes_df = pd.read_csv('codes_table.csv', dtype='str',names=['id','code'])
#                try:
#                    codes_df["code"].to_sql('codes_t', self.engine)
#                except ValueError as e:
#                    logger.info(e)
#                except Exception as e:
#                    logger.info(e)
#            else: 
#                # raise an error, 'codes_table.csv' fails, try again
#                logger.error('fail to generate codes_table.csv, try again')
#                assert (1==0)
#    
#    def initCodeTable(self, flag='ifexist'):
##        date = datetime.now().strftime("%Y-%m-%d")
##        code_df = pd.DataFrame(r.fetchall(), columns=['code'])
#        cmd_get_codes = "SELECT code FROM codes_t"
#        try:
#            assert(flag=='ifnotexist')
#            r = self.engine.execute(cmd_get_codes)
#            # codes_t exists in engine, pass
#            pass
#        except Exception as e:
#            #force to init codes_t from csv
#            logger.debug(e)
#            logger.debug("engine does not have codes_t, init code_t from csv")
#            try:
#                code_df = pd.read_csv('codes_table.csv', dtype=object)
#                try:
#                    #code_df.to_csv('codes_table.csv')
#                    code_df["code"].to_sql('codes_t', self.engine)
#                except ValueError as e:
#                    logger.info("Exception: %s",e)
#                except Exception as e:
#                    logger.info("Exception: %s",e)
#            except Exception as e:
#                logger.error("codes_table.csv does not exist")
#        
#    
#    def saveCodes_fromCSV_toDB(self):
#        try:
#            codes_df = pd.read_csv('codes_table.csv', dtype='str')
#            try:
#                #code_df.to_csv('codes_table.csv')
#                codes_df["code"].to_sql('codes_t', self.engine)
#            except ValueError as e:
#                logger.info("Exception: %s",e)
#            except Exception as e:
#                logger.info("Exception: %s",e)
#        except Exception as e:
#            logger.error("codes_table.csv does not exist")
#        
#    def saveLatestCodes_tocsv(self):
#        date = datetime.now().strftime("%Y-%m-%d")
##        date = '2018-10-17'
#        sqlcmd_get_codes = "SELECT code FROM '%s'"%date
#        try:
#            r = self.engine.execute(sqlcmd_get_codes)
#            code_df = pd.DataFrame(r.fetchall(), columns=['code'])
#            code_df.to_csv('codes_table.csv')
#            logger.debug("codes saves to cdoes_table.csv")
##        except OperationalError as e:
##            logger.warning("read %s from %s error: %s", date, self.sql_filename, e)
#        except Exception as e:
#            logger.warning("read %s from %s error: %s", date, self.sql_filename, e)
    

        

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
'''