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
from sqlite3 import dbapi2 as sqlite
from sqlalchemy import create_engine
from sqlalchemy.dialects.sqlite import TIME, DATE, DATETIME
from sqlalchemy import create_engine, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy import MetaData, Sequence
from sqlalchemy.orm import sessionmaker, relationship




# creat log in trace.log
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
handler = logging.FileHandler('trace.log',mode='a')
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)

# create a logging in console
formatterconsole = logging.Formatter('%(message)s')
handlerconsole = logging.StreamHandler()
handlerconsole.setFormatter(formatterconsole)
handlerconsole.setLevel(logging.DEBUG)
# to reduce duplicate handler in using ipython
if logger.hasHandlers() is False:
    logger.addHandler(handler)
    logger.addHandler(handlerconsole)
#    logger.info("HasHandlers() is False, add two new handlers")
#else:
#    logger.info("HasHandlers() is True, previous handlers existed, don't add new ones")

# Global variable definition here

G_NUM_OF_CODES = 3      #3625

#sql_get_codes = "SELECT code FROM '%s'"

class TestThread(threading.Thread):
    def __init__(self):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.start()    # start the thread

    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread.
        for i in range(6):
            time.sleep(10)
            wx.CallAfter(self.postTime, i)
        time.sleep(5)
        wx.CallAfter(pub.sendMessage, "update", msg="Thread finished!")

    def postTime(self, amt):
        """
        Send time to GUI
        """
        amtOfTime = (amt + 1) * 10
        pub.sendMessage("update", msg=amtOfTime)


# Class definition here
class AbstractModel(object):
    def __init__(self):
        self.listeners = []
    def addListener(self, listenerFunc):
        self.listeners.append(listenerFunc)
    def removeListener(self, listenerFunc):
        self.listeners.remove(listenerFunc)
    def update(self):   #定义，子类找到父类方法，但self指向的是子类的实例，不是父类实例，也不是子类。
        for eachFunc in self.listeners:
            print(self)
            #在继承时，传入的是哪个实例，就是那个传入的实例，而不是指定义了self的类的实例
            eachFunc(self)  #这是调用，不是定义，self指向子类实例(frame.model)
class SimpleName(AbstractModel):
    def __init__(self, first="", last=""):
        AbstractModel.__init__(self)
        self.set(first, last)
    def set(self, first, last):
        self.first = first
        self.last = last
        self.update() #1 更新, 这是方法调用，不需要self作为参数，子类中没有update方法，向父类寻找

#class SimpleDBName(AbstractModel):
#    def __init__(self, dbName=""):
#        AbstractModel.__init__(self)
#        self.set(dbName)
#    def set(self, dbName):
#        self.dbName = dbName
#        self.update() #1 更新, 这是方法调用，不需要self作为参数，子类中没有update方法，向父类寻找

class HqDataHandler():
    def __init__(self,menu):
#        threading.Thread.__init__(self)
#        self.start()    # start the thread

        self.menu = menu
        self.sql_filename_base = 'hqData.db'
        self.sql_filename = self.sql_filename_base
        self.date_tail = '00:00:00.000000'
        self.start_date='2018-10-15'
        self.end_date = datetime.now().strftime("%Y-%m-%d")
        self.current_date = datetime.now().strftime("%Y-%m-%d")
#        self.engine = create_engine('sqlite+pysqlite:///%s'%self.sql_filename, module=sqlite)
        #self.engine = create_engine('sqlite+pysqlite:///nfq_hqData.db', module=sqlite)
#        self.engine = create_engine('sqlite+pysqlite:///file.db', module=sqlite)
        self.update_DB_and_autype()
        #self.initDB()
        self.hq_codes = self.get_codes()
        self.tablenm_hqall='hqall_t'
        pass
        
    
    def update_DB_and_autype(self):
        if (self.menu.autypeStr == 'nfq'):
            self.autype=None
        elif (self.menu.autypeStr == 'hfq'):
            self.autype='hfq'
        elif (self.menu.autypeStr == 'qfq'):
            self.autype='qfq'
        self.sql_filename = self.menu.autypeStr+'_'+self.sql_filename_base
        self.engine = create_engine('sqlite+pysqlite:///%s'%self.sql_filename, module=sqlite)
        self.initDB()
        logger.debug("change to %s database and engine",self.sql_filename)
        
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
        logger.debug("filtered menu date: [%s, %s]",newStartStr, newEndStr)
        return [newStartStr, newEndStr]

    def updateHQdata(self):
        pub.sendMessage("update", msg="disableMenu")
        #TODO: verify validation of start_date, end_date
        i=0
        target_span=self.filter_date(self.menu.start_date, self.menu.end_date)
        for code in self.hq_codes:
            i+=1
            pub.sendMessage("update", msg=i)
            #logger.debug("gauge=%d",i)
            dateSpans=self.get_dateSpans(code, target_span)
            try:
                logger.debug("get %s hq data, start", code)
                print(dateSpans)
                for span in dateSpans:
                    if (self.menu.HQonoff==1):
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
                        #(self.menu.HQonoff==0):        #stop
                        pub.sendMessage("update", msg="endHQupdate")        #clear gauage counter
                        logger.info("updateHQdata() is stopped by setting HQonoff 1")
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
                pub.sendMessage("update", msg="endHQupdate")
                break
        pub.sendMessage("update", msg="endHQupdate")            
            
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
            start_date_menu = self.menu.start_date
            end_date_menu = self.menu.end_date
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
        for i in r:
            codes.append(list(i)[0])
        #print(codes)
        return codes
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
    
    def initCodeTable(self, flag='ifexist'):
#        date = datetime.now().strftime("%Y-%m-%d")
#        code_df = pd.DataFrame(r.fetchall(), columns=['code'])
        cmd_get_codes = "SELECT code FROM codes_t"
        try:
            assert(flag=='ifnotexist')
            r = self.engine.execute(cmd_get_codes)
            # codes_t exists in engine, pass
            pass
        except Exception as e:
            #force to init codes_t from csv
            logger.debug(e)
            logger.debug("engine does not have codes_t, init code_t from csv")
            try:
                code_df = pd.read_csv('codes_table.csv', dtype=object)
                try:
                    #code_df.to_csv('codes_table.csv')
                    code_df["code"].to_sql('codes_t', self.engine)
                except ValueError as e:
                    logger.info("Exception: %s",e)
                except Exception as e:
                    logger.info("Exception: %s",e)
            except Exception as e:
                logger.error("codes_table.csv does not exist")
        
    
    def saveCodes_fromCSV_toDB(self):
        try:
            codes_df = pd.read_csv('codes_table.csv', dtype='str')
            try:
                #code_df.to_csv('codes_table.csv')
                codes_df["code"].to_sql('codes_t', self.engine)
            except ValueError as e:
                logger.info("Exception: %s",e)
            except Exception as e:
                logger.info("Exception: %s",e)
        except Exception as e:
            logger.error("codes_table.csv does not exist")
        
    def saveLatestCodes_tocsv(self):
        date = datetime.now().strftime("%Y-%m-%d")
#        date = '2018-10-17'
        sqlcmd_get_codes = "SELECT code FROM '%s'"%date
        try:
            r = self.engine.execute(sqlcmd_get_codes)
            code_df = pd.DataFrame(r.fetchall(), columns=['code'])
            code_df.to_csv('codes_table.csv')
            logger.debug("codes saves to cdoes_table.csv")
#        except OperationalError as e:
#            logger.warning("read %s from %s error: %s", date, self.sql_filename, e)
        except Exception as e:
            logger.warning("read %s from %s error: %s", date, self.sql_filename, e)
    

import wx
import os
#import hqdata
from datetime import datetime,timedelta
import threading
from wx.lib.pubsub import pub
import wx.adv
from wx.lib.splitter import MultiSplitterWindow

class PageOne(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "This is a PageOne object", (20,20), style=wx.ST_NO_AUTORESIZE)
class LeftPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.choiceList = [u'偏离', u'低于', u'高于']
        self.pickList = [u'至多',u'至少']
        self.daysAveList = ['5', '20','30','60','120','240']
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        #筛选条件
        sizer = self.buildChooseCondBar()
        mainsizer.Add(sizer,0, wx.EXPAND)
        mainsizer.AddSpacer(10)
        #均价关系
        sizer = self.buildAveRelationBars()
        mainsizer.Add(sizer,0, wx.EXPAND)
        mainsizer.AddSpacer(10)
        #量能标准
        sizer = self.createAmtErgBars()
        mainsizer.Add(sizer,0, wx.EXPAND)
        mainsizer.AddSpacer(10)
        #终止条件
        staticsizer = self.buildEndCondBar()
        mainsizer.Add(staticsizer,0, wx.EXPAND)
        mainsizer.AddSpacer(10)
        #启动按钮
        button = wx.Button(self, -1, label=u"开始量能筛选")
        self.Bind(wx.EVT_BUTTON, self.Evt_Startup, button)
        mainsizer.Add(button)
        
        self.SetBackgroundColour("white")
        self.SetSizerAndFit(mainsizer)
        self.SetSizer(mainsizer)
#        mainsizer.Fit(self)
        self.Fit()
        self.Show()
    
    def buildChooseCondData(self):
        return ((u"开始日期", "2018-10-25",self.EvtDatePick),
                    (u"截止日期", "2018-10-31",self.EvtDatePick))
    def buildChooseCondDate(self):
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        for chooseCondDateItem in self.buildChooseCondData():
            self.buildOneChooseCondDate(hSizer, chooseCondDateItem)
        return hSizer
    def buildOneChooseCondDate(self, sizer, chooseCondDateItem):
        for label, value, eHandler in [chooseCondDateItem]:
            text = wx.StaticText(self, label=label, style=wx.ALIGN_CENTER)
            sizer.Add(text, 0, wx.ALL, 2)
            datepicker = wx.adv.DatePickerCtrl(self, size=(100,-1), style = wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY)
