# !/usr/bin/env python
'''This is the wxPython for stock quant
stock_quant.py
add model to 'updateData'
add threading.event to 'stop' button
'''


import dataworker
G_NUM_OF_CODES=3
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


import matplotlib  
import numpy as np   
# matplotlib采用WXAgg为后台,将matplotlib嵌入wxPython中  
#matplotlib.use("WXAgg")  
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas  
from matplotlib.figure import Figure  
from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar  



import wx
import wx.lib.agw.aui as aui
import wx.lib.mixins.inspection as wit

import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar




# creat log in trace.log
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
handler = logging.FileHandler('trace.log',mode='a')
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
#debug, info, warn, error, critical

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



#sql_get_codes = "SELECT code FROM '%s'"

import wx
import os
import wx.grid
#import hqdata
from datetime import datetime,timedelta
import threading
from wx.lib.pubsub import pub
import wx.adv
from wx.lib.splitter import MultiSplitterWindow

#class TestTable(wx.grid.PyGridTableBase):#定义网格表
class TestTable(wx.grid.GridTableBase):#定义网格表
    def __init__(self, data={}):
        self.defaultLabel="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        wx.grid.GridTableBase.__init__(self)
#        self.data = { (1,1) : "Here",
#                            (2,2) : "is",
#                            (3,3) : "some",
#                            (4,4) : "data",
#                            }
        self.data=data
        self.odd=wx.grid.GridCellAttr()
#        self.odd.SetBackgroundColour("sky blue")
#        self.odd.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.even=wx.grid.GridCellAttr()
#        self.even.SetBackgroundColour("sea green")
#        self.even.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))

    # these five are the required methods
    def GetNumberRows(self):
        if (isinstance(self.data, pd.core.frame.DataFrame)):
            print("GetNumberRows called, return %d"%self.data.shape[0])
            return self.data.shape[0]
        elif (isinstance(self.data, dict)):
            return 50
    def GetNumberCols(self):
        if (isinstance(self.data, pd.core.frame.DataFrame)):
            print("GetNumberCols called, return %d"%self.data.shape[1])
            return self.data.shape[1]
        elif (isinstance(self.data, dict)):
            return 50
    def IsEmptyCell(self, row, col):
        if (isinstance(self.data, dict)):
            return self.data.get((row, col)) is not None
        elif (isinstance(self.data, pd.core.frame.DataFrame)):
            for rowN, colN in [self.data.shape]:
#                print(row, col, self.data.shape)
                return row<rowN and col<colN
    def GetValue(self, row, col):#为网格提供数据
        if (isinstance(self.data, dict)):
            value = self.data.get((row, col))
        elif (isinstance(self.data, pd.core.frame.DataFrame)):
            value = self.data.iloc[row,col]
        if value is not None:
            if isinstance(value, float):
                value="%.3f"%value
            return value
        else:
            return ''
    def SetValue(self, row, col, value):#给表赋值
        pass
    def GetColLabelValue(self, col):#列标签
        if (isinstance(self.data, pd.core.frame.DataFrame)):
            return self.data.columns[col]
        elif (isinstance(self.data, dict)):
            return str(col)
#    def GetRowLabelValue(self, row):#行标签
#        return self.rowLabels[row]
        
        # Now allow to write table
#        if (isinstance(self.data, dict)):
#            self.data[(row,col)] = value
#        elif (isinstance(self.data, pd.core.frame.DataFrame)):
#            self.data.iloc[row,col] = value
    # the table can also provide the attribute for each cell
    
#    def GetAttr(self, row, col, kind):
#        attr = [self.even, self.odd][row % 2]
#        attr.IncRef()
#        return attr
    def setData(self, data):
        self.data = data


class PageOne(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "This is a PageOne object", (20,20), style=wx.ST_NO_AUTORESIZE)


class RPSLeftPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.rpsNChoices=['5','20','50','120', '240']
        self.rpsMktChoices = [u'全部', u'深市', u'沪市', u'创业板' ]
        self.rpsRangeChoices = [u'全部', u'一年以上']
        self.rpsTextLabelFields={}
#        t = wx.StaticText(self, -1, "This is a Page RPS Left object", (20,20), style=wx.ST_NO_AUTORESIZE)
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        #RPS条件设置
        sizer = self.buildRPSBar()
        mainsizer.Add(sizer,0, wx.EXPAND)
        mainsizer.AddSpacer(10)
        
        #启动按钮
#        name="rpsTglBtn"
#        self.toggleButton = wx.ToggleButton(self, -1, label=u"开始", name= name)
#        self.rpsTextLabelFields[name]=self.toggleButton
#        self.Bind(wx.EVT_TOGGLEBUTTON, self.Evt_toggleButton, self.toggleButton)
#        mainsizer.Add(self.toggleButton)

        #Radio boxes: auType, qfq, hfq, bfq
        self.auTypeStrList= ['nfq', 'qfq', 'hfq']
        self.autypedict={'nfq':None, 'qfq':'qfq', 'hfq':'hfq'}
        sizer = self.buildRPS_InitDataBar()
        mainsizer.Add(sizer, 0, wx.EXPAND)

        #启动按钮
#        name = 'rpsBtn'
#        self.startRPSbuttons = wx.Button(self, -1, "Start", name=name)        # add buttons
#        self.rpsTextLabelFields[name]=self.startRPSbuttons
#        self.Bind(wx.EVT_BUTTON, self.Evt_RPSstartButton, self.startRPSbuttons) 
        

        self.SetBackgroundColour("white")
        self.SetSizer(mainsizer)
        self.Show()
        self.SetDoubleBuffered(True)    #to avoid flickering of text
## Viewer ##

    

    def buildRPS_InitDataBar(self):
#        box = wx.StaticBox(self, -1, u"RPS初始化")
#        staticsizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        staticsizer = wx.BoxSizer(wx.HORIZONTAL)
        cbxname = "auType cbx"
        self.auTyperbx = wx.RadioBox(self, label="Data Type", pos=(-1, -1), choices=self.auTypeStrList,  majorDimension=1,
                         style=wx.RA_SPECIFY_ROWS, name=cbxname)
        self.rpsTextLabelFields[cbxname]=self.auTyperbx
        self.Bind(wx.EVT_RADIOBOX, self.EvtRPSauTypeRadioBox, self.auTyperbx)
        staticsizer.Add(self.auTyperbx)
        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        name = 'rpsInitCbx'
        cbx = wx.CheckBox(self, label=u'允许初始化', name=name)
        self.rpsTextLabelFields[name]=cbx
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, cbx)
        vsizer.Add(cbx, 0, wx.ALL, 2)
        
        vsizer.AddSpacer(4)
        
        name = 'rpsInitBtn'
        self.startRPSbuttons = wx.Button(self, -1, "RPS Init", name=name)        # add buttons
        self.rpsTextLabelFields[name]=self.startRPSbuttons
        self.Bind(wx.EVT_BUTTON, self.Evt_RPSDataInitButton, self.startRPSbuttons) 
        self.startRPSbuttons.Disable()
        vsizer.Add(self.startRPSbuttons)
        
        staticsizer.AddSpacer(10)
        staticsizer.Add(vsizer)
        return staticsizer
    
    def setRpsMkt(self, value):
        self.rpsTextLabelFields["cmbxMarket"].SetValue(value)
        logger.debug("set cmbxMarket=%s",value)
        pass
    
    def setRpsRange(self, value):
        self.rpsTextLabelFields["cmbxRange"].SetValue(value)
        logger.debug("set cmbxRange=%s",value)
    
    def setRpsHighValue(self, valueStr):
        self.rpsTextLabelFields["scRPS_High"].SetValue(str(valueStr))
        logger.debug("set RPS High =%s", str(valueStr))
    
    def setRpsLowValue(self, valueStr):
        self.rpsTextLabelFields["scRPS_Low"].SetValue(str(valueStr))
        logger.debug("set RPS Low =%s", str(valueStr))
    
    def setAllowInitCbx(self, value):
        pass
        
    def setStartDate(self, date):
        self.rpsTextLabelFields["start_date"].SetValue(datetime.strptime(date, "%Y-%m-%d"))
    
    def setEndDate(self, date):
        self.rpsTextLabelFields["end_date"].SetValue(datetime.strptime(date, "%Y-%m-%d"))

    def setRPSN(self, days):
        self.rpsTextLabelFields["cmbxN"].SetValue(days)
        logger.debug("set N=%s",days)        

    def setStartButtonLabel(self, name):
        self.toggleButton.SetLabel(name)

    def setStartButtonOFF(self):
        self.rpsTextLabelFields["rpsTglBtn"].Disable()

    def setRPSPanelOff(self):
        for label in self.rpsTextLabelFields:
            self.rpsTextLabelFields[label].Disable()
        #self.rpsTextLabelFields["rpsTglBtn"].Enable()
    def setRPSPanelOn(self):
        for label in self.rpsTextLabelFields:
            self.rpsTextLabelFields[label].Enable()
        self.startRPSbuttons.Disable()
    def setAuType(self, autype):
        self.auTyperbx.SetSelection(self.auTyperbx.FindString(autype))
        logger.debug("set auType to '%s'"%autype)
        
    def buildRPSDateData(self):
        return ((u"开始日期", "2018-10-25",self.EvtRPSDatePick,"start_date"),
                    (u"截止日期", "2018-10-31",self.EvtRPSDatePick,"end_date"))
    def buildRPSDateBar(self):
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        for chooseRPSDateItem in self.buildRPSDateData():
            self.buildOneRPSDate(hSizer, chooseRPSDateItem)
        return hSizer
    def buildOneRPSDate(self, sizer, dataItem):
        for label, value, eHandler, name in [dataItem]:
            text = wx.StaticText(self, label=label, style=wx.ALIGN_CENTER)
            sizer.Add(text, 0, wx.ALL, 2)
            datepicker = wx.adv.DatePickerCtrl(self, size=(100,-1), style = wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY, name=name)
            self.rpsTextLabelFields[name]=datepicker
