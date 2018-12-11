from datetime import datetime, timedelta
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


edate = '20181211'
print(get_startdate_byworkday(edate, -10))