#            datepicker = wx.adv.DatePickerCtrl(self, size=(100,-1), style = wx.adv.DP_DEFAULT)
            self.Bind(wx.adv.EVT_DATE_CHANGED, self.EvtStartDate, datepicker)
            sizer.Add(datepicker, 0, wx.ALL, 2)
    def buildChooseCondPriceData(self):
        return ((u'收盘价', 2, self.choiceList, self.EvtCombo1Box, 5, self.EvtCombo1Box),
                    (u'日均价', 1, self.pickList, self.EvtCombo1Box, '0', self.EvtCondText),
                    )
    def buildOneChooseCondPrice(self, sizer, chooseCondPriceItem):
        for label, cmbxIdx1, choices, eHandler1,cmbxIdx2,eHandler2 in [chooseCondPriceItem]:
            text = wx.StaticText(self, label=label)
            sizer.Add(text, 0, wx.ALL, 2)
            cmbx = wx.ComboBox(self, size=(50, -1), choices=choices, value=choices[cmbxIdx1],style=wx.CB_DROPDOWN|wx.CB_READONLY)
            self.Bind(wx.EVT_COMBOBOX, eHandler1, cmbx)
            sizer.Add(cmbx, 0, wx.ALL, 2)
            if isinstance(cmbxIdx2,str):
                #textctrl
                obj = wx.SpinCtrl(self, size=(50,-1))
                obj.SetRange(1,100)
                obj.SetValue(int(cmbxIdx2))
                self.Bind(wx.EVT_TEXT, eHandler2, obj)
            else:
                #combox
                obj = wx.ComboBox(self, size=(50, -1), choices=self.daysAveList, value=self.daysAveList[cmbxIdx2],style=wx.CB_DROPDOWN)
            sizer.Add(obj, 0, wx.ALL, 2)
            
    def buildChooseCondPriceBar(self):
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        cbx = wx.CheckBox(self, label=u"筛选条件")
        hSizer.Add(cbx,0,wx.ALL, 2)
        for chooseCondPriceItem in self.buildChooseCondPriceData():
            self.buildOneChooseCondPrice(hSizer,chooseCondPriceItem)
        text = wx.StaticText(self, label='%', style=wx.ALIGN_CENTER)
        hSizer.Add(text, 0, wx.ALL, 2)
        return hSizer
    def buildChooseCondBar(self):
        box = wx.StaticBox(self, -1, u"筛选条件")
        staticsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        #row1
        sizer1 = self.buildChooseCondDate()
        #row2
        sizer2 = self.buildChooseCondPriceBar()
        staticsizer.Add(sizer1, 0, wx.ALL, 2)
        staticsizer.Add(sizer2, 0, wx.ALL, 2)
        
        return staticsizer
    
    def buildEndCondBar(self):
        box = wx.StaticBox(self, -1, u"终止条件")
        staticsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        #ROW1
        sizer1 = self.buildOneEndPrice()
        #ROW2
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        for endCondItem in self.creatEndCondData():
            self.buildOneEndCond(sizer2, endCondItem)
        staticsizer.Add(sizer1, 0, wx.ALL, 2)
        staticsizer.Add(sizer2, 0, wx.ALL, 2)