#            datepicker = wx.adv.DatePickerCtrl(self, size=(100,-1), style = wx.adv.DP_DEFAULT)
            self.Bind(wx.adv.EVT_DATE_CHANGED, eHandler, datepicker)
            sizer.Add(datepicker, 0, wx.ALL, 2)
    def buildRPSOptionData(self):
        return (('N:', 0, self.rpsNChoices, self.EvtRPSn, "cmbxN", 45),
                    (u'市场', 0, self.rpsMktChoices, self.EvtMktSetting, "cmbxMarket", 65),
                    (u'范围', 0, self.rpsRangeChoices, self.EvtRangeSetting, "cmbxRange", 90))
    def buildOneRPSOption(self, sizer, dataItem):
        for label, cmbxIdx, choices, eHandler, name, size in [dataItem]:
            text = wx.StaticText(self, label=label)
            sizer.Add(text, 0, wx.ALL, 2)
            cmbx = wx.ComboBox(self, size=(size, -1), choices=choices, value=choices[cmbxIdx],style=wx.CB_DROPDOWN|wx.CB_READONLY, name=name)
            self.rpsTextLabelFields[name] = cmbx
            self.Bind(wx.EVT_COMBOBOX, eHandler, cmbx)
            sizer.Add(cmbx, 0, wx.ALL, 2)
    def buildRPSOptionBar(self):
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        for chooseRPSOptionItem in self.buildRPSOptionData():
            self.buildOneRPSOption(hSizer, chooseRPSOptionItem)
        return hSizer

    
    def buildRPStartButton(self, sizer):
        name = 'rpsStartBtn'
        self.startRPSStartBtn = wx.Button(self, -1, "Start", name=name)        # add buttons
        self.rpsTextLabelFields[name]=self.startRPSStartBtn
        self.Bind(wx.EVT_BUTTON, self.Evt_RPStartBtn, self.startRPSStartBtn) 
        sizer.Add(self.startRPSStartBtn, 0, wx.ALIGN_CENTER,2)
        
    def buildRPSRangeData(self):
        return ((u'RPS 从', 100, self.rpsRangeHigh, "scRPS_High"),
                    (u'至', 80, self.rpsRangeLow, "scRPS_Low"))
    def buildOneRPSRange(self, sizer, dataItem):
#        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        for label, initvalue, eHandler,name in [dataItem]:
            text = wx.StaticText(self, label=label)
            sizer.Add(text, 0, wx.ALL, 2)
            sc = wx.SpinCtrl(self, size=(60,-1), name=name)
            sc.SetRange(1,100)
            sc.SetValue(initvalue)
            self.rpsTextLabelFields[name] = sc
            self.Bind(wx.EVT_TEXT, eHandler, sc)
            sizer.Add(sc, 0, wx.ALL, 2)
        
        
    def buildRPSRangeBar(self):
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        for chooseRPSRangeItem in self.buildRPSRangeData():
            self.buildOneRPSRange(hSizer, chooseRPSRangeItem)
        self.buildRPStartButton(hSizer)
        return hSizer

            
    def buildRPSBar(self):
        box = wx.StaticBox(self, -1, u"RPS选项")
        staticsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        #row1
        sizer = self.buildRPSDateBar()
        staticsizer.Add(sizer, 0, wx.ALL, 2)

        #row2
        sizer = self.buildRPSOptionBar()
        staticsizer.Add(sizer, 0, wx.ALL, 2)
        
        #row3
        sizer = self.buildRPSRangeBar()
        staticsizer.Add(sizer, 0, wx.ALL, 2)
        staticsizer.SetSizeHints(self)
        return staticsizer
     
    def EvtCheckBox(self, event):
        name = event.GetEventObject().GetName()
        para = event.GetEventObject().GetValue()
        if (para == True):
            self.startRPSbuttons.Enable()
        else:
            self.startRPSbuttons.Disable()

    def EvtRPSDatePick(self,event):
        name = event.GetEventObject().GetName()
        para = event.GetEventObject().GetValue().Format('%Y-%m-%d')
        pub.sendMessage("pubMsg_RPSLeftPanel", msg=(name, para))
    
    def EvtRPSn(self,event):
        name = event.GetEventObject().GetName()
        para = event.GetString()
        pub.sendMessage("pubMsg_RPSLeftPanel", msg=(name, para))
        #print(e.GetEventObject().GetStringSelection())
        #print(e.GetString())
        pass
    
        
    def EvtRangeSetting(self,event):
        "cmbxRange"
        name = event.GetEventObject().GetName()
        para = event.GetString()
        pub.sendMessage("pubMsg_RPSLeftPanel", msg=(name, para))
        
    def EvtMktSetting(self,event):
        "cmbxMarket"
        name = event.GetEventObject().GetName()
        para = event.GetString()
        pub.sendMessage("pubMsg_RPSLeftPanel", msg=(name, para))
        
    def rpsRangeHigh(self,event):
        "scRPS_High"
        name = event.GetEventObject().GetName()
        para = event.GetString()
        pub.sendMessage("pubMsg_RPSLeftPanel", msg=(name, para))

    def rpsRangeLow(self,event):
        "scRPS_Low"
        name = event.GetEventObject().GetName()
        para = event.GetString()
        pub.sendMessage("pubMsg_RPSLeftPanel", msg=(name, para))
    
    def Evt_RPStartBtn(self, event):
        name = 'rpsStartButton'
        para = event.GetEventObject().GetName()
        #para = event.GetEventObject().GetValue()
        pub.sendMessage("pubMsg_RPSLeftPanel", msg=(name, para))
    
    def EvtRPSauTypeRadioBox(self, event):
        name = event.GetEventObject().GetName()
        para = event.GetString()
        pub.sendMessage("pubMsg_RPSLeftPanel", msg=(name, para))
        #logger.debug('EvtRPSauTypeRadioBox event')
        
    def Evt_RPSDataInitButton(self, event):
        name = 'rpsDataInitButton'
        para = event.GetEventObject().GetName()
        #para = event.GetEventObject().GetValue()
        pub.sendMessage("pubMsg_RPSLeftPanel", msg=(name, para))
        
    def Evt_toggleButton(self,event):
        name = event.GetEventObject().GetName()
        para = event.GetEventObject().GetValue()
        pub.sendMessage("pubMsg_RPSLeftPanel", msg=(name, para))

class RPSRightUpPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
#        t = wx.StaticText(self, -1, "This is a Page RPS Right object", (20,20), style=wx.ST_NO_AUTORESIZE)       
        self.grid = wx.grid.Grid(self)
#        self.data = self.getStockData()
        self.data={}
        self.table = TestTable(self.data)
        self.myTable = self.grid.SetTable(self.table, True, selmode=wx.grid.Grid.SelectRows)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.grid.EnableEditing(False)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.Evt_GridLeftClick, self.grid)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.Evt_GridRightClick, self.grid)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.Evt_GridLeftDClick, self.grid)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_DCLICK, self.Evt_GridLabelLeftDClick, self.grid)
        # Key event
        self.Bind(wx.EVT_KEY_DOWN, self.Evt_GridKeyDown)
        
        self.sizer.Add(self.grid, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(self.sizer)
#        self.sizer.Fit(self)
        self.labelDClickDict={}
        self.directionList=[True, False]
        self.Fit()
        
        #Variable
        self.selectedRowsList=[]

    def getStockData(self):
        try:
            df=pd.read_csv('stock_2.csv')
        except Exception as e:
            print(e)
            df={}
        return df
    def updateTable(self, data):
        self.grid.BeginBatch()
        self.grid.ClearGrid()
        self.data=data
#        self.table.setData(self.data)
#        self.myTable.data=self.data
#        self.table.GetNumberRows()
#        self.table.GetNumberCols()
        
        
        self.table = TestTable(data)
        self.myTable = self.grid.SetTable(self.table, True, selmode=wx.grid.Grid.SelectRows)

#        self.sizer.FitInside(self)
#        self.SetSizer(self.sizer)
        # Autosize the column and row
        self.grid.AutoSize()
        self.grid.Refresh()
        self.grid.ForceRefresh()
        self.grid.EndBatch()
#        self.sizer.Fit(self)
#        self.SetSizer(self.sizer)

    def setGridSelectionOFF(self):
        self.grid.ClearSelection()
    def Evt_GridLabelLeftDClick(self,event):
        self.labelDClickDict[event.Col] = (self.labelDClickDict.get(event.Col, 0)+1)%2
#        print(event.Col)
        if (event.Col>=0):
            name = "RPSGridColLabelLeftDClick"
            para = (self.data, self.data.columns[event.Col], self.directionList[self.labelDClickDict[event.Col]])
#            print(para)
            pub.sendMessage("pubMsg_RPSRightUpPanel", msg=(name, para))
#            self.SetSizer(self.sizer)
#        print(dir(event))
#        print(dir(event.GetEventObject()))
    def Evt_GridKeyDown(self, event):
        if (event.GetKeyCode()==wx.WXK_INSERT):
            print(event)
            self.selectedRowsList = []
        
    def Evt_GridRightClick(self,event):
        """Dont know why : list(self.data['code'][event.GetEventObject().SelectedRows].values) is not working"""
        """Use a stupid way """
        i=0
        codeIdx = 0
        for col in self.data.columns:
            if col =='code':
                codeIdx=i
            i+=1
        para = []
        for idx in event.GetEventObject().SelectedRows:
            para.append(self.data.iloc[idx, codeIdx])
        name = "rpsRightUp_rightClick"
        pub.sendMessage("pubMsg_RPSRightUpPanel", msg=(name, para))
        #event.GetEventObject().ClearSelection()
    def Evt_GridLeftClick(self,event):
        #self.selectedRowsList = event.GetEventObject().GetSelectedRows().append(event.Row)
        pass
#        print("Evt_GridLeftClick---------")
#        print(event.Row)
#        print(event.GetEventObject().SelectedRows
#        self.selectedRowsList = []
#        for i in range(grid.GetNumberRows()):dRows())
#        grid = event.GetEventObject()
#            if (grid.IsInSelection( i, 0 )):
#                self.selectedRowsList.append(i)
#                
#        print(self.selectedRowsList)
        
        
        event.Skip()
    def Evt_GridLeftDClick(self, event):
        i=0
        dateIdx = 0
        codeIdx = 0
        for col in self.data.columns:
            if col =='code':
                codeIdx=i
            elif col =='date':
                dateIdx=i
            i+=1
        name = "RPSGridTableLeftDClick"
        para = self.data.iloc[event.Row, codeIdx]
        pub.sendMessage("pubMsg_RPSRightUpPanel", msg=(name, para))
#        self.SetSizer(self.sizer)
#        print(dir(event))
#        print(event.GetRow())
#        print(type(event.Row))
#        print(event.GetEventObject())
#        event.GetEventObject().SelectRow(event.Row)
#        print(self.data['code'][event.Row])
#        print(self.data['date'][event.Row])
#        print(self.data.iloc[event.Row, codeIdx])
#        print(self.data.iloc[event.Row, dateIdx])
        
class PageThree(wx.Panel):
#    def __init__(self, parent):
#        wx.Panel.__init__(self, parent)
#        t = wx.StaticText(self, -1, "This is a PageThree object", (20,20), style=wx.ST_NO_AUTORESIZE)
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        mainsplitter = MultiSplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.splitterpanel1 = RPSLeftPanel(mainsplitter)
#        self.splitterpanel2 = RPSRightUpPanel(mainsplitter)
        self.splitterpanel2 = RPSRightPanel(mainsplitter)
        mainsplitter.SetOrientation(wx.HORIZONTAL)
        mainsplitter.AppendWindow(self.splitterpanel1, -1)
        mainsplitter.AppendWindow(self.splitterpanel2, -1)
        mainsplitter.SetSashPosition(0, 320)
#        mainsplitter.SetMinimumPaneSize(0)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(mainsplitter, 1, wx.EXPAND | wx.ALL)
        self.SetBackgroundColour("white")
        self.SetSizer(mainSizer)
        self.Fit()
        self.Show()


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
        self.SetSizer(mainsizer)
        mainsizer.Fit(self)
        self.Fit()
        self.Show()
        self.SetDoubleBuffered(True)    #to avoid flickering of text
#        self.statusReadoutPanel.SetDoubleBuffered(True)
    
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
        staticsizer.Add(sizer1, 0, wx.ALL|wx.EXPAND, 2)
        staticsizer.Add(sizer2, 0, wx.ALL|wx.EXPAND, 2)
        
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
        #self.SetSizer(staticsizer)
        #staticsizer.Fit(self)
        
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
            sc = wx.SpinCtrl(self, size=(50,-1))
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
        mainsplitter = MultiSplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.splitterpanel1 = RightUpPanel(mainsplitter)
        self.splitterpanel2 = RightDownPanel(mainsplitter)
        mainsplitter.SetOrientation(wx.VERTICAL)
        mainsplitter.AppendWindow(self.splitterpanel1, -1)
        mainsplitter.AppendWindow(self.splitterpanel2, -1)
        mainsplitter.SetSashPosition(0, 300)
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.Add(mainsplitter, 1, wx.EXPAND | wx.ALL)
#        mainSizer.Add(mainsplitter, 0, wx.ALL)
        self.SetBackgroundColour("light grey")
        self.SetSizer(mainsizer)
        self.Fit()
#        self.SetDoubleBuffered(True)
        self.Show()
        self.SetDoubleBuffered(True)
        
class RightUpPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
#        t = wx.StaticText(self, -1, "This is a RightPanel object", (20,20))                
        grid = wx.grid.Grid(self)
#        self.data = self.getStockData()
        self.data = {}
        self.table = TestTable(self.data)
        self.myTable = grid.SetTable(self.table, True)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
    def getStockData(self):
        try:
            df=pd.read_csv('stock_test.csv')
        except Exception as e:
            print(e)
            df={}
        return df

'''
import mpl_finance as mpf
from matplotlib.pylab import date2num
import datetime
'''
class MyPlot(wx.Panel):
    def __init__(self, parent, id=-1, dpi=None, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.figure = mpl.figure.Figure(dpi=dpi, figsize=(2, 2))
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        #sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)


class PlotNotebook(wx.Panel):
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id=id)
        self.nb = aui.AuiNotebook(self)
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def add(self, name="plot"):
        page = MyPlot(self.nb)
        self.nb.AddPage(page, name)
        return page.figure

class MPL_Panel(wx.Panel):  
    ''''' #MPL_Panel面板,可以继承或者创建实例'''  
    def __init__(self,parent):    
        wx.Panel.__init__(self,parent=parent, id=-1)    
     
        self.Figure = matplotlib.figure.Figure(figsize=(4,3))    
        self.axes = self.Figure.add_axes([0.1,0.1,0.8,0.8])    
        self.FigureCanvas = FigureCanvas(self,-1,self.Figure)    
             
#        #继承鼠标移动显示鼠标处坐标的事件    
#        self.FigureCanvas.mpl_connect('motion_notify_event',self.MPLOnMouseMove)    
#             
#        self.NavigationToolbar = NavigationToolbar(self.FigureCanvas)    
#     
#        self.StaticText = wx.StaticText(self,-1,label='Show Help String')    
#     
#        self.SubBoxSizer = wx.BoxSizer(wx.HORIZONTAL)    
#        self.SubBoxSizer.Add(self.NavigationToolbar,proportion =0, border = 2,flag = wx.ALL | wx.EXPAND)    
#        self.SubBoxSizer.Add(self.StaticText,proportion =-1, border = 2,flag = wx.ALL | wx.EXPAND)    
#     
        self.TopBoxSizer = wx.BoxSizer(wx.VERTICAL)    
#        self.TopBoxSizer.Add(self.SubBoxSizer,proportion =-1, border = 2,flag = wx.ALL | wx.EXPAND)    
        self.TopBoxSizer.Add(self.FigureCanvas,proportion =-10, border = 2,flag = wx.ALL | wx.EXPAND)    
     
        self.SetSizer(self.TopBoxSizer)    
     
    #显示坐标值        
    def MPLOnMouseMove(self,event):    
     
        ex=event.xdata#这个数据类型是numpy.float64    
        ey=event.ydata#这个数据类型是numpy.float64    
        if ex  and ey :    
            #可以将numpy.float64类型转化为float类型,否则格式字符串可能会出错    
            self.StaticText.SetLabel('%10.5f,%10.5f' % (float(ex),float(ey)))    
            #也可以这样    
            #self.StaticText.SetLabel('%s,%s' % (ex,ey))       


class RPSRightDownPanel_pre(wx.Panel):
    """This class is a backup class for drawing NOTEBOOK like picture in wx.Panel.
    not used in this project.
    """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        #t = wx.StaticText(self, -1, "This is a RPSRightDownPanel panel, used to draw RPS-Line of selected stock", (20,20))
        #self.plotter = PlotNotebook(self)
        self.plotter = aui.AuiNotebook(self)
        sizer = wx.BoxSizer()
        sizer.Add(self.plotter, 1, wx.EXPAND)
        self.SetSizer(sizer)
   
    def displayOneRPSbyCode(self, df):
        x = df.iloc[:,0]
        y = df.iloc[:,1]
        axes1 = self.plotter.add('figure 1').gca()
        axes1.plot(x,y,'--b*')
        
    #    axes2 = plotter.add('figure 2').gca()
    #    axes2.plot([1, 2, 3, 4, 5], [2, 1, 4, 2, 3])
        self.Show()
        
        
        
        
    #按钮事件,用于测试绘图  

class RPSRightDownPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
#        t = wx.StaticText(self, -1, "This is a RPSRightDownPanel panel, used to draw RPS-Line of selected stock", (20,20))
        self.MPL = MPL_Panel(self)  
        self.Figure = self.MPL.Figure  
        self.axes = self.MPL.axes  
        self.FigureCanvas = self.MPL.FigureCanvas  
           
#        self.RightPanel = wx.Panel(self,-1)  
#        #测试按钮1  
#        self.Button1 = wx.Button(self.RightPanel,-1,"TestButton",size=(100,40),pos=(10,10))  
#        self.Button1.Bind(wx.EVT_BUTTON,self.Button1Event)  
#        #创建FlexGridSizer  
#        self.FlexGridSizer=wx.FlexGridSizer( rows=5, cols=1, vgap=5,hgap=5)  
#        self.FlexGridSizer.SetFlexibleDirection(wx.BOTH)  
#        #加入Sizer中  
#        self.FlexGridSizer.Add(self.Button1,proportion =0, border = 5,flag = wx.ALL | wx.EXPAND)  
#   
#   
#        self.RightPanel.SetSizer(self.FlexGridSizer)  
#      
        
     
        self.BoxSizer=wx.BoxSizer(wx.VERTICAL)  
        self.BoxSizer.AddSpacer(5)
        for label, eHandler, name in [self.buildCheckBoxData()]:
            self.buildOneCheckBox(label, eHandler, name, self.BoxSizer)
        self.BoxSizer.Add(self.MPL, proportion =-1, border = 2,flag = wx.ALL | wx.EXPAND)  
#        self.BoxSizer.Add(self.RightPanel,proportion =0, border = 2,flag = wx.ALL | wx.EXPAND)  
        self.SetBackgroundColour("white")
        self.SetSizer(self.BoxSizer)
        self.Fit()
        #MPL_Frame界面居中显示  
        self.Centre(wx.BOTH)  
        self.displayMany=False
    def buildCheckBoxData(self):
        return(u"显示多条", self.EvtCheckBox, 'rpsInitCbx')
    
    def buildOneCheckBox(self, label, eHandler, name, sizer):
        cbx = wx.CheckBox(self, label=label, name=name)
        #self.rpsTextLabelFields[name]=cbx
        self.Bind(wx.EVT_CHECKBOX, eHandler, cbx)
        sizer.Add(cbx, 0, wx.ALL, 2)
    def displayOneRPSbyCode(self, df):
        import matplotlib.dates as mdate
        #把date string转换成datetime
        x =  pd.to_datetime(df.iloc[:,0], format = "%Y-%m-%d", errors = 'coerce')
#        x =  pd.to_datetime(df.iloc[:,0],infer_datetime_format=True)
        y = df.iloc[:,1]
        if (not self.displayMany):
            self.axes.cla()
        self.axes.plot(x,y,'-', label=df.loc[0,'code'])  
        handles, labels = self.axes.get_legend_handles_labels()
        self.axes.legend(handles[::-1], labels[::-1])
        #self.axes.set_title(df.loc[0,'code'])
        self.axes.set_title("RPS Lines for Stock")
#        self.axes.plot(df,'--b*')  
        self.axes.grid(True)
        self.axes.xaxis.set_major_formatter(mdate.DateFormatter('%Y-%m-%d'))

        #print(dir(self.FigureCanvas))
        self.FigureCanvas.draw()#一定要实时更新  
    def EvtCheckBox(self,event):
        name = event.GetEventObject().GetName()
        para = event.GetEventObject().GetValue()
        if (para == True):
            self.displayMany=True
        else:
            self.displayMany=False
    
    #按钮事件,用于测试绘图  
    def Button1Event(self,event):  
        x=np.arange(-10,10,0.25)  
        y=np.cos(x)  
        self.axes.plot(x,y,'--b*')  
        self.axes.grid(True)  
        self.FigureCanvas.draw()#一定要实时更新  
class RPSRightPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.mainsplitter = MultiSplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.splitterpanel1 = RPSRightUpPanel(self.mainsplitter)
        self.splitterpanel2 = RPSRightDownPanel(self.mainsplitter)
        self.mainsplitter.SetOrientation(wx.VERTICAL)
        self.mainsplitter.AppendWindow(self.splitterpanel1, -1)
        self.mainsplitter.AppendWindow(self.splitterpanel2, -1)
        # workaround for scroller bar
        # Scroller bar can not be displayed normally, except the window size is changed.
        # So ,I change the SetSashPosition back and force every time after Table is updated.
        
        self.mainsplitter.SetSashPosition(0, 298)
        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.mainsizer.Add(self.mainsplitter, 1, wx.EXPAND | wx.ALL)
#        mainSizer.Add(mainsplitter, 0, wx.ALL)
        self.SetBackgroundColour("light grey")
        self.SetSizer(self.mainsizer)
        self.Fit()
#        self.SetDoubleBuffered(True)
        self.Show()
        self.num=0
        self.sashpositionValue = [299,300]
    def updateSashPosition(self):
        """ workaround for scroller bar:
         A bug is in Scroller bar, it is not working normally after re-writing table in RPSRightUpPanel.
         One way to workaround this bug is to change the window size by modifing the window size.
         Through SetSashPosition() method. I toggle the sashpositionValue every time I update the table
        """
        self.num=(self.num+1)%2
        self.mainsplitter.SetSashPosition(0, self.sashpositionValue[self.num])

class RightDownPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "This is a RightDown panel, used to draw K-Line of selected stock", (20,20))
        self.SetDoubleBuffered(True)
