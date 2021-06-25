import xlrd
import pymysql

conn  =  pymysql . connect ( host = '10.55.23.168' ,port=33062 ,  user = 'root' ,  passwd = "1234" ,  db = 'rma' ) 
cur  =  conn . cursor () 

# 評核excel資料處理
# 20200723  insert copq_xy 
path = 'D:/RMA需求/COPQ/m2 CoPQ BU 評核實績.xlsx'

# 20200701  insert copq_xy
#path = 'D:/RMA需求/COPQ/m2 CoPQ BU 評核鑼.xlsx'

data = xlrd.open_workbook(path)
sheet_raw = data.sheet_by_name('實績')
print(" row num:", sheet_raw.nrows,",col num:", sheet_raw.ncols)
if sheet_raw.nrows > 0 :
    cur.execute("delete from rma.copq_xy")   
    for row in range(2, sheet_raw.nrows):   
        xvalue = sheet_raw.cell(row,3).value
        if xvalue == '' or xvalue == 0:
            continue;
        yearmonth = str(sheet_raw.cell(row,0).value).replace('.0','')
        bu = sheet_raw.cell(row,1).value
        app = sheet_raw.cell(row,2).value       
        
        print(yearmonth,' ',bu,' ',app,' ',xvalue,' ',round(xvalue*5, 2))
        cur.execute("insert ignore into rma.copq_xy (yearmonth,app,bu,xvalue)values(%s,%s,%s,%s)",(yearmonth,app,bu,xvalue))
cur.execute("commit")