#        self.SetSizerAndFit(staticSizer)
#        staticSizer.Fit(self)
        
        return staticsizer
    def buildOneEndCond(self, sizer, endCondItem):
        for idx, value, eHandler, label in [endCondItem]:
            sc = wx.SpinCtrl(self, size=(40,-1))
            sc.SetRange(1,100)
            sc.SetValue(value)
            self.Bind(wx.EVT_TEXT, self.EvtCondText, sc)
            sizer.Add(sc, 0, wx.ALL, 2)
            text = wx.StaticText(self, label=label, style=wx.ALIGN_CENTER)
            sizer.Add(text, 0, wx.ALL, 2)
    def creatEndCondData(self):
        return (('end', 1, self.EvtEndCond, u'天内至少'),
                    ('end', 1, self.EvtEndCond, u'天以上满足终止条件且不满足均价关系'))
    def buildEndPriceData(self):
        return ((u'收盘价', self.choiceList,2, self.EvtEndCond, self.daysAveList, 5, self.EvtEndCond),
                        (u'日均价', self.pickList,1, self.EvtEndCond, '', '0', self.EvtEndCond))
    def buildOneEndPrice(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        cbx = wx.CheckBox(self, label=u'终止条件')
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, cbx)
        sizer.Add(cbx, 0, wx.ALL, 2)
        for label, choices, idx1, eHandler1, daychoices, idx2, eHandler2 in self.buildEndPriceData():
            text = wx.StaticText(self, label=label)
            sizer.Add(text, 0, wx.ALL, 2)
            cmbx = wx.ComboBox(self, size=(60, -1), choices=choices, value=choices[idx1],style=wx.CB_DROPDOWN)
            self.Bind(wx.EVT_COMBOBOX, self.EvtCom1Box, cmbx )
            
            cmbx.Disable()
            sizer.Add(cmbx, 0, wx.ALL, 2)
            if (daychoices != ''):
                obj = wx.ComboBox(self, size=(60, -1), choices=daychoices, value=daychoices[idx2],style=wx.CB_DROPDOWN)
                self.Bind(wx.EVT_COMBOBOX, self.EvtCom1Box, obj )
            else:
                obj = wx.TextCtrl(self, value='0', size=(30,-1))
                self.Bind(wx.EVT_TEXT, self.EvtCondText, obj)   
            obj.Disable()
            sizer.Add(obj, 0, wx.ALL, 2)
        text = wx.StaticText(self, label='%')
        sizer.Add(text, 0, wx.ALL, 2)
        return sizer    

    def createAmtErgData(self):
        return ((u'累计量能达到', '100', self.EvtAmtErg, u'%以上' ),)
    def createAmtErgBars(self):
        box = wx.StaticBox(self, -1, u"量能标准")
        staticsizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        for amountErgItem in self.createAmtErgData():
            self.createOneAmtErg(staticsizer, amountErgItem)
        return staticsizer
    def createOneAmtErg(self, sizer, amountErgItem):
        for label, value, eventHandler, label2 in [amountErgItem]:
            text= wx.StaticText(self, label=label)
            sizer.Add(text, 0, wx.ALL, 2)
            sc = wx.SpinCtrl(self, size=(40,-1))
            sc.SetRange(1,100)
            sc.SetValue(value)
            self.Bind(wx.EVT_TEXT, eventHandler, sc)    
            sizer.Add(sc, 0, wx.ALL, 2)
            text = wx.StaticText(self, label=label2)
            sizer.Add(text, 0, wx.ALL, 2)
    
    def buildAveRelationBars(self):
        box = wx.StaticBox(self, -1, u"均价关系")
        staticsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        for aveRelationItem in self.buildAveRelationData():
            sizer = self.buildOneAveRelation(aveRelationItem)
            staticsizer.Add(sizer, 0, wx.ALL, 2)
        return staticsizer
    def buildAveRelationData(self):
        return ((u'条件一', self.EvtCheckBox, 0, self.EvtCombo1Box, 1, self.EvtCombo2Box,1, self.Evtcombo3Box, '10', self.EvtComboBox),
                    (u'条件二', self.EvtCheckBox, 0, self.EvtCombo1Box, 1, self.EvtCombo2Box,1, self.Evtcombo3Box, '10', self.EvtComboBox),
                    (u'条件三', self.EvtCheckBox, 0, self.EvtCombo1Box, 1, self.EvtCombo2Box,1, self.Evtcombo3Box, '10', self.EvtComboBox),
                    (u'条件四', self.EvtCheckBox, 0, self.EvtCombo1Box, 1, self.EvtCombo2Box,1, self.Evtcombo3Box, '10', self.EvtComboBox),
                    (u'条件五', self.EvtCheckBox, 0, self.EvtCombo1Box, 1, self.EvtCombo2Box,1, self.Evtcombo3Box, '10', self.EvtComboBox),
                    (u'条件六', self.EvtCheckBox, 0, self.EvtCombo1Box, 1, self.EvtCombo2Box,1, self.Evtcombo3Box, '10', self.EvtComboBox))
    def buildOneAveRelation(self, aveRelationItem):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        for cbxLabel, cbxHandler, cmb1idx, cmb1Handler, \
        cmb2idx, cmb2Handler, cmb3idx, cmb3Handler, \
        value, textHandler in [aveRelationItem]:
            cbx = wx.CheckBox(self, label=cbxLabel)
            self.Bind(wx.EVT_CHECKBOX, cbxHandler, cbx)
            sizer.Add(cbx, 0, wx.ALL, 2)
            
            text = wx.StaticText(self, label=u'收盘价')
            sizer.Add(text, 0, wx.ALL, 2)
            
            cmbx = wx.ComboBox(self, size=(50, -1), choices=self.choiceList, value=self.choiceList[cmb1idx],style=wx.CB_DROPDOWN)
            self.Bind(wx.EVT_COMBOBOX, cmb1Handler, cmbx )
            sizer.Add(cmbx, 0, wx.ALL, 2)
            
            cmbx = wx.ComboBox(self, size=(40, -1), choices=self.daysAveList, value=self.daysAveList[cmb2idx],style=wx.CB_DROPDOWN)
            self.Bind(wx.EVT_COMBOBOX, cmb2Handler, cmbx )
            sizer.Add(cmbx, 0, wx.ALL, 2)
            
            text = wx.StaticText(self, label=u'日均价')
            sizer.Add(text, 0, wx.ALL, 2)
            
            cmbx = wx.ComboBox(self, size=(50, -1), choices=self.pickList, value=self.pickList[cmb3idx],style=wx.CB_DROPDOWN)
            self.Bind(wx.EVT_COMBOBOX, cmb3Handler, cmbx )
            sizer.Add(cmbx, 0, wx.ALL, 2)
            
            textctrl = wx.TextCtrl(self, value=value, size=(30,-1))
            self.Bind(wx.EVT_TEXT, textHandler, textctrl)
            sizer.Add(textctrl, 0, wx.ALL, 2)
            
            text = wx.StaticText(self, label='%')
            sizer.Add(text, 0, wx.ALL, 2)
        return sizer    
    def EvtCheckBox(self, e):
        print(e)
        a = e.GetEventObject()
        print(a)
        print(a.GetValue())
    def EvtStartDate(self, e):
        print(e)
        print(e.GetDate())
        a = e.GetDate()
        b=a.FormatISODate()
        print(type(a))
        print(b)
    def EvtCond1(self, event):
        pass
    def EvtCombo1Box(self, e):
        print(e)
        print(e.GetSelection())
        print(e.GetString())
        pass
    def EvtCombo2Box(self, event):
        pass
    def Evtcombo3Box(self, event):
        pass
    def EvtCondText(self, event):
        pass
    def EvtAmtErg(self, event):
        pass
    def EvtCom1Box(self, event):
        pass
    def EvtEndCond(self, event):
        pass
    def Evt_Startup(self, event):
        pass
    def EvtComboBox(self):
        pass
    def EvtDatePick(self):
        pass
class RightPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "This is a PageOne object", (20,20))                
class PageTwo(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        mainsplitter = MultiSplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.splitterpanel1 = LeftPanel(mainsplitter)
        self.splitterpanel2 = RightPanel(mainsplitter)
        mainsplitter.SetOrientation(wx.HORIZONTAL)
        mainsplitter.AppendWindow(self.splitterpanel1, -1)
        mainsplitter.AppendWindow(self.splitterpanel2, -1)
        mainsplitter.SetSashPosition(0, 420)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(mainsplitter, 1, wx.EXPAND | wx.ALL)
        self.SetBackgroundColour("white")
        self.SetSizer(mainSizer)
        self.Fit()

class MyFrame(wx.Frame):
    def __init__(self, parent, title=""):
        wx.Frame.__init__(self, parent, title=title, size=(1000, 600))
        self.CreateStatusBar()
        # 1st Generate menus: File, Edit
#        self.createMenuBar()
        # Here we create a panel and a notebook on the panel
        p = wx.Panel(self, wx.ID_ANY)
        nb = wx.Notebook(p)
        
        # Here we create a panel and a notebook on the panel
        page1 = PageTwo(nb)
        page2 = MainPanel(nb)
#        page1 = PageOne(nb)
        
        
        # add the pages to the notebook with the label to show on the tab
        nb.AddPage(page1, "Page 1")
        nb.AddPage(page2, "Page 2")
        
        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)
        p.SetSizer(sizer)
        p.Fit()
        
        self.SetBackgroundColour("white")
        self.Layout()
        
    def menuData(self):
        return (("&File",(
                      ("&Open","Open a file from directory",self.OnOpen),
                      ("","",""),
                      ("&About","about this editor",self.OnAbout),
                      ("","",""),
                      ("E&xit", "Exit the programer",self.OnExit))),
                      ("&Edit",(
                      ("&Font","Change the font", self.OnEditFont),
                      ("","",""),
                      ("Dr&aw", "Draw your picture",self.OnEditDraw))))
    def createMenuBar(self):
        menuBar = wx.MenuBar()          ##???
        for eachMenuData in self.menuData():
            menuLabel = eachMenuData[0]
            menuItems = eachMenuData[1]
            menuBar.Append(self.createMenu(menuItems), menuLabel)
        self.SetMenuBar(menuBar)
    def createMenu(self,menuItems):
        menu = wx.Menu()
        for eachLable, eachStatus, eachhandler in menuItems:
            if not eachLable:   #for "", add a spacer
                menu.AppendSeparator()
                continue
            menuItem = menu.Append(-1, eachLable, eachStatus)
            self.Bind(wx.EVT_MENU, eachhandler, menuItem)
        return menu
        # About 
    def OnAbout(self, event):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets. 
        #dlg = wx.MessageDialog( self, "A small text editor", "About Sample Editor", wx.OK)
        dlg = wx.MessageDialog( self, "A small text editor", "About Sample Editor")    #wx.ID can be omited in this case. wxWidget will assign one automaticlly.
        dlg.ShowModal()         # Show it
        dlg.Destroy()             # finally destroy it when finished.
    # Open
    def OnOpen(self, event):
        """ Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.FD_OPEN)    #wx.FD_OPENf for py3.5; wx.OPEN for py2.7
        # 调用了ShowModal。通过它，打开了对话框。“Modal（模式/模态）”意味着在用户点击了确定按钮或者取消按钮之前，他不能在该程序中做任何事情。ShowModal的返回值是被按下的按钮的ID。如果用户点击了确定按钮，我们就读文件
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = open(os.path.join(self.dirname, self.filename), 'r')
            self.control.SetValue(f.read())
            f.close()
        dlg.Destroy()
    # Exit
    def OnExit(self, e):
        self.Close(True)            # Close the frame
    def OnEditFont(self, event):
        pass
    def OnEditDraw(self, event):
        pass


class MainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
#        self.panel= wx.Panel(self, wx.ID_ANY)
        self.start_date='2018-10-20'
        self.end_date=datetime.now().strftime("%Y-%m-%d")       #'2018-10-18'
        
        self.autypeStr = 'nfq'         #不复权
        self.days_num = 30
                
        self.control = wx.TextCtrl(self, size=(200,100),style=wx.TE_MULTILINE)
        self.SetBackgroundColour("grey")
        startY=0
        startX=0
        
        # create some sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=5, vgap=5)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)     #wx.VERTICAL

#        self.quote = wx.StaticText(self, label="STOCK QUANT V0.01 ")
#        grid.Add(self.quote, pos=(startY,startX))

        # A multiline TextCtrl - This is here to show how the events work in this program, don't pay too much attention to it
        self.logger = wx.TextCtrl(self, size=(200,200), style=wx.TE_MULTILINE | wx.TE_READONLY)
        
        # 2nd Generate textCtrls        
#        self.textCtrlHooks=[]
        self.textCtrlFields={}
        self.idx_START_DATE, self.idx_END_DATE, self.idx_WORK_DAY = range(3)
        self.createDateTextBar(self, grid, yPos=0)

        startY-=1
              
        startY+=1


        startY+=1

        
        startY+=1
        
        # Button: Update Data
        self.HQonoff=1          #used to stop self.hq.updateHQdata
        self.updateBtnStatus = 'Update Data'        #or 'Stop'
        self.updateHQbuttons = wx.Button(self, -1, "Update Data")        # add buttons
        grid.Add(self.updateHQbuttons, pos=(startY+1,startX))
        self.Bind(wx.EVT_BUTTON, self.Evt_UpdateButton, self.updateHQbuttons)      
        
        # Gauge
        self.gaugecount=0
        self.gauge = wx.Gauge(self,-1, G_NUM_OF_CODES, size=(80,20))
        grid.Add(self.gauge, pos=(startY+1, startX+1))
        self.Bind(wx.EVT_IDLE, self.GaugeOnIdle, self.gauge)
        self.gauge.SetValue(self.gaugecount)
#        self.gauge.Disable()
#        self.gauge.Hide()
        
        startY+=1
        
        #Radio boxes: auType, qfq, hfq, bfq
        self.auTypeList= ['nfq', 'qfq', 'hfq']
        self.auTyperbx = wx.RadioBox(self, label="Data Type", pos=(startY+1, startX+ 1), choices=self.auTypeList,  majorDimension=3,
                         style=wx.RA_SPECIFY_ROWS)
        grid.Add(self.auTyperbx, pos=(startY+1,startX), span=(1,2))
        self.Bind(wx.EVT_RADIOBOX, self.EvtTypeRadioBox, self.auTyperbx)
        
        
        # add a spacer to the sizer
        grid.Add((10, 40), pos=(startY+ 2,startX))
        
        # the combobox Control
        self.sampleList = ['friends', 'advertising', 'web search', 'Yellow Pages']
        self.lblhear = wx.StaticText(self, label="How did you know us ?")
        grid.Add(self.lblhear, pos=(startY+3,startX))
        self.edithear = wx.ComboBox(self, size=(95, -1), choices=self.sampleList, style=wx.CB_DROPDOWN)
        grid.Add(self.edithear, pos=(startY+3,startX+1))
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, self.edithear)
        self.Bind(wx.EVT_TEXT, self.Evt_StartDate,self.edithear)

        # Checkbox
        self.insure = wx.CheckBox(self, label="Do you want Insured Shipment ?")
        grid.Add(self.insure, pos=(startY+4,startX), span=(1,2), flag=wx.BOTTOM, border=5)
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.insure)
        #self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.OnChecked)

        # Radio Boxes
        radioList = ['blue', 'red', 'yellow', 'orange', 'green', 'purple', 'navy blue', 'black', 'gray']
        rb = wx.RadioBox(self, label="What color would you like ?", pos=(startY+20, startX+ 210), choices=radioList,  majorDimension=3,
                         style=wx.RA_SPECIFY_COLS)
        grid.Add(rb, pos=(startY+5,startX), span=(1,2))
        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, rb)

        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)    #ob2
        self.buttons = []
        for i in range(0, 3):
            self.buttons.append(wx.Button(self,-1, "Button &"+str(i)))        # add buttons
            self.sizer2.Add(self.buttons[i], 1, wx.EXPAND)    # Add several buttons in sizer2; para=1 means 1:1:1.., try 'i'
        # A button
        self.button =wx.Button(self, label="Save")
        self.Bind(wx.EVT_BUTTON, self.OnClick,self.button)
        # Use some sizers to see layout options

        #hSizer = grid + logger, mainSizer = hSizer + Button.
        hSizer.Add(grid, 0, wx.ALL, 5)
        hSizer.Add(self.logger, 0, wx.ALL, 5)
        mainSizer.Add(hSizer, proportion=0,flag=wx.EXPAND|wx.ALL, border=5)
        mainSizer.Add(self.control, proportion=0,flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT,border = 5)
        mainSizer.Add(self.sizer2, 0, wx.CENTER)
        #mainSizer.Add(self.sizer, 0, wx.ALL, 5)

        mainSizer.Add(self.button, 0, wx.CENTER)
        self.SetSizerAndFit(mainSizer)
        self.gauge.Hide()
#        self.hq = hqdata.HqDataHandler(self)
        self.hq = HqDataHandler(self)
#        self.model = SimpleDBName()
        pub.subscribe(self.updateDisplay, "update")
#        self.Refresh()
###### Model ######
    def updateStartDate(self, model):
        self.textCtrlFields["start date:"].SetValue(model.start_date)


###### Viewer ######
    def dateTextData(self):
        #label, size, value, handler
        return (("start date", (80, -1), self.start_date, self.Evt_StartDate),
                     ("end date", (80, -1), self.end_date, self.Evt_EndDate),
                     ("work days", (40, -1), '', self.Evt_DaysNum))
    def createDateTextBar(self, panel, grid, yPos=0):
        for dateTextItem in self.dateTextData():
            self.buildOneDateText(panel,grid, yPos, dateTextItem)
            yPos+=1
    def buildOneDateText(self, panel, grid, yPos, dateTextItem):
        for label, size, value, handler in [dateTextItem]:
            text = wx.StaticText(panel, label=label)
            grid.Add(text, pos=(yPos, 0))
            textctrl = wx.TextCtrl(panel, value=value, size=size)
            self.textCtrlFields[label]=textctrl
#            self.textCtrlHooks.append(textctrl)
            grid.Add(textctrl, (yPos, 1))
            self.Bind(wx.EVT_TEXT, handler, textctrl)
            

    def buttonData(self):
        return(("Update Data", self.Evt_UpdateButton))   
    def createButtonBar(self, panel, grid, yPos = 0):
        xPos = 0
        for eachLable, eachHandler in self.buttonData():
            pos = (yPos, xPos)
            button = self.buildOneButton(panel, grid, eachLable, eachHandler)
            xPos +=button.GetSize().width
            grid.Add(button, pos)
    def buildOneButton(self, parent, label, handler, pos=(0,0)):
        button = wx.button(parent, -1, label, pos)
        self.Bind(wx.EVT_BUTTON, handler, button)
        return button
    
###### Controller ###### 
  
    def Evt_UpdateButton(self, event):
        if (self.updateBtnStatus == 'Update Data'):
            self.HQonoff=1
            self.updateBtnStatus = 'Stop'
            self.updateHQbuttons.SetLabel(self.updateBtnStatus)
#            for textCtrlHook in self.textCtrlHooks:
#                textCtrlHook.Disable()
            for label in self.textCtrlFields:
                self.textCtrlFields[label].Disable()
#            self.editstartdate.Disable()
#            self.editenddate.Disable()
#            self.updateHQbuttons.Disable()
            self.auTyperbx.Disable()        #not work, why?
    
            self.gaugecount = 0
            self.gauge.SetValue(self.gaugecount)
            self.gauge.Show()
            self.logger.AppendText('Evt_UpdateButton\n')
            self.logger.AppendText('hq update start\n')
            t = threading.Thread(target=self.hq.updateHQdata, args=())
            t.start()
#            t = threading.Thread(target=wx.CallAfter, args=(self.hq.updateHQdata,))
#            wx.CallAfter(self.hq.updateHQdata)
        elif (self.updateBtnStatus == 'Stop'):
            self.HQonoff=0
            print('clear self.HQonoff to 0, to stop hqupdate')
            self.updateBtnStatus = 'Update Data'
            #self.updateHQbuttons.SetLabel(self.updateBtnStatus)
            self.updateHQbuttons.Disable()
            #print("updateBtnStatus is %s"%self.updateBtnStatus)
#        t.join()                
        #self.hq.updateHQdata()
#        self.auTyperbx.Enable()
#        self.logger.AppendText('hq update end\n')
#        self.editstartdate.Enable()
#        self.editenddate.Enable()
#        self.updateHQbuttons.Enable()
            pass
    def get_startdate_byworkday(self,end_date_str, numofdays):
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        if end_date.isoweekday() in [6,7]:
            preDate = end_date-timedelta(end_date.isoweekday()-5)
        else:
            preDate = end_date
        while (numofdays>1):
            if (preDate.isoweekday() not in [6,7]):
                numofdays-=1
                preDate = preDate-timedelta(days=1)
            else:
                preDate = preDate-timedelta(days=1)
        while(preDate.isoweekday() in [6,7]):
            preDate = preDate-timedelta(days=1)
        return preDate.strftime("%Y-%m-%d")
    
    def updateDisplay(self, msg):
        
        if isinstance(msg, str):
            if msg == "endHQupdate":
                #self.logger.AppendText("enable menu,msg=%s\n"%msg)
#                for textCtrlHook in self.textCtrlHooks:
#                    textCtrlHook.Enable()
                for label in self.textCtrlFields:
                    self.textCtrlFields[label].Enable()
                
                self.updateHQbuttons.Enable()
                self.auTyperbx.Enable()

                self.gauge.Hide()
                self.gaugecount = 0
                self.gauge.SetValue(self.gaugecount)
                
                self.updateBtnStatus = 'Update Data'
                self.updateHQbuttons.SetLabel(self.updateBtnStatus)

        elif isinstance(msg, int):
            #self.logger.AppendText('gauge %d\n'%msg)
            self.gaugecount = msg
            self.gauge.SetValue(self.gaugecount)
            
            
#        self.displayLbl.SetLabel("Time since thread started: %s seconds" % t)
    def EvtRadioBox(self, event):
        self.logger.AppendText('EvtRadioBox: %d\n' % event.GetInt())
        
    def EvtTypeRadioBox(self, event):
        self.autypeStr = event.GetString()
        self.hq.update_DB_and_autype()
        self.logger.AppendText('EvtTypeRadioBox: %s\n' % event.GetString())

#        print(event.GetKeyCode())
    def EvtComboBox(self, event):
        self.logger.AppendText('EvtComboBox: %s\n' % event.GetString())
    def OnClick(self,event):
        self.logger.AppendText(" Click on object with Id %d\n" %event.GetId())
    def Evt_StartDate(self, event):
        self.start_date = event.GetString()
        self.logger.AppendText('Evt_StartDate: %s\n' % event.GetString())
    def Evt_DaysNum(self, event):
        if (event.GetString()==''):
            # to avoid infinite loop
            pass
        else:
            try:
                self.logger.AppendText('Evt_DaysNum: %s\n' % event.GetString())
                self.days_num = int(event.GetString())
#                self.start_date = (datetime.now()-timedelta(days=self.days_num)).strftime("%Y-%m-%d")
                self.start_date=self.get_startdate_byworkday(self.end_date, self.days_num)
#                self.textCtrlHooks[self.idx_START_DATE].SetValue(self.start_date)
                self.textCtrlFields["start date"].SetValue(self.start_date)
            except Exception as e:
                print(e)
#                self.textCtrlHooks[self.idx_WORK_DAY].SetValue('')
                self.textCtrlFields["work days"].SetValue('')
        self.logger.AppendText('Evt_DaysNum: %s\n' % event.GetString())
    def Evt_EndDate(self, event):
        self.end_date = event.GetString()
        self.logger.AppendText('Evt_EndDate: %s\n' % event.GetString())
    def EvtChar(self, event):
        self.logger.AppendText('EvtChar: %d\n' % event.GetKeyCode())
        event.Skip()
    def EvtCheckBox(self, event):
        self.logger.AppendText('EvtCheckBox: %d\n' % event.IsChecked())    #IsChecked(), not OnChecked. https://docs.wxpython.org/wx.CheckBox.html?highlight=checkbox
    
    def GaugeOnIdle(self):
#        self.logger.AppendText('GaugeOnIdle\n' )
#        self.gaugecount = self.gaugecount + 1
#        if self.gaugecount >= 80:
#            self.gaugecount = 0
#        self.gauge.SetValue(self.gaugecount)
        pass
    

class UI(object):
    def __init__(self):
        self.frame = None
        self.panel = None
        self.app = None

    def ui_init(self, title="Stock Quant V0.01"):
        self.app = wx.App(False)  # Create a new app, don't redirect stdout/stderr to a window.
        self.frame = MyFrame(None, title=title)  # A Frame is a top-level window. , size=(200,-1)
#        self.panel = MainPanel(self.frame)
            
        
        self.frame.Show()
        self.app.SetTopWindow(self.frame)
        #self.frame.Center()
        return self.frame, self.panel

    def ui_run(self):
        self.app.MainLoop()
                
def main():
    ui = UI()
    ui.ui_init()
    ui.ui_run()

if __name__ == '__main__':
    main()