#        
#        self.Figure = matplotlib.figure.Figure(figsize=(4,3))    
#        self.axes = self.Figure.add_axes([0.1,0.1,0.8,0.8])    
#        self.FigureCanvas = FigureCanvas(self,-1,self.Figure)    
#             
#        #继承鼠标移动显示鼠标处坐标的事件    
#        self.FigureCanvas.mpl_connect('motion_notify_event',self.MPLOnMouseMove)    
#             
#        self.NavigationToolbar = NavigationToolbar(self.FigureCanvas)    
#     
#        self.StaticText = wx.StaticText(self,-1,label='Show Help String')    
#     
#        self.SubBoxSizer = wx.BoxSizer(wx.HORIZONTAL)    
#        self.SubBoxSizer.Add(self.NavigationToolbar,proportion =0, border = 2,flag = wx.ALL | wx.EXPAND)    
#        self.SubBoxSizer.Add(self.StaticText,proportion =-1, border = 2,flag = wx.ALL | wx.EXPAND)    
#     
#        self.TopBoxSizer = wx.BoxSizer(wx.VERTICAL)    
#        self.TopBoxSizer.Add(self.SubBoxSizer,proportion =-1, border = 2,flag = wx.ALL | wx.EXPAND)    
#        self.TopBoxSizer.Add(self.FigureCanvas,proportion =-10, border = 2,flag = wx.ALL | wx.EXPAND)    
#     
#        self.SetSizer(self.TopBoxSizer)    
#        
#        
        try:
