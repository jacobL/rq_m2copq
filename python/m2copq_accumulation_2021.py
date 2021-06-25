#!/usr/bin/env python
# coding: utf-8

import xlrd
import pymysql

conn  =  pymysql . connect ( host = '10.55.23.168' ,port=33062 ,  user = 'root' ,  passwd = "1234" ,  db = 'rma' ) 
cur  =  conn . cursor () 

# 20210113 于真
#path = 'D:/RMA需求/COPQ/累計資料/2021 月圖 美金_公版_0113.xlsx'
path = 'D:/RMA需求/COPQ/累計資料/2021 月圖 美金_公版_0312.xlsx'

data = xlrd.open_workbook(path)
sheet_raw = data.sheet_by_name('實績版')
print(" row num:", sheet_raw.nrows,",col num:", sheet_raw.ncols)

# 從execl取得最後有值的月，訂為當月=>yearmonthLog
yearmonthLog = 202101 
#yearmonthLog = '0'
for row in range(1, sheet_raw.nrows):
    yearmonth = str(sheet_raw.cell(row,0).value).replace('.0','')
    
    copq = sheet_raw.cell(row,6).value
    #print(yearmonth,' ',yearmonthLog,' copq:',copq)
    if copq!='' and copq > 0 and yearmonth not in ('2021改善前','2020實績') and int(yearmonth) > int(yearmonthLog) :
        yearmonthLog = yearmonth
print('yearmonthLog:',yearmonthLog)

if sheet_raw.nrows > 0 :
    #cur.execute("delete from rma.copq_accumulation_actachievement_w13 where yearmonthLog=%s",(yearmonthLog))   
    #cur.execute("delete from rma.copq_accumulation_actachievement_2021")  
    cur.execute("delete from rma.copq_accumulation_actachievement_2021 where yearmonthLog=%s",(yearmonthLog)) 
    for row in range(1, sheet_raw.nrows):   
        yearmonth = str(sheet_raw.cell(row,0).value).replace('.0','')
        #if yearmonth == '2019實績' : 
        #    continue;
        app = sheet_raw.cell(row,2).value
        area = sheet_raw.cell(row,3).value
        m2copq_target = sheet_raw.cell(row,4).value
        copq_target = sheet_raw.cell(row,5).value
        copq = sheet_raw.cell(row,6).value
        m2copq = sheet_raw.cell(row,7).value
        provision = 0 if sheet_raw.cell(row,8).value == '' else sheet_raw.cell(row,8).value
        purge = 0 if sheet_raw.cell(row,9).value  == '' else sheet_raw.cell(row,9).value 
        mcr = 0 if sheet_raw.cell(row,10).value  == '' else sheet_raw.cell(row,10).value 
        #print('yearmonth:',yearmonth,' app:',app,',area:',area,',m2copq_target:',m2copq_target,',copq_target:',copq_target,',copq:',copq,',m2copq:',m2copq,',provision:',provision,',purge:',purge)
        print('yearmonth:',yearmonth,',provision:',provision,',purge:',purge,',mcr:',mcr)
        cur.execute("insert ignore into rma.copq_accumulation_actachievement_2021(yearmonthLog,yearmonth,app,area,m2copq_target,copq_target,copq,m2copq,provision,`purge`,mcr)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(yearmonthLog,yearmonth,app,area,m2copq_target,copq_target,copq,m2copq,provision,purge,mcr))
cur.execute("commit")        
