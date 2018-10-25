# /usr/bin/env python
'''This is the wxPython for stock quant
stock_quant.py
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

G_NUM_OF_CODES = 3625

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
                        #time.sleep(2)
                        #add a columen code
                        df['code']=code
                        #print(df)
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
            
            if (i>=G_NUM_OF_CODES+100):
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


class MyFrame(wx.Frame):
    def __init__(self, parent, title=""):
        
        wx.Frame.__init__(self, parent, title=title, size=(500, 350))
        self.panel= wx.Panel(self, wx.ID_ANY)
        self.CreateStatusBar()
        
        #self.CreateStatusBar()
        #**************Menu, Button**************
        
        # wx.MenuBar，在你的框架的顶部放一个菜单栏。
        # wx.Statusbar，在你的框架底部设置一个区域，来显示状态信息等等。
        # wx.ToolBar，在你的框架中放置一个工具栏
        # wx.Control的子类，这里面提供了一些控件的用户接口（比如说用来显示数据或者用户输入的可视化控件），常见的wx.Control对象包括wx.Button，wx.StaticText，wx.TextCtrl和wx.ComboBox。
        # wx.Panel，它是一个容器，可以用来包含你的许多wx.Control对象。将你的wx.Control对象放入一个wx.Panel中，意味着用户可以直接将一对控件从一个可视化器件移动到另一个可视化器件上。  

        # 1st menu: File
        # Setting up the menu.
        filemenu= wx.Menu() #First Menu, NOT MENU BAR
        # wx.ID_ABOUT and wx.ID_EXIT are standard IDs provided by wxWidgets.
        #menu_file_open is used to connect to EVENT
        menu_file_open = filemenu.Append(wx.ID_ANY, "&Open","Open a file from directory") #wx.ID_ANY can be used for many times. they generate random numbers
        filemenu.AppendSeparator()
        menu_file_about = filemenu.Append(wx.ID_ABOUT, "&About","about this editor") 
        filemenu.AppendSeparator()
        menu_file_exit = filemenu.Append(wx.ID_EXIT, "E&xit", "Exit the programer")
        
        # 2nd menu: Edit
        # Setting up the menu.
        editmenu= wx.Menu() #First Menu, NOT MENU BAR
        menu_edit_Font = editmenu.Append(wx.ID_ABOUT, "&Font","Change the font")
        editmenu.AppendSeparator()  # add a separator
        menu_edit_exit = editmenu.Append(wx.ID_ANY, "Dr&aw", "Draw your picture")
        
        #3rd menu: TODO
        # Setting up the menu.
        # TODO
        
        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File")        # add 1st "filemenu" to the MenuBar
        menuBar.Append(editmenu, "&Edit")     # add 2nd 'editmenu" to MenuBar
        #TODO ... add more if needed
        
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        
        # Set Event
        self.Bind(wx.EVT_MENU, self.OnOpen, menu_file_open)
        self.Bind(wx.EVT_MENU, self.OnExit, menu_file_exit)
        self.Bind(wx.EVT_MENU, self.OnAbout, menu_file_about)

        
        self.start_date='2018-10-20'
        self.end_date=datetime.now().strftime("%Y-%m-%d")       #'2018-10-18'
        
        self.autypeStr = 'nfq'         #不复权
        self.days_num = 30
        
                
        self.control = wx.TextCtrl(self.panel, size=(200,100),style=wx.TE_MULTILINE)
        
        startY=0
        startX=0
        
        # create some sizers
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=2, vgap=5)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
#        hSizer = wx.BoxSizer(wx.VERTICAL)

#        self.quote = wx.StaticText(self, label="STOCK QUANT V0.01 ")
#        grid.Add(self.quote, pos=(startY,startX))

        # A multiline TextCtrl - This is here to show how the events work in this program, don't pay too much attention to it
        self.logger = wx.TextCtrl(self.panel, size=(200,200), style=wx.TE_MULTILINE | wx.TE_READONLY)

        startY-=1
        # Start date
        self.lblstartdate = wx.StaticText(self.panel, label="Start Date :")
        grid.Add(self.lblstartdate, pos=(startY+1,startX))
        self.editstartdate = wx.TextCtrl(self.panel, value=self.start_date, size=(80,-1))
        grid.Add(self.editstartdate, pos=(startY+1,startX+1))
        self.Bind(wx.EVT_TEXT, self.Evt_StartDate, self.editstartdate)
        #self.Bind(wx.EVT_CHAR, self.EvtChar, self.editstartdate)
               
        startY+=1
                
        # End date
        self.lblenddate = wx.StaticText(self.panel, label="End Date :")
        grid.Add(self.lblenddate, pos=(startY+1,startX))
        self.editenddate = wx.TextCtrl(self.panel, value=self.end_date, size=(80,-1))
        grid.Add(self.editenddate, pos=(startY+1,startX+1))
        self.Bind(wx.EVT_TEXT, self.Evt_EndDate, self.editenddate)      
        #self.Bind(wx.EVT_CHAR, self.EvtChar, self.editenddate)

        startY+=1
        
        # Days number
        self.lbldaysnum = wx.StaticText(self.panel, label="Work days")
        grid.Add(self.lbldaysnum, pos=(startY+1,startX))
        self.editdaysnum = wx.TextCtrl(self.panel, size=(40,-1))
        grid.Add(self.editdaysnum, pos=(startY+1,startX+1))
        self.Bind(wx.EVT_TEXT, self.Evt_DaysNum, self.editdaysnum)
        
        startY+=1
        
        # Button: Update Data
        self.HQonoff=1          #used to stop self.hq.updateHQdata
        self.updateBtnStatus = 'Update Data'        #'Stop'
        self.updateHQbuttons = wx.Button(self.panel, -1, "Update Data")        # add buttons
        grid.Add(self.updateHQbuttons, pos=(startY+1,startX))
        self.Bind(wx.EVT_BUTTON, self.Evt_UpdateButton, self.updateHQbuttons)      
        
        # Gauge
        self.gaugecount=0
        self.gauge = wx.Gauge(self.panel,-1, G_NUM_OF_CODES, size=(80,20))
        grid.Add(self.gauge, pos=(startY+1, startX+1))
        self.Bind(wx.EVT_IDLE, self.GaugeOnIdle, self.gauge)
        self.gauge.SetValue(self.gaugecount)
        self.gauge.Disable()
        
        startY+=1
        
        #Radio boxes: auType, qfq, hfq, bfq
        self.auTypeList= ['nfq', 'qfq', 'hfq']
        self.auTyperbx = wx.RadioBox(self.panel, label="Data Type", pos=(startY+1, startX+ 1), choices=self.auTypeList,  majorDimension=3,
                         style=wx.RA_SPECIFY_ROWS)
        grid.Add(self.auTyperbx, pos=(startY+1,startX), span=(1,2))
        self.Bind(wx.EVT_RADIOBOX, self.EvtTypeRadioBox, self.auTyperbx)
        
        
        # add a spacer to the sizer
        grid.Add((10, 40), pos=(startY+ 2,startX))
        
        # the combobox Control
        self.sampleList = ['friends', 'advertising', 'web search', 'Yellow Pages']
        self.lblhear = wx.StaticText(self.panel, label="How did you hear from us ?")
        grid.Add(self.lblhear, pos=(startY+3,startX))
        self.edithear = wx.ComboBox(self.panel, size=(95, -1), choices=self.sampleList, style=wx.CB_DROPDOWN)
        grid.Add(self.edithear, pos=(startY+3,startX+1))
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, self.edithear)
        self.Bind(wx.EVT_TEXT, self.Evt_StartDate,self.edithear)

        

        # Checkbox
        self.insure = wx.CheckBox(self.panel, label="Do you want Insured Shipment ?")
        grid.Add(self.insure, pos=(startY+4,startX), span=(1,2), flag=wx.BOTTOM, border=5)
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.insure)
        #self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.OnChecked)

        # Radio Boxes
        radioList = ['blue', 'red', 'yellow', 'orange', 'green', 'purple', 'navy blue', 'black', 'gray']
        rb = wx.RadioBox(self.panel, label="What color would you like ?", pos=(startY+20, startX+ 210), choices=radioList,  majorDimension=3,
                         style=wx.RA_SPECIFY_COLS)
        grid.Add(rb, pos=(startY+5,startX), span=(1,2))
        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, rb)
    
        
        # SIZER####################
        # wx.BoxSizer，以水平或垂直的方式将控件放置在一条线上。
        # wx.GridSizer，将控件以网状结构放置。
        # wx.FlexGridSizer，它和wx.GridSizer相似，但是它允许以更加灵活的方式放置可视化控件
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)    #ob2
        self.buttons = []
        for i in range(0, 3):
            self.buttons.append(wx.Button(self.panel,-1, "Button &"+str(i)))        # add buttons
            self.sizer2.Add(self.buttons[i], 1, wx.EXPAND)    # Add several buttons in sizer2; para=1 means 1:1:1.., try 'i'
        # A button
        self.button =wx.Button(self.panel, label="Save")
        self.Bind(wx.EVT_BUTTON, self.OnClick,self.button)
        # Use some sizers to see layout options
        
        #self.sizer = wx.BoxSizer(wx.VERTICAL)        #obj 1
        #self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        #grid.Add(self.control, pos=(6,0))
        #Grid.Add(self.sizer2, pos=(7,0))
        #self.sizer.Add(self.control, 1, wx.EXPAND)    # add control panel. Add(PanelName, size(in portion), type). 4:1
        # also see wx.GROW, wx.SHAPED
        # also see wx.ALIGN_CENTER_HORIZONTAL, wx.ALIGN_CENTER_VERICAL
        # also see wx.ALIGN_LEFT,wx.ALIGN_TOP,wx.ALIGN_RIGHT和wx.ALIGN_BOTTOM中选择几个作为一个组合。默认的行为是wx.ALIGN_LEFT | wx.ALIGN_TOP
        #self.sizer.Add(self.sizer2, 1, wx.EXPAND)    # sizer2 in sizer, try '-1'(don't change size)

        #Layout sizers
        # 建立了你的可视化控件之后并将它们添加到sizer（或者嵌套的sizer）里面，下一步就是告诉你的框架或者窗口去调用这个sizer，你可以完成这个，用以下三步
        #self.SetSizer(self.sizer)    # 告诉你的窗口或框架去使用这个sizer
        #self.SetAutoLayout(1)    # 告诉你的窗口使用sizer去为你的控件计算位置和大小
        #self.sizer.Fit(self)            # 计算所有控件的初始位置和大小
        # SIZER END ##################
        
    
        #hSizer = grid + logger, mainSizer = hSizer + Button.
        hSizer.Add(grid, 0, wx.ALL, 5)
        hSizer.Add(self.logger, 0, wx.ALL, 5)
        mainSizer.Add(hSizer, proportion=0,flag=wx.EXPAND|wx.ALL, border=5)
        mainSizer.Add(self.control, proportion=0,flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT,border = 5)
        mainSizer.Add(self.sizer2, 0, wx.CENTER)
        #mainSizer.Add(self.sizer, 0, wx.ALL, 5)

        mainSizer.Add(self.button, 0, wx.CENTER)
        self.panel.SetSizerAndFit(mainSizer)
        
#        self.hq = hqdata.HqDataHandler(self)
        self.hq = HqDataHandler(self)
        pub.subscribe(self.updateDisplay, "update")

    
    def Evt_UpdateButton(self, event):
        if (self.updateBtnStatus == 'Update Data'):
            self.HQonoff=1
            self.updateBtnStatus = 'Stop'
            self.updateHQbuttons.SetLabel(self.updateBtnStatus)
            self.editstartdate.Disable()
            self.editenddate.Disable()
#            self.updateHQbuttons.Disable()
            self.editdaysnum.Disable()
            self.auTyperbx.Disable()        #not work, why?
    
            self.gaugecount = 0
            self.gauge.SetValue(self.gaugecount)
            
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
                
                self.editstartdate.Enable()
                self.editenddate.Enable()
                self.updateHQbuttons.Enable()
                self.auTyperbx.Enable()
                self.editdaysnum.Enable()
                self.gaugecount = 0
                self.gauge.SetValue(self.gaugecount)
                self.updateBtnStatus = 'Update Data'
                self.updateHQbuttons.SetLabel(self.updateBtnStatus)
                #self.logger.AppendText('hq update end\n')
#            elif msg == "disableMenu":
#                self.logger.AppendText("disable menus,msg=%s"%msg)
#                self.editstartdate.Disable()
#                self.editenddate.Disable()
#                #self.updateHQbuttons.Disable()
#                self.editdaysnum.Disable()
#                self.auTyperbx.Enable(False)        #not work, why?
        elif isinstance(msg, int):
#            self.logger.AppendText('gauge %d\n'%msg)
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
                self.days_num = int(event.GetString())
#                self.start_date = (datetime.now()-timedelta(days=self.days_num)).strftime("%Y-%m-%d")
                self.start_date=self.get_startdate_byworkday(self.end_date, self.days_num)
                self.editstartdate.SetValue(self.start_date)
            except Exception as e:
                print(e)
                self.editdaysnum.SetValue('')
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
        self.logger.AppendText('GaugeOnIdle\n' )
        self.gaugecount = self.gaugecount + 1
        if self.gaugecount >= G_NUM_OF_CODES+10:
            self.gaugecount = 0
        self.gauge.SetValue(self.gaugecount)
    
    
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


class UI(object):
    def __init__(self):
        self.frame = None
        self.panel = None
        self.app = None

    def ui_init(self, title="Stock Quant V0.01"):
        self.app = wx.App(False)  # Create a new app, don't redirect stdout/stderr to a window.
        self.frame = MyFrame(None, title=title)  # A Frame is a top-level window. , size=(200,-1)
        #self.panel = MainWindow(self.frame)
        self.frame.Show()
        self.frame.Center()
        return self.frame, self.panel

    def ui_run(self):
        self.app.MainLoop()
                
def main():
    ui = UI()
    ui.ui_init()
    ui.ui_run()

if __name__ == '__main__':
    main()