#            wx.CallAfter(self.test_drawCandleFig)
            pass
        except Exception as e:
            logger.debug(e)
    #显示坐标值        
#    def MPLOnMouseMove(self,event):    
#     
#        ex=event.xdata#这个数据类型是numpy.float64    
#        ey=event.ydata#这个数据类型是numpy.float64    
#        if ex  and ey :    
#            #可以将numpy.float64类型转化为float类型,否则格式字符串可能会出错    
#            self.StaticText.SetLabel('%10.5f,%10.5f' % (float(ex),float(ey)))    
#            #也可以这样    
#            #self.StaticText.SetLabel('%s,%s' % (ex,ey))     
    def date_to_num(self, dates):
        num_time = []
        for date in dates:
            date_time = datetime.strptime(date,'%Y-%m-%d')
            num_date = date2num(date_time)
            num_time.append(num_date)
        return num_time
    
    def test_drawCandleFig(self):
        code="600889.csv"
        csvType = {'date':'str','open':float,'close':float,'high':float,'low':float,'volume':float,'code':'str'}
        df=pd.read_csv("%s"%code, dtype=csvType)
        #df = ts.get_k_data('600889','2018-05-01')
        #df.info()
        #df[:3]
        # dataframe转换为二维数组
        mat_df = df.values
        num_time = self.date_to_num(mat_df[:,0])
        #num_time = date_to_num(mat_df[:,0])
        mat_df[:,0] = num_time
        #         日期,   开盘,     收盘,    最高,      最低,   成交量,    代码
        #mat_df[:3]
        
        fig, ax = plt.subplots(figsize=(8,2))
        fig.subplots_adjust(bottom=0.5)
        mpf.candlestick_ochl(ax, mat_df, width=0.6, colorup='g', colordown='r', alpha=1.0)
        plt.grid(True)
        # 设置日期刻度旋转的角度 
        plt.xticks(rotation=30)
        plt.title("%s"%code.split('.')[0])
        plt.xlabel('Date')
        plt.ylabel('Price')
        # x轴的刻度为日期
        ax.xaxis_date()
        plt.show()
        ###candlestick_ochl()函数的参数
        # ax 绘图Axes的实例
        # mat_df 价格历史数据
        # width    图像中红绿矩形的宽度,代表天数
        # colorup  收盘价格大于开盘价格时的颜色
        # colordown   低于开盘价格时矩形的颜色
        # alpha      矩形的颜色的透明度
    
        
        
class PickByEnergy(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        mainsplitter = MultiSplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.splitterpanel1 = LeftPanel(mainsplitter)
        self.splitterpanel2 = RightPanel(mainsplitter)
        mainsplitter.SetOrientation(wx.HORIZONTAL)
        mainsplitter.AppendWindow(self.splitterpanel1, -1)
        mainsplitter.AppendWindow(self.splitterpanel2, -1)
        mainsplitter.SetSashPosition(0, 420)
#        mainsplitter.SetMinimumPaneSize(0)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(mainsplitter, 1, wx.EXPAND | wx.ALL)
        self.SetBackgroundColour("white")
        self.SetSizer(mainSizer)
        self.Fit()
        #self.Refresh()
        self.Show()

class MyFrame(wx.Frame):
    def __init__(self, parent, title=""):
        wx.Frame.__init__(self, parent, title=title, size=(1000,600))
        self.CreateStatusBar()
        # 1st Generate menus: File, Edit
#        self.createMenuBar()
        # Here we create a panel and a notebook on the panel
        p = wx.Panel(self, wx.ID_ANY)
        nb = wx.Notebook(p)
        
        # Here we create a panel and a notebook on the panel
        page1 = PickByEnergy(nb)
        page2 = DnldHQDataPanel(nb)
        page3 = PageThree(nb)

        
        
        # add the pages to the notebook with the label to show on the tab
        nb.AddPage(page1, "量能筛选")
        nb.AddPage(page2, "数据更新")
        nb.AddPage(page3, "RPS")
        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        self.SetBackgroundColour("white")
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.ALL|wx.EXPAND)
        
        p.SetSizer(sizer)
        p.Fit()
        p.Show()
#        self.SetDoubleBuffered(True)
        
        
#        self.Layout()
        
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

class Viewer(wx.Frame):
    def __init__(self, parent, title=""):
        wx.Frame.__init__(self, parent, title=title, size=(1000,600))
        self.CreateStatusBar()
        # 1st Generate menus: File, Edit
#        self.createMenuBar()
        # Here we create a panel and a notebook on the panel
        p = wx.Panel(self, wx.ID_ANY)
        nb = wx.Notebook(p)
        
        # Here we create a panel and a notebook on the panel
        self.page1 = PickByEnergy(nb)
        self.page2 = DnldHQDataPanel(nb)
        self.page3 = PageThree(nb)

        
        
        # add the pages to the notebook with the label to show on the tab
        nb.AddPage(self.page1, "量能筛选")
        nb.AddPage(self.page2, "数据更新")
        nb.AddPage(self.page3, "RPS")
        # Choose Page 2
        nb.SetSelection(2)
        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        self.SetBackgroundColour("white")
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.ALL|wx.EXPAND)
        
        p.SetSizer(sizer)
        p.Fit()
        p.Show()
        self.Show()
#        self.SetDoubleBuffered(True)
        
        
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
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, " ", "*.*", wx.FD_OPEN)    #wx.FD_OPENf for py3.5; wx.OPEN for py2.7
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
        
class Controller(object):
    def __init__(self, title=''):
        # 1. model
        self.dnldModel = dataworker.DnldHQDataModel()
        self.calcRPSModel = dataworker.CalcRPS_Model()
        # 2. parent view 
        self.view = Viewer(None, title)
        # 3. child view
        self.rpsController = Controller_RPS(self.view.page3.splitterpanel1, self.view.page3.splitterpanel2, self.calcRPSModel)
        self.dnldDataController = Controller_dnldData(self.view.page2, self.dnldModel)
        # 4. show view
        self.view.Show()
                

class Controller_RPS(object):
    def __init__(self, view, viewRight, model):
        logger.debug("hello, %s",__class__)
        self.model = model
        self.view = view
        self.view.setStartDate(self.model.start_date)
        self.view.setEndDate(self.model.end_date)
        self.view.setRPSN(self.model.rpsN)
        self.view.setAuType(self.model.autypeStr)
        self.view.setRpsMkt(self.model.rpsMktValue)
        self.view.setRpsRange(self.model.rpsRangeValue)
        self.view.setRpsHighValue(self.model.rpsHigh)
        self.view.setRpsLowValue(self.model.rpsLow)
        
        self.viewRight = viewRight
        
        
        # msg from view to controller
        pub.subscribe(self.pubMsg_RPSLeftPanel, "pubMsg_RPSLeftPanel")
        # msg from model to controller
        pub.subscribe(self.pubMsg_CalcRPS_Model, "pubMsg_CalcRPS_Model")
        
        # msg from view to controller
        pub.subscribe(self.pubMsg_RPSRightUpPanel, "pubMsg_RPSRightUpPanel")
        
    def pubMsg_RPSRightUpPanel(self, msg):
        logger.debug("pubMsg_RPSRightUpPanel: msg = %s", msg)
        if (isinstance(msg, tuple)):
            #tuple(name, para) style
            if (msg[0]=="RPSGridTableLeftDClick"):
                #双击数据显示code对应 RPS值
                self.model.getRPSbyCode(msg[1])
            if (msg[0]=="RPSGridColLabelLeftDClick"):
                #双击label排序
                self.model.sortExistedRPSdata(msg[1])
            if (msg[0]=="rpsRightUp_rightClick"):
                self.model.saveSelectedCodesToFavorite(msg[1])

    def pubMsg_RPSLeftPanel(self, msg):
        logger.debug("pubMsg_RPSLeftPanel: msg = %s", msg)
        if (isinstance(msg, tuple)):
            #tuple(name, para) style
            if (msg[0]=="start_date"):
                self.model.start_date = msg[1]
                logger.debug("RPS start date changed, = %s", self.model.start_date)
            if (msg[0]=="end_date"):
                self.model.end_date = msg[1]
                logger.debug("RPS end date changed, = %s", self.model.end_date)
            if (msg[0]=="cmbxN"):
                self.model.rpsN=msg[1]
                logger.debug("rpsN = %s", self.model.rpsN)
            if (msg[0]=="rpsDataInitButton"):
                self.worker_rpsDataInitButton(msg[1])
            if (msg[0] =="auType cbx"):
                if (msg[1] in self.view.auTypeStrList):
                    #check box from viewer
                    self.model.set_DBname_and_autype(msg[1])
            if (msg[0]=="rpsStartButton"):
                self.worker_rpsStartButton(msg[1])
            if (msg[0]=="cmbxMarket"):
                self.model.rpsMktValue=msg[1]
                logger.debug("rpsMktValue = %s", self.model.rpsMktValue)
            if (msg[0]=="cmbxRange"):
                self.model.rpsRangeValue=msg[1]
                logger.debug("rpsRangeValue = %s", self.model.rpsRangeValue)
            if (msg[0]=="scRPS_High"):
                self.model.rpsHigh=msg[1]
                logger.debug("rpsHigh = %s", self.model.rpsHigh)
            if (msg[0]=="scRPS_Low"):
                self.model.rpsLow=msg[1]
                logger.debug("rpsLow = %s", self.model.rpsLow)
        pass
        
    
    def worker_rpsStartButton(self, para):
        if (para == 'rpsStartBtn'):
            self.view.setRPSPanelOff()
            logger.debug("pubMsg_RPSLeftPanel: get RPS")
            #update button pressed, to start, from viewer
            t = threading.Thread(target=self.model.getRPSbyDate, args=())
            t.start()
    def worker_rpsDataInitButton(self, para):
        if (para == 'rpsInitBtn'):
            self.view.setRPSPanelOff()
            logger.debug("pubMsg_RPSLeftPanel: start RPS Data Init")
            #update button pressed, to start, from viewer
            t = threading.Thread(target=self.model.calcAllRPS, args=())
            t.start()

    def worker_rpsStartTglButton(self, para):
        if (para == True):
            self.view.setRPSPanelOff()
            self.view.setStartButtonLabel(u'停止')
            self.model.onoff=1
            logger.debug("pubMsg_RPSLeftPanel: start RPS update")
            #update button pressed, to start, from viewer
            t = threading.Thread(target=self.model.calcAllRPS, args=())
            t.start()
        elif (para ==False):
            self.model.onoff=0
            #self.view.setStartButtonLabel(u'开始')
            self.view.setStartButtonOFF()
            #self.view.setRPSPanelOn()   #TODO:only for test. REMOVE this in formal use. setRPSPanelOn() shoule be called when task is finished.
            logger.debug("pubMsg_RPSLeftPanel: stop RPS update")
            #update button pressed, to stop, from viewer

    def pubMsg_CalcRPS_Model(self, msg):
        logger.debug("pubMsg_CalcRPS_Model: msg = %s", msg)
        if (isinstance(msg, tuple)):
        #end_calcAllRPS
            if (msg[0]=="end_getRPSbyDate"):
                self.viewRight.splitterpanel1.updateTable(msg[1])
                self.view.setRPSPanelOn()
                #to refresh RPSRightDownPanel
                #self.viewRight.splitterpanel2.Show()
                self.viewRight.updateSashPosition()
                

            elif (msg[0]=="end_getRPSbyCode"):
                self.viewRight.splitterpanel2.displayOneRPSbyCode(msg[1])
            elif (msg[0]=="end_saveSelectedCodesToFavorite"):
                self.viewRight.splitterpanel1.setGridSelectionOFF()
        elif isinstance(msg, str):
            if msg == "end_calcAllRPS":
                self.view.setRPSPanelOn()
                #self.view.setStartButtonLabel(u'开始')   #for toggle button
            if msg =="end_getRPSbyDate":
                self.view.setRPSPanelOn()
        elif isinstance(msg, int):
            #self.view.setGaugeCount(msg)        
            pass
    
class Viewer_Base(object):
    def __init__(self):
        pass
    def setStartDate(self, date):
        self.textPanelFields["start date"].SetValue(datetime.strptime(date, "%Y-%m-%d"))
        self.setLoggerMsg(date)
    
    def setEndDate(self, date):
        #self.textPanelFields["end date"].SetValue(date)
        self.textPanelFields["end date"].SetValue(datetime.strptime(date, "%Y-%m-%d"))
        self.setLoggerMsg(date)

    def setWorkDays(self, days):
        self.textPanelFields["work days"].SetValue(days)
        self.setLoggerMsg(days)

    def setAuType(self, autype):
        self.auTyperbx.SetSelection(self.auTyperbx.FindString(autype))
        self.setLoggerMsg(autype)
        
class Controller_dnldData(object):
    def __init__(self, view, model):
        logger.debug("hello, %s",__class__)
        self.model=model
        self.view = view
        self.view.setStartDate(self.model.start_date)
        self.view.setEndDate(self.model.end_date)
        self.view.setWorkDays(self.model.days_num)
        self.view.setAuType(self.model.autypeStr)
        
        
        # msg from view to controller
        pub.subscribe(self.pubMsg_DnldHQdataPanel, "pubMsg_DnldHQdataPanel")
        # msg from model to controller
        pub.subscribe(self.pubMsg_DnldHQDataModel, "pubMsg_DnldHQDataModel")

        

    def pubMsg_DnldHQDataModel(self, msg):
        if isinstance(msg, str):
            if msg == "endHQupdate":
                self.view.setPanelOn()     
                self.view.setLoggerMsg("End data udpate\n")           
        elif isinstance(msg, int):
            self.view.setGaugeCount(msg)

    def pubMsg_DnldHQdataPanel(self, msg):
        logger.debug("pubMsg_DnldHQdataPanel: msg = %s", msg)
        if (isinstance(msg, tuple)):
            #tuple(name, para) style
            if (msg[0]=="start date"):
                self.model.start_date = msg[1]
                logger.debug("start date changed, = %s", self.model.start_date)
            if (msg[0]=="end date"):
                self.model.end_date = msg[1]
                logger.debug("end date changed, = %s", self.model.end_date)
            if (msg[0]=="work days"):
                self.worker_work_days(msg[1])
            if (msg[0]=="update button"):
                #self.worker_updateButton(msg[1])
                self.worker_dnldStartButton(msg[1])
            if (msg[0] =="auType cbx"):
                if (msg[1] in self.view.auTypeStrList):
                    #check box from viewer
                    self.model.set_DBname_and_autype(msg[1])
    
#    def worker_updateButton(self, para):
#        if (para == "updating data"):
#            self.view.setPanelOff()
#            self.view.setUpdateButtonLabel('Stop')
#            self.model.HQonoff=1
#            self.view.setLoggerMsg('Start data update')
#            logger.debug("pubMsg_DnldHQdataPanel: start data update")
#            #update button pressed, to start, from viewer
#            t = threading.Thread(target=self.model.updateHQdata, args=())
#            t.start()
#        elif (para =='stop updating'):
#            self.model.HQonoff=0
#            self.view.setUpdateButtonOff()
#            self.view.setLoggerMsg('Stop data update')
#            logger.debug("pubMsg_DnldHQdataPanel: stop data update")
#            #update button pressed, to stop, from viewer
  
    def worker_dnldStartButton(self, para):
        if (para == True):
            self.view.setPanelOff()
            self.view.setUpdateButtonLabel('Stop')
            self.model.HQonoff=1
            logger.debug("pubMsg_DnldHQdataPanel: start data update")
            #update button pressed, to start, from viewer
            t = threading.Thread(target=self.model.updateHQdata, args=())
            t.start()
        elif (para ==False):
            self.model.HQonoff=0
            self.view.setUpdateButtonOff()
            #self.view.setRPSPanelOn()   #TODO:only for test. REMOVE this in formal use. setRPSPanelOn() shoule be called when task is finished.
            logger.debug("pubMsg_DnldHQdataPanel: stop data update")
            #update button pressed, to stop, from viewer
    
    def worker_work_days(self, days):
        try:
            days_num = int(days)
        except Exception as e:
            logger.warn(e)
        start_date=self.get_startdate_byworkday(self.model.end_date, days_num)
        self.model.start_date = start_date
        self.view.setStartDate(start_date)
        logger.debug("work days changed, = %d", days)
        logger.debug("start date changed, = %s", self.model.start_date)
            
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


class DnldHQDataPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        #self.start_date='2018-10-20'
        #self.end_date=datetime.now().strftime("%Y-%m-%d")       #'2018-10-18'
        
        #self.autypeStr = 'nfq'         #不复权
        #self.days_num = ''
                
        self.SetBackgroundColour("white")
        startY=0
        startX=0
        
        # create some sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=5, vgap=5)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)     #wx.VERTICAL

        # A multiline TextCtrl - This is here to show how the events work in this program, don't pay too much attention to it
        self.logger = wx.TextCtrl(self, size=(200,200), style=wx.TE_MULTILINE | wx.TE_READONLY)
        
        # 2nd Generate textCtrls        
        self.textPanelFields={}
        self.idx_START_DATE, self.idx_END_DATE, self.idx_WORK_DAY = range(3)
        
        self.createDatePickerBar(self, grid, yPos=0)
        self.createWorkdaysTextBar(self, grid, yPos=2)
        startY+=3
        
        # Toggle Button: Update Data
        name = "update button"
        self.updateBtnCurrLabel = 'Update Data'        #or 'Stop'
        self.updateHQbuttons = wx.ToggleButton(self, -1, label=u"Update Data", name= name)        # add buttons
        grid.Add(self.updateHQbuttons, pos=(startY+1,startX))
        self.Bind(wx.EVT_TOGGLEBUTTON, self.Evt_UpdateButtonPressed, self.updateHQbuttons) 
        
#        self.updateBtnCurrLabel = 'Update Data'        #or 'Stop'
#        self.updateHQbuttons = wx.Button(self, -1, "Update Data", name="Update Button")        # add buttons
#        grid.Add(self.updateHQbuttons, pos=(startY+1,startX))
#        self.Bind(wx.EVT_BUTTON, self.Evt_UpdateButtonPressed, self.updateHQbuttons) 
        
        
        # Gauge
        self.gaugecount=0
        self.gauge = wx.Gauge(self,-1, G_NUM_OF_CODES, size=(80,20))
        grid.Add(self.gauge, pos=(startY+1, startX+1))
        self.Bind(wx.EVT_IDLE, self.GaugeOnIdle, self.gauge)
        self.gauge.SetValue(self.gaugecount)
#        self.gauge.Hide()      #Hide the gauage after SetSizer(mainSizer), to avoid abnormal display
        
        startY+=1
        
        #Radio boxes: auType, qfq, hfq, bfq
        self.auTypeStrList= ['nfq', 'qfq', 'hfq']
        self.autypedict={'nfq':None, 'qfq':'qfq', 'hfq':'hfq'}

        self.auTyperbx = wx.RadioBox(self, label="Data Type", pos=(startY+1, startX+ 1), choices=self.auTypeStrList,  majorDimension=3,
                         style=wx.RA_SPECIFY_ROWS, name="auType cbx")
        grid.Add(self.auTyperbx, pos=(startY+1,startX), span=(1,2))
        self.Bind(wx.EVT_RADIOBOX, self.EvtTypeRadioBox, self.auTyperbx)
#        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)    #ob2
#        self.buttons = []
#        for i in range(0, 3):
#            self.buttons.append(wx.Button(self,-1, "Button &"+str(i)))        # add buttons
#            self.sizer2.Add(self.buttons[i], 1, wx.EXPAND)    # Add several buttons in sizer2; para=1 means 1:1:1.., try 'i'

        #hSizer = grid + logger, mainSizer = hSizer + Button.
        hSizer.Add(grid, 0, wx.ALL, 5)
        hSizer.Add(self.logger, 0, wx.ALL, 5)
        mainSizer.Add(hSizer, proportion=0,flag=wx.EXPAND|wx.ALL, border=5)
        self.SetSizer(mainSizer)
        self.Fit()
        self.gauge.Hide()

        #pub.subscribe(self.updateDisplay, "update")
        self.SetBackgroundColour("grey")
        self.SetDoubleBuffered(True)        
#        self.Refresh()

###### Viewer ######
    def setStartDate(self, date):
        self.textPanelFields["start date"].SetValue(datetime.strptime(date, "%Y-%m-%d"))
        self.setLoggerMsg(date)
    
    def setEndDate(self, date):
        #self.textPanelFields["end date"].SetValue(date)
        self.textPanelFields["end date"].SetValue(datetime.strptime(date, "%Y-%m-%d"))
        self.setLoggerMsg(date)

    def setWorkDays(self, days):
        self.textPanelFields["work days"].SetValue(days)
        self.setLoggerMsg(days)

    def setAuType(self, autype):
        self.auTyperbx.SetSelection(self.auTyperbx.FindString(autype))
        self.setLoggerMsg(autype)

    def setGaugeCount(self, counter):
        self.gaugecount = counter
        self.gauge.SetValue(self.gaugecount)


    def setPanelOn(self):
        for label in self.textPanelFields:
            self.textPanelFields[label].Enable()
        self.updateHQbuttons.Enable()
        self.auTyperbx.Enable()
        self.gauge.Hide()
        self.gaugecount = 0
        self.gauge.SetValue(self.gaugecount)
        self.updateBtnCurrLabel = 'Update Data'
        self.updateHQbuttons.SetLabel(self.updateBtnCurrLabel)
    
    def setPanelOff(self):
        for label in self.textPanelFields:
            self.textPanelFields[label].Disable()
        #self.updateHQbuttons.Disable()
        self.auTyperbx.Disable()
        self.gauge.Show()
        self.gaugecount = 0
        self.gauge.SetValue(self.gaugecount)
     
    def setUpdateButtonOff(self):
        self.updateHQbuttons.Disable()

    def setUpdateButtonLabel(self, name):
        self.updateHQbuttons.SetLabel(name)

    def setLoggerMsg(self, msg):
        self.logger.AppendText(msg+'\n')

    def workdaysTextData(self):
        #label, size, value, handler
        return (("work days", (40, -1), '', self.Evt_DaysNum),)
    def createWorkdaysTextBar(self, panel, grid, yPos=0):
        for dateTextItem in self.workdaysTextData():
        #for dateTextItem in self.datePickerData():
            self.buildOneWorkdaysText(panel,grid, yPos, dateTextItem)
            yPos+=1
    def buildOneWorkdaysText(self, panel, grid, yPos, dateTextItem):
        for label, size, value, handler in [dateTextItem]:
            text = wx.StaticText(panel, label=label)
            grid.Add(text, pos=(yPos, 0))
            textctrl = wx.TextCtrl(panel, value=value, size=size, name=label, style=wx.TE_PROCESS_ENTER)
            self.Bind(wx.EVT_TEXT_ENTER, handler, textctrl)
            self.textPanelFields[label]=textctrl
#            self.textCtrlHooks.append(textctrl)
            grid.Add(textctrl, (yPos, 1))
            
    def datePickerData(self):
        #label, size, value, handler
        return (("start date", (80, -1), '', self.Evt_StartDate),
                     ("end date", (80, -1), '', self.Evt_StartDate))
    def buildOneDatePicker(self,panel, grid, yPos, dateTextItem):
        for label, size, value, handler in [dateTextItem]:
            text = wx.StaticText(self, label=label, style=wx.ALIGN_CENTER)
            grid.Add(text, pos=(yPos, 0))
            datepicker = wx.adv.DatePickerCtrl(self, size=(100,-1), style = wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY, name=label)
            self.textPanelFields[label]=datepicker
#            datepicker = wx.adv.DatePickerCtrl(self, size=(100,-1), style = wx.adv.DP_DEFAULT)
            self.Bind(wx.adv.EVT_DATE_CHANGED, handler, datepicker)
            grid.Add(datepicker, (yPos, 1))          
    def createDatePickerBar(self, panel, grid, yPos=0):
        for dateTextItem in self.datePickerData():
            self.buildOneDatePicker(panel,grid, yPos, dateTextItem)
            yPos+=1
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

    # changer widget    
    def Evt_UpdateButtonPressed(self,event):
        name = event.GetEventObject().GetName()
        para = event.GetEventObject().GetValue()
        pub.sendMessage("pubMsg_DnldHQdataPanel", msg=(name, para))
        
#        name = "update button" 
#        if (self.updateBtnCurrLabel == "Update Data"):
#            para = "updating data"
#            self.updateBtnCurrLabel = 'Stop'
#        elif (self.updateBtnCurrLabel == 'Stop'):
#            para = "stop updating"
#            self.updateBtnCurrLabel = "Update Data"
#        pub.sendMessage("pubMsg_DnldHQdataPanel", msg=(name, para))

    #def Evt_UpdateButton(self, event):
    #    if (self.updateBtnCurrLabel == 'update data'):
    #        self.HQonoff=1
    #        self.updateBtnCurrLabel = 'Stop'
    #        self.updateHQbuttons.SetLabel(self.updateBtnCurrLabel)
    #        for label in self.textPanelFields:
    #            self.textPanelFields[label].Disable()
    #        self.auTyperbx.Disable()        #not work, why?
    #        self.gaugecount = 0
    #        self.gauge.SetValue(self.gaugecount)
    #        self.gauge.Show()
    #        self.logger.AppendText('Evt_UpdateButton\n')
    #        self.logger.AppendText('hq update start\n')
    #    elif (self.updateBtnCurrLabel == 'Stop'):
            
    #        logger.debug('clear self.HQonoff to 0, to stop hqupdate')
    #        self.updateBtnCurrLabel = 'Update Data'
    #        self.updateHQbuttons.Disable()
    #    pub.sendMessage("pubMsg_DnldHQdataPanel", msg=self.updateBtnCurrLabel)

    
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
    
#    def updateDisplay(self, msg):
        
#        if isinstance(msg, str):
#            if msg == "endHQupdate":
#                #self.logger.AppendText("enable menu,msg=%s\n"%msg)
##                for textCtrlHook in self.textCtrlHooks:
##                    textCtrlHook.Enable()
#                for label in self.textPanelFields:
#                    self.textPanelFields[label].Enable()
                
#                self.updateHQbuttons.Enable()
#                self.auTyperbx.Enable()

#                self.gauge.Hide()
#                self.gaugecount = 0
#                self.gauge.SetValue(self.gaugecount)
                
#                self.updateBtnCurrLabel = 'Update Data'
#                self.updateHQbuttons.SetLabel(self.updateBtnCurrLabel)

#        elif isinstance(msg, int):
#            #self.logger.AppendText('gauge %d\n'%msg)
#            self.gaugecount = msg
#            self.gauge.SetValue(self.gaugecount)
            
            
#        self.displayLbl.SetLabel("Time since thread started: %s seconds" % t)
    def EvtRadioBox(self, event):
        self.logger.AppendText('EvtRadioBox: %d\n' % event.GetInt())
        
    def EvtTypeRadioBox(self, event):
        name = event.GetEventObject().GetName()
        para = event.GetString()
        pub.sendMessage("pubMsg_DnldHQdataPanel", msg=(name, para))
        #self.hq.set_DBname_and_autype()
        self.logger.AppendText('EvtTypeRadioBox: %s\n' % event.GetString())

#        print(event.GetKeyCode())
    def EvtComboBox(self, event):
        self.logger.AppendText('EvtComboBox: %s\n' % event.GetString())
    def OnClick(self,event):
        self.logger.AppendText(" Click on object with Id %d\n" %event.GetId())
    def Evt_StartDate(self, event):
        name = event.GetEventObject().GetName()
        para = event.GetEventObject().GetValue().Format('%Y-%m-%d')
        pub.sendMessage("pubMsg_DnldHQdataPanel", msg=(name, para))
        #self.start_date = event.GetString()
        #self.logger.AppendText('Evt_StartDate: %s\n' % event.GetString())
        #print(1, event.GetString())
        #print(2, event.GetEventObject().GetValue().Format('%Y-%m-%d'))
        
        #print(3, event.GetEventObject().GetName())
        #print(4, event.GetValue())
        #print(5, event.GetValue().strftime("%Y-%m-%d"))
    def Evt_DaysNum(self, event):
        try:
            name = event.GetEventObject().GetName()
            para = int(event.GetString())
            pub.sendMessage("pubMsg_DnldHQdataPanel", msg=(name, para))
        except Exception as e:
            logger.warn(e)
            logger.warn("Input work days is not a valid int Number")

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
        self.c = Controller(title)
        #self.frame = MyFrame(None, title=title)  # A Frame is a top-level window. , size=(200,-1)
#        self.panel = DnldHQDataPanel(self.frame)
            
        
        #self.frame.Show()
        #self.app.SetTopWindow(self.frame)
        #self.frame.Center()
        #return self.frame, self.panel

    def ui_run(self):
        self.app.MainLoop()
                
def main():
    ui = UI()
    ui.ui_init()
    ui.ui_run()

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

# not order
cmd="SELECT date, close FROM hqall_t WHERE code='603999'"
a=engine.execute(cmd)
b=a.fetchall()
N=20
c=b[20][1]



engine = create_engine('sqlite+pysqlite:///qfq_hqData.db', module=sqlite)
cmd="SELECT * FROM hqall_t"
a=engine.execute(cmd)

'''