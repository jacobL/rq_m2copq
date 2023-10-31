# encoding=utf8  
import sys   
#reload(sys)  
#sys.setdefaultencoding('utf8')
#import codecs 
#sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
#以上放到HPC的python2才會使用

'''
同一支程式，有兩個地方要切換 
1. localDB = true(local)/false(server)， 
2. run_simple('127.0.0.1', 81, app)   #local
   / app.run(host='0.0.0.0', port=81) #server
'''

from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS, cross_origin
from collections import OrderedDict
from werkzeug.serving import run_simple
import pymysql
import datetime
import time
import json
#from calendar import monthrange

#host = '10.55.23.168'
#port=33062
host = '10.55.14.121'
port=3306
user = 'rma'
passwd = "1234"
db = 'rma'

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
CORS(app)
 
bu = {}
bu['OVERALL'] = "'AA BU','ITI BU','MD BU','TV BU'";
bu['AA BU'] = "'AA','AUTO'";
bu['ITI BU'] = "'IAVM','MNT','NB'";
bu['MD BU'] = "'CE','MP','TABLET'";
bu['TV BU'] = "'TV','TV (SET)'";
 
localDB = False  #False #True  

@app.route("/getAccumulation_act_2023_bg", methods=['GET','POST'])
def getAccumulation_act_2023_bg():
    conn = pymysql.connect(host=host, port=port,user=user, passwd=passwd, db=db)
    cur = conn.cursor() 
    if request.method == 'POST':
        app = request.form.get('app');
        yearmonthLog = request.form.get('yearmonth');
        commentType = request.form.get('commentType'); #20200723 區別act/xy的comment
    else :
        app = request.args.get('app');
        yearmonthLog = request.args.get('yearmonth');
        commentType = request.args.get('commentType'); #20200723 區別act/xy的comment
    #yearmonthLog='202201'    
    print('request.method:',request.method,' app:', app,' yearmonthLog:',yearmonthLog,' commentType:',commentType)
    
    returnData = OrderedDict();   
    
    # 20200602 增加 provision, purge
    # 20200702 增加 yearmonthLog條件，提供每月歷史資料查詢
    # 20200810 增加 mcr
    if app == 'OVERALL' : ####################################################################################                
        #AA BG','ILS BG','IMS BG
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'AA BG', copq, NULL)), GROUP_CONCAT(if(app = 'ILS BG', copq, NULL)), \
        GROUP_CONCAT(if(app = 'IMS BG', copq, NULL)), \
        GROUP_CONCAT(if(app = 'AA BG', copq_target, NULL)), GROUP_CONCAT(if(app = 'ILS BG', copq_target, NULL)), \
        GROUP_CONCAT(if(app = 'IMS BG', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr from rma.copq_accumulation_actachievement_2023_newbg a \
        left join (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2023_newbg \
        where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth where app in ('AA BG','ILS BG','IMS BG') \
        and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app")
        if cur.rowcount > 2 :
            AA_BG_copq_accumulation = 0
            ILS_BG_copq_accumulation = 0
            IMS_BG_copq_accumulation = 0

            AA_BG_copq_target_accumulation = 0
            ILS_BG_copq_target_accumulation = 0
            IMS_BG_copq_target_accumulation = 0
            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['AA BG_copq'] = float(r[1])
                    tmp['ILS BG_copq'] = float(r[2])  
                    tmp['IMS BG_copq'] = float(r[3])  
                    tmp['AA BG_copq_target'] = float(r[4])
                    tmp['ILS BG_copq_target'] = float(r[5])
                    tmp['IMS BG_copq_target'] = float(r[6])   
                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        AA_BG_copq_accumulation = AA_BG_copq_accumulation + float(r[1])
                        ILS_BG_copq_accumulation = ILS_BG_copq_accumulation + float(r[2])
                        IMS_BG_copq_accumulation = IMS_BG_copq_accumulation + float(r[3]) 
                    else :
                        AA_BG_copq_accumulation = 0
                        ILS_BG_copq_accumulation = 0
                        IMS_BG_copq_accumulation = 0 
                    AA_BG_copq_target_accumulation = AA_BG_copq_target_accumulation + float(r[4])
                    ILS_BG_copq_target_accumulation = ILS_BG_copq_target_accumulation + float(r[5])  
                    IMS_BG_copq_target_accumulation = IMS_BG_copq_target_accumulation + float(r[6]) 

                    tmp['AA BG_copq'] = AA_BG_copq_accumulation
                    tmp['ILS BG_copq'] = ILS_BG_copq_accumulation  
                    tmp['IMS BG_copq'] = IMS_BG_copq_accumulation   
                    tmp['AA BG_copq_target'] = AA_BG_copq_target_accumulation
                    tmp['ILS BG_copq_target'] = ILS_BG_copq_target_accumulation
                    tmp['IMS BG_copq_target'] = IMS_BG_copq_target_accumulation   
                tmp['m2copq'] = r[7]        
                tmp['m2copq_target'] = r[8]  

                tmp['provision'] = r[9]
                tmp['purge'] = r[10]
                tmp['mcr'] = r[11]
                returnData[yearmonth] = tmp
        else :
            returnData[0] = 0 #無資料回傳
            
    elif app == 'AA BG' : #"'AA','AUTO'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'AA', copq, NULL)),GROUP_CONCAT(if(app = 'AUTO', copq, NULL)), \
        GROUP_CONCAT(if(app = 'AA', copq_target, NULL)),GROUP_CONCAT(if(app = 'AUTO', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2023_newbg a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2023_newbg where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('AA','AUTO') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            AA_copq_accumulation = 0
            AUTO_copq_accumulation = 0

            AA_copq_target_accumulation = 0
            AUTO_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['AA_copq'] = float(r[1])
                    tmp['AUTO_copq'] = float(r[2])  
                    tmp['AA_copq_target'] = float(r[3])
                    tmp['AUTO_copq_target'] = float(r[4])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        AA_copq_accumulation = AA_copq_accumulation + float(r[1])
                        AUTO_copq_accumulation = AUTO_copq_accumulation + float(r[2])
                    else :
                        AA_copq_accumulation = 0
                        AUTO_copq_accumulation = 0
                    AA_copq_target_accumulation = AA_copq_target_accumulation + float(r[3])
                    AUTO_copq_target_accumulation = AUTO_copq_target_accumulation + float(r[4])  

                    tmp['AA_copq'] = AA_copq_accumulation  
                    tmp['AUTO_copq'] = AUTO_copq_accumulation 
                    tmp['AA_copq_target'] = AA_copq_target_accumulation
                    tmp['AUTO_copq_target'] = AUTO_copq_target_accumulation
                tmp['m2copq'] = r[5]        
                tmp['m2copq_target'] = r[6]  
                tmp['provision'] = r[7]        
                tmp['purge'] = r[8]
                tmp['mcr'] = r[9]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    elif app == 'ILS BG' : # 'MAA','MNT','TV','TV-SET' ###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'MAA', copq, NULL)),GROUP_CONCAT(if(app = 'MNT', copq, NULL)),GROUP_CONCAT(if(app = 'TV', copq, NULL)),GROUP_CONCAT(if(app = 'TV-SET', copq, NULL)), \
        GROUP_CONCAT(if(app = 'MAA', copq_target, NULL)),GROUP_CONCAT(if(app = 'MNT', copq_target, NULL)),GROUP_CONCAT(if(app = 'TV', copq_target, NULL)),GROUP_CONCAT(if(app = 'TV-SET', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2023_newbg a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2023_newbg where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('MAA','MNT','TV','TV-SET') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            MAA_copq_accumulation = 0
            MNT_copq_accumulation = 0
            TV_copq_accumulation = 0
            TV_SET_copq_accumulation = 0

            MAA_copq_target_accumulation = 0
            MNT_copq_target_accumulation = 0    
            TV_copq_target_accumulation = 0
            TV_SET_copq_target_accumulation = 0

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['MAA_copq'] = float(r[1])
                    tmp['MNT_copq'] = float(r[2]) 
                    tmp['TV_copq'] = float(r[3]) 
                    tmp['TV_SET_copq'] = float(r[4]) 
                    tmp['MAA_copq_target'] = float(r[5])
                    tmp['MNT_copq_target'] = float(r[6])
                    tmp['TV_copq_target'] = float(r[7])
                    tmp['TV_SET_copq_target'] = float(r[8])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        MAA_copq_accumulation = MAA_copq_accumulation + float(r[1])
                        MNT_copq_accumulation = MNT_copq_accumulation + float(r[2])
                        TV_copq_accumulation = TV_copq_accumulation + float(r[3])
                        TV_SET_copq_accumulation = TV_SET_copq_accumulation + float(r[4])
                    else :
                        MAA_copq_accumulation = 0
                        MNT_copq_accumulation = 0
                        TV_copq_accumulation = 0
                        TV_SET_copq_accumulation = 0
                    MAA_copq_target_accumulation = MAA_copq_target_accumulation + float(r[5])    
                    MNT_copq_target_accumulation = MNT_copq_target_accumulation + float(r[6])
                    TV_copq_target_accumulation = TV_copq_target_accumulation + float(r[7])  
                    TV_SET_copq_target_accumulation = TV_SET_copq_target_accumulation + float(r[8])  
                    tmp['MAA_copq'] = MAA_copq_accumulation                    
                    tmp['MNT_copq'] = MNT_copq_accumulation
                    tmp['TV_copq'] = TV_copq_accumulation  
                    tmp['TV_SET_copq'] = TV_SET_copq_accumulation
                    tmp['MAA_copq_target'] = MAA_copq_target_accumulation
                    tmp['MNT_copq_target'] = MNT_copq_target_accumulation
                    tmp['TV_copq_target'] = TV_copq_target_accumulation                    
                    tmp['TV_SET_copq_target'] = TV_SET_copq_target_accumulation
                tmp['m2copq'] = r[9]        
                tmp['m2copq_target'] = r[10]
                tmp['provision'] = r[11]        
                tmp['purge'] = r[12]
                tmp['mcr'] = r[13]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳

    elif app == 'IMS BG' : # 'IMS_CELL','IMS_MODULE(non-NB)','NB_MODULE' ###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'IMS_CELL', copq, NULL)),GROUP_CONCAT(if(app = 'IMS_MODULE(non-NB)', copq, NULL)),GROUP_CONCAT(if(app = 'NB_MODULE', copq, NULL)), \
        GROUP_CONCAT(if(app = 'IMS_CELL', copq_target, NULL)),GROUP_CONCAT(if(app = 'IMS_MODULE(non-NB)', copq_target, NULL)),GROUP_CONCAT(if(app = 'NB_MODULE', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2023_newbg a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2023_newbg where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('IMS_CELL','IMS_MODULE(non-NB)','NB_MODULE') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            IMS_CELL_copq_accumulation = 0
            IMS_MODULE_copq_accumulation = 0
            NB_MODULE_copq_accumulation = 0

            IMS_CELL_copq_target_accumulation = 0
            IMS_MODULE_copq_target_accumulation = 0    
            NB_MODULE_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['IMS_CELL_copq'] = float(r[1])
                    tmp['IMS_MODULE_copq'] = float(r[2]) 
                    tmp['NB_MODULE_copq'] = float(r[3]) 
                    tmp['IMS_CELL_copq_target'] = float(r[4])
                    tmp['IMS_MODULE_copq_target'] = float(r[5])
                    tmp['NB_MODULE_copq_target'] = float(r[6])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        IMS_CELL_copq_accumulation = IMS_CELL_copq_accumulation + float(r[1])
                        IMS_MODULE_copq_accumulation = IMS_MODULE_copq_accumulation + float(r[2])
                        NB_MODULE_copq_accumulation = NB_MODULE_copq_accumulation + float(r[3])
                    else :
                        IMS_CELL_copq_accumulation = 0
                        IMS_MODULE_copq_accumulation = 0
                        NB_MODULE_copq_accumulation = 0
                    IMS_CELL_copq_target_accumulation = IMS_CELL_copq_target_accumulation + float(r[4])
                    IMS_MODULE_copq_target_accumulation = IMS_MODULE_copq_target_accumulation + float(r[5])  
                    NB_MODULE_copq_target_accumulation = NB_MODULE_copq_target_accumulation + float(r[6])  

                    tmp['IMS_CELL_copq'] = IMS_CELL_copq_accumulation  
                    tmp['IMS_MODULE_copq'] = IMS_MODULE_copq_accumulation 
                    tmp['NB_MODULE_copq'] = NB_MODULE_copq_accumulation 
                    tmp['IMS_CELL_copq_target'] = IMS_CELL_copq_target_accumulation
                    tmp['IMS_MODULE_copq_target'] = IMS_MODULE_copq_target_accumulation
                    tmp['NB_MODULE_copq_target'] = NB_MODULE_copq_target_accumulation
                tmp['m2copq'] = r[7]        
                tmp['m2copq_target'] = r[8]  
                tmp['provision'] = r[9]        
                tmp['purge'] = r[10]
                tmp['mcr'] = r[11]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
 
    
    else : # app類
        cur.execute("select yearmonth,copq,copq_target,m2copq,m2copq_target,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2023_newbg where app=%s and (yearmonthLog=%s or yearmonthLog is NULL)",(app,yearmonthLog))
        copq_accumulation = 0
        copq_target_accumulation = 0
        if cur.rowcount > 2 :
            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['copq'] = float(r[1])
                    tmp['copq_target'] = float(r[2])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 :
                        copq_accumulation = copq_accumulation + float(r[1])
                    else :
                        copq_accumulation = 0
                    copq_target_accumulation = copq_target_accumulation + float(r[2])

                    tmp['copq'] = copq_accumulation  
                    tmp['copq_target'] = copq_target_accumulation
                tmp['m2copq'] = r[3]        
                tmp['m2copq_target'] = r[4]  
                tmp['provision'] = r[5]        
                tmp['purge'] = r[6]
                tmp['mcr'] = r[7]

                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    # 20200723 增加commentType 均銘 
    # comment
    if commentType == 'act' :
        cur.execute("select comment from rma.copq_comment_actachievement where app=%s and yearmonth=%s order by id desc limit 1",(app,yearmonthLog))
    elif commentType == 'xy' :
        cur.execute("select comment from rma.copq_comment_xy where yearmonth=%s order by id desc limit 1",(yearmonthLog))
        
    if cur.rowcount > 0 and '202312' in returnData :
        tmp = returnData['202312']; 
        for r in cur :
            tmp['comment'] = r[0]
        returnData['202312'] = tmp
    
    # 20200720 燈圖    
    print(returnData)
    #print('==================================')
    
    cur.execute("select app,handtype from copq_handtype where yearmonth=%s",(yearmonthLog))
    if cur.rowcount > 0 :
        for r in cur : 
            print(r)
            returnData['202312'][r[0]] = r[1]            
    else : # 還沒設本月燈圖
        returnData['202312'][r[0]] = 0;
        
    response = jsonify(returnData)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
    
@app.route("/getYmEnd_bg", methods=['GET','POST'])
def getYmEnd_bg():
    conn = pymysql.connect(host=host, port=port,user=user, passwd=passwd, db=db) 
    cur = conn.cursor() 
    
    returnData = OrderedDict();
    returnData[0] = 202212
    #cur.execute('SELECT max(yearmonthLog) FROM copq_accumulation_actachievement')
    cur.execute('SELECT max(yearmonthLog) FROM copq_accumulation_actachievement_2023_newbg')
    yearmonthLog = cur.fetchone()
    if yearmonthLog is not None :
        returnData[0] = yearmonthLog[0];
    response = jsonify(returnData)
    response.headers.add('Access-Control-Allow-Origin', '*')    
    return response

################################################################################################
##20210113 于真需求，增加202101 
@app.route("/getAccumulation_act_2021", methods=['GET','POST'])
def getAccumulation_act_2021():
    conn = pymysql.connect(host=host, port=port,user=user, passwd=passwd, db=db)
    cur = conn.cursor() 
    if request.method == 'POST':
        app = request.form.get('app');
        yearmonthLog = request.form.get('yearmonth');
        commentType = request.form.get('commentType'); #20200723 區別act/xy的comment
    else :	
        app = request.args.get('app');
        yearmonthLog = request.args.get('yearmonth');
        commentType = request.args.get('commentType'); #20200723 區別act/xy的comment
    #yearmonthLog='202101'    
    print('request.method:',request.method,' app:', app,' yearmonthLog:',yearmonthLog,' commentType:',commentType)
    
    returnData = OrderedDict();   
    
    # 20200602 增加 provision, purge
    # 20200702 增加 yearmonthLog條件，提供每月歷史資料查詢
    # 20200810 增加 mcr
    if app == 'OVERALL' : ####################################################################################                
        
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'AA BU', copq, NULL)), GROUP_CONCAT(if(app = 'ITI BU', copq, NULL)), \
        GROUP_CONCAT(if(app = 'MD BU', copq, NULL)), GROUP_CONCAT(if(app = 'TV BU', copq, NULL)), \
        GROUP_CONCAT(if(app = 'AA BU', copq_target, NULL)), GROUP_CONCAT(if(app = 'ITI BU', copq_target, NULL)), \
        GROUP_CONCAT(if(app = 'MD BU', copq_target, NULL)), GROUP_CONCAT(if(app = 'TV BU', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr from rma.copq_accumulation_actachievement_2021 a \
        left join (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2021 \
        where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth where app in ('AA BU','ITI BU','MD BU','TV BU') \
        and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app")
        if cur.rowcount > 2 :
            AA_BU_copq_accumulation = 0
            ITI_BU_copq_accumulation = 0
            MD_BU_copq_accumulation = 0
            TV_BU_copq_accumulation = 0

            AA_BU_copq_target_accumulation = 0
            ITI_BU_copq_target_accumulation = 0
            MD_BU_copq_target_accumulation = 0
            TV_BU_copq_target_accumulation = 0
            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2020實績' or yearmonth == '2021改善前':
                    tmp['AA BU_copq'] = float(r[1])
                    tmp['ITI BU_copq'] = float(r[2])  
                    tmp['MD BU_copq'] = float(r[3])  
                    tmp['TV BU_copq'] = float(r[4]) 
                    tmp['AA BU_copq_target'] = float(r[5])
                    tmp['ITI BU_copq_target'] = float(r[6])
                    tmp['MD BU_copq_target'] = float(r[7])  
                    tmp['TV BU_copq_target'] = float(r[8])
                else : # 202001 ~ 202012 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        AA_BU_copq_accumulation = AA_BU_copq_accumulation + float(r[1])
                        ITI_BU_copq_accumulation = ITI_BU_copq_accumulation + float(r[2])
                        MD_BU_copq_accumulation = MD_BU_copq_accumulation + float(r[3])
                        TV_BU_copq_accumulation = TV_BU_copq_accumulation + float(r[4]) 
                    else :
                        AA_BU_copq_accumulation = 0
                        ITI_BU_copq_accumulation = 0
                        MD_BU_copq_accumulation = 0
                        TV_BU_copq_accumulation = 0
                    AA_BU_copq_target_accumulation = AA_BU_copq_target_accumulation + float(r[5])
                    ITI_BU_copq_target_accumulation = ITI_BU_copq_target_accumulation + float(r[6])  
                    MD_BU_copq_target_accumulation = MD_BU_copq_target_accumulation + float(r[7])
                    TV_BU_copq_target_accumulation = TV_BU_copq_target_accumulation + float(r[8])

                    tmp['AA BU_copq'] = AA_BU_copq_accumulation
                    tmp['ITI BU_copq'] = ITI_BU_copq_accumulation  
                    tmp['MD BU_copq'] = MD_BU_copq_accumulation  
                    tmp['TV BU_copq'] = TV_BU_copq_accumulation 
                    tmp['AA BU_copq_target'] = AA_BU_copq_target_accumulation
                    tmp['ITI BU_copq_target'] = ITI_BU_copq_target_accumulation
                    tmp['MD BU_copq_target'] = MD_BU_copq_target_accumulation  
                    tmp['TV BU_copq_target'] = TV_BU_copq_target_accumulation
                tmp['m2copq'] = r[9]        
                tmp['m2copq_target'] = r[10]  

                tmp['provision'] = r[11]        
                tmp['purge'] = r[12]
                tmp['mcr'] = r[13]
                returnData[yearmonth] = tmp
        else :
            returnData[0] = 0 #無資料回傳
            
    elif app == 'AA BU' : #"'AA','AUTO'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'AA', copq, NULL)),GROUP_CONCAT(if(app = 'AUTO', copq, NULL)), \
        GROUP_CONCAT(if(app = 'AA', copq_target, NULL)),GROUP_CONCAT(if(app = 'AUTO', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2021 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2021 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('AA','AUTO') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            AA_copq_accumulation = 0
            AUTO_copq_accumulation = 0

            AA_copq_target_accumulation = 0
            AUTO_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2020實績' or yearmonth == '2021改善前':
                    tmp['AA_copq'] = float(r[1])
                    tmp['AUTO_copq'] = float(r[2])  
                    tmp['AA_copq_target'] = float(r[3])
                    tmp['AUTO_copq_target'] = float(r[4])

                else : # 202001 ~ 202012 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        AA_copq_accumulation = AA_copq_accumulation + float(r[1])
                        AUTO_copq_accumulation = AUTO_copq_accumulation + float(r[2])
                    else :
                        AA_copq_accumulation = 0
                        AUTO_copq_accumulation = 0
                    AA_copq_target_accumulation = AA_copq_target_accumulation + float(r[3])
                    AUTO_copq_target_accumulation = AUTO_copq_target_accumulation + float(r[4])  

                    tmp['AA_copq'] = AA_copq_accumulation  
                    tmp['AUTO_copq'] = AUTO_copq_accumulation 
                    tmp['AA_copq_target'] = AA_copq_target_accumulation
                    tmp['AUTO_copq_target'] = AUTO_copq_target_accumulation
                tmp['m2copq'] = r[5]        
                tmp['m2copq_target'] = r[6]  
                tmp['provision'] = r[7]        
                tmp['purge'] = r[8]
                tmp['mcr'] = r[9]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    elif app == 'ITI BU' : #"'IAVM','MNT','NB'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'IAVM', copq, NULL)),GROUP_CONCAT(if(app = 'MNT', copq, NULL)),GROUP_CONCAT(if(app = 'NB', copq, NULL)), \
        GROUP_CONCAT(if(app = 'IAVM', copq_target, NULL)),GROUP_CONCAT(if(app = 'MNT', copq_target, NULL)),GROUP_CONCAT(if(app = 'NB', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2021 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2021 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('IAVM','MNT','NB') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            IAVM_copq_accumulation = 0
            MNT_copq_accumulation = 0
            NB_copq_accumulation = 0

            IAVM_copq_target_accumulation = 0
            MNT_copq_target_accumulation = 0    
            NB_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2020實績' or yearmonth == '2021改善前':
                    tmp['IAVM_copq'] = float(r[1])
                    tmp['MNT_copq'] = float(r[2]) 
                    tmp['NB_copq'] = float(r[3]) 
                    tmp['IAVM_copq_target'] = float(r[4])
                    tmp['MNT_copq_target'] = float(r[5])
                    tmp['NB_copq_target'] = float(r[6])

                else : # 202001 ~ 202012 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        IAVM_copq_accumulation = IAVM_copq_accumulation + float(r[1])
                        MNT_copq_accumulation = MNT_copq_accumulation + float(r[2])
                        NB_copq_accumulation = NB_copq_accumulation + float(r[3])
                    else :
                        IAVM_copq_accumulation = 0
                        MNT_copq_accumulation = 0
                        NB_copq_accumulation = 0
                    IAVM_copq_target_accumulation = IAVM_copq_target_accumulation + float(r[4])
                    MNT_copq_target_accumulation = MNT_copq_target_accumulation + float(r[5])  
                    NB_copq_target_accumulation = NB_copq_target_accumulation + float(r[6])  

                    tmp['IAVM_copq'] = IAVM_copq_accumulation  
                    tmp['MNT_copq'] = MNT_copq_accumulation 
                    tmp['NB_copq'] = NB_copq_accumulation 
                    tmp['IAVM_copq_target'] = IAVM_copq_target_accumulation
                    tmp['MNT_copq_target'] = MNT_copq_target_accumulation
                    tmp['NB_copq_target'] = NB_copq_target_accumulation
                tmp['m2copq'] = r[7]        
                tmp['m2copq_target'] = r[8]
                tmp['provision'] = r[9]        
                tmp['purge'] = r[10]
                tmp['mcr'] = r[11]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳

    elif app == 'MD BU' : #"'CE','MP','TABLET'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'CE', copq, NULL)),GROUP_CONCAT(if(app = 'MP', copq, NULL)),GROUP_CONCAT(if(app = 'TABLET', copq, NULL)), \
        GROUP_CONCAT(if(app = 'CE', copq_target, NULL)),GROUP_CONCAT(if(app = 'MP', copq_target, NULL)),GROUP_CONCAT(if(app = 'TABLET', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2021 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2021 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('CE','MP','TABLET') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            CE_copq_accumulation = 0
            MP_copq_accumulation = 0
            TABLET_copq_accumulation = 0

            CE_copq_target_accumulation = 0
            MP_copq_target_accumulation = 0    
            TABLET_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2020實績' or yearmonth == '2021改善前':
                    tmp['CE_copq'] = float(r[1])
                    tmp['MP_copq'] = float(r[2]) 
                    tmp['TABLET_copq'] = float(r[3]) 
                    tmp['CE_copq_target'] = float(r[4])
                    tmp['MP_copq_target'] = float(r[5])
                    tmp['TABLET_copq_target'] = float(r[6])

                else : # 202001 ~ 202012 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        CE_copq_accumulation = CE_copq_accumulation + float(r[1])
                        MP_copq_accumulation = MP_copq_accumulation + float(r[2])
                        TABLET_copq_accumulation = TABLET_copq_accumulation + float(r[3])
                    else :
                        CE_copq_accumulation = 0
                        MP_copq_accumulation = 0
                        TABLET_copq_accumulation = 0
                    CE_copq_target_accumulation = CE_copq_target_accumulation + float(r[4])
                    MP_copq_target_accumulation = MP_copq_target_accumulation + float(r[5])  
                    TABLET_copq_target_accumulation = TABLET_copq_target_accumulation + float(r[6])  

                    tmp['CE_copq'] = CE_copq_accumulation  
                    tmp['MP_copq'] = MP_copq_accumulation 
                    tmp['TABLET_copq'] = TABLET_copq_accumulation 
                    tmp['CE_copq_target'] = CE_copq_target_accumulation
                    tmp['MP_copq_target'] = MP_copq_target_accumulation
                    tmp['TABLET_copq_target'] = TABLET_copq_target_accumulation
                tmp['m2copq'] = r[7]        
                tmp['m2copq_target'] = r[8]  
                tmp['provision'] = r[9]        
                tmp['purge'] = r[10]
                tmp['mcr'] = r[11]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    elif app == 'TV BU' : #"'TV','TV (SET)'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'TV', copq, NULL)),GROUP_CONCAT(if(app = 'TV (SET)', copq, NULL)), \
        GROUP_CONCAT(if(app = 'TV', copq_target, NULL)),GROUP_CONCAT(if(app = 'TV (SET)', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2021 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2021 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('TV','TV (SET)') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            TV_copq_accumulation = 0
            TV_SET_copq_accumulation = 0

            TV_copq_target_accumulation = 0
            TV_SET_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2020實績' or yearmonth == '2021改善前':
                    tmp['TV_copq'] = float(r[1])
                    tmp['TV_SET_copq'] = float(r[2])  
                    tmp['TV_copq_target'] = float(r[3])
                    tmp['TV_SET_copq_target'] = float(r[4])

                else : # 202001 ~ 202012 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        TV_copq_accumulation = TV_copq_accumulation + float(r[1])
                        TV_SET_copq_accumulation = TV_SET_copq_accumulation + float(r[2])
                    else :
                        TV_copq_accumulation = 0
                        TV_SET_copq_accumulation = 0
                    TV_copq_target_accumulation = TV_copq_target_accumulation + float(r[3])
                    TV_SET_copq_target_accumulation = TV_SET_copq_target_accumulation + float(r[4])  

                    tmp['TV_copq'] = TV_copq_accumulation  
                    tmp['TV_SET_copq'] = TV_SET_copq_accumulation 
                    tmp['TV_copq_target'] = TV_copq_target_accumulation
                    tmp['TV_SET_copq_target'] = TV_SET_copq_target_accumulation
                tmp['m2copq'] = r[5]        
                tmp['m2copq_target'] = r[6] 
                tmp['provision'] = r[7]        
                tmp['purge'] = r[8]
                tmp['mcr'] = r[9]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
    
    else : # app類
        cur.execute("select yearmonth,copq,copq_target,m2copq,m2copq_target,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2021 where app=%s and (yearmonthLog=%s or yearmonthLog is NULL)",(app,yearmonthLog))
        copq_accumulation = 0
        copq_target_accumulation = 0
        if cur.rowcount > 2 :
            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2020實績' or yearmonth == '2021改善前':
                    tmp['copq'] = float(r[1])
                    tmp['copq_target'] = float(r[2])

                else : # 202001 ~ 202012 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 :
                        copq_accumulation = copq_accumulation + float(r[1])
                    else :
                        copq_accumulation = 0
                    copq_target_accumulation = copq_target_accumulation + float(r[2])

                    tmp['copq'] = copq_accumulation  
                    tmp['copq_target'] = copq_target_accumulation
                tmp['m2copq'] = r[3]        
                tmp['m2copq_target'] = r[4]  
                tmp['provision'] = r[5]        
                tmp['purge'] = r[6]
                tmp['mcr'] = r[7]

                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    # 20200723 增加commentType 均銘 
    # comment
    if commentType == 'act' :
        cur.execute("select comment from rma.copq_comment_actachievement where app=%s and yearmonth=%s order by id desc limit 1",(app,yearmonthLog))
    elif commentType == 'xy' :
        cur.execute("select comment from rma.copq_comment_xy where yearmonth=%s order by id desc limit 1",(yearmonthLog))
        
    if cur.rowcount > 0 and '202112' in returnData :
        tmp = returnData['202112']; 
        for r in cur :
            tmp['comment'] = r[0]
        returnData['202112'] = tmp
    
    # 20200720 燈圖    
    #print(returnData)
    #print('==================================')
    cur.execute("select app,handtype from copq_handtype where yearmonth=%s",(yearmonthLog))
    if cur.rowcount > 0 :
        for r in cur : 
            print(r)
            returnData['202112'][r[0]] = r[1]            
    #else : # 還沒設本月燈圖
    #    returnData['202112'][r[0]] = 0;
        
    response = jsonify(returnData)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response 

##20220127 李蔚杉需求，增加2022
@app.route("/getAccumulation_act_2022", methods=['GET','POST'])
def getAccumulation_act_2022():
    conn = pymysql.connect(host=host, port=port,user=user, passwd=passwd, db=db)
    cur = conn.cursor() 
    if request.method == 'POST':
        app = request.form.get('app');
        yearmonthLog = request.form.get('yearmonth');
        commentType = request.form.get('commentType'); #20200723 區別act/xy的comment
    else :	
        app = request.args.get('app');
        yearmonthLog = request.args.get('yearmonth');
        commentType = request.args.get('commentType'); #20200723 區別act/xy的comment
    #yearmonthLog='202201'    
    print('request.method:',request.method,' app:', app,' yearmonthLog:',yearmonthLog,' commentType:',commentType)
    
    returnData = OrderedDict();   
    
    # 20200602 增加 provision, purge
    # 20200702 增加 yearmonthLog條件，提供每月歷史資料查詢
    # 20200810 增加 mcr
    if app == 'OVERALL' : ####################################################################################                
        
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'AA BU', copq, NULL)), GROUP_CONCAT(if(app = 'ITI BU', copq, NULL)), \
        GROUP_CONCAT(if(app = 'MD BU', copq, NULL)), GROUP_CONCAT(if(app = 'TV BU', copq, NULL)), \
        GROUP_CONCAT(if(app = 'AA BU', copq_target, NULL)), GROUP_CONCAT(if(app = 'ITI BU', copq_target, NULL)), \
        GROUP_CONCAT(if(app = 'MD BU', copq_target, NULL)), GROUP_CONCAT(if(app = 'TV BU', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr from rma.copq_accumulation_actachievement_2022 a \
        left join (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2022 \
        where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth where app in ('AA BU','ITI BU','MD BU','TV BU') \
        and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app")
        if cur.rowcount > 2 :
            AA_BU_copq_accumulation = 0
            ITI_BU_copq_accumulation = 0
            MD_BU_copq_accumulation = 0
            TV_BU_copq_accumulation = 0

            AA_BU_copq_target_accumulation = 0
            ITI_BU_copq_target_accumulation = 0
            MD_BU_copq_target_accumulation = 0
            TV_BU_copq_target_accumulation = 0
            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2021實績' or yearmonth == '2022改善前':
                    tmp['AA BU_copq'] = float(r[1])
                    tmp['ITI BU_copq'] = float(r[2])  
                    tmp['MD BU_copq'] = float(r[3])  
                    tmp['TV BU_copq'] = float(r[4]) 
                    tmp['AA BU_copq_target'] = float(r[5])
                    tmp['ITI BU_copq_target'] = float(r[6])
                    tmp['MD BU_copq_target'] = float(r[7])  
                    tmp['TV BU_copq_target'] = float(r[8])
                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        AA_BU_copq_accumulation = AA_BU_copq_accumulation + float(r[1])
                        ITI_BU_copq_accumulation = ITI_BU_copq_accumulation + float(r[2])
                        MD_BU_copq_accumulation = MD_BU_copq_accumulation + float(r[3])
                        TV_BU_copq_accumulation = TV_BU_copq_accumulation + float(r[4]) 
                    else :
                        AA_BU_copq_accumulation = 0
                        ITI_BU_copq_accumulation = 0
                        MD_BU_copq_accumulation = 0
                        TV_BU_copq_accumulation = 0
                    AA_BU_copq_target_accumulation = AA_BU_copq_target_accumulation + float(r[5])
                    ITI_BU_copq_target_accumulation = ITI_BU_copq_target_accumulation + float(r[6])  
                    MD_BU_copq_target_accumulation = MD_BU_copq_target_accumulation + float(r[7])
                    TV_BU_copq_target_accumulation = TV_BU_copq_target_accumulation + float(r[8])

                    tmp['AA BU_copq'] = AA_BU_copq_accumulation
                    tmp['ITI BU_copq'] = ITI_BU_copq_accumulation  
                    tmp['MD BU_copq'] = MD_BU_copq_accumulation  
                    tmp['TV BU_copq'] = TV_BU_copq_accumulation 
                    tmp['AA BU_copq_target'] = AA_BU_copq_target_accumulation
                    tmp['ITI BU_copq_target'] = ITI_BU_copq_target_accumulation
                    tmp['MD BU_copq_target'] = MD_BU_copq_target_accumulation  
                    tmp['TV BU_copq_target'] = TV_BU_copq_target_accumulation
                tmp['m2copq'] = r[9]        
                tmp['m2copq_target'] = r[10]  

                tmp['provision'] = r[11]        
                tmp['purge'] = r[12]
                tmp['mcr'] = r[13]
                returnData[yearmonth] = tmp
        else :
            returnData[0] = 0 #無資料回傳
            
    elif app == 'AA BU' : #"'AA','AUTO'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'AA', copq, NULL)),GROUP_CONCAT(if(app = 'AUTO', copq, NULL)), \
        GROUP_CONCAT(if(app = 'AA', copq_target, NULL)),GROUP_CONCAT(if(app = 'AUTO', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2022 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2022 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('AA','AUTO') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            AA_copq_accumulation = 0
            AUTO_copq_accumulation = 0

            AA_copq_target_accumulation = 0
            AUTO_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2021實績' or yearmonth == '2022改善前':
                    tmp['AA_copq'] = float(r[1])
                    tmp['AUTO_copq'] = float(r[2])  
                    tmp['AA_copq_target'] = float(r[3])
                    tmp['AUTO_copq_target'] = float(r[4])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        AA_copq_accumulation = AA_copq_accumulation + float(r[1])
                        AUTO_copq_accumulation = AUTO_copq_accumulation + float(r[2])
                    else :
                        AA_copq_accumulation = 0
                        AUTO_copq_accumulation = 0
                    AA_copq_target_accumulation = AA_copq_target_accumulation + float(r[3])
                    AUTO_copq_target_accumulation = AUTO_copq_target_accumulation + float(r[4])  

                    tmp['AA_copq'] = AA_copq_accumulation  
                    tmp['AUTO_copq'] = AUTO_copq_accumulation 
                    tmp['AA_copq_target'] = AA_copq_target_accumulation
                    tmp['AUTO_copq_target'] = AUTO_copq_target_accumulation
                tmp['m2copq'] = r[5]        
                tmp['m2copq_target'] = r[6]  
                tmp['provision'] = r[7]        
                tmp['purge'] = r[8]
                tmp['mcr'] = r[9]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    elif app == 'ITI BU' : #"'IAVM','MNT','NB'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'IAVM', copq, NULL)),GROUP_CONCAT(if(app = 'MNT', copq, NULL)),GROUP_CONCAT(if(app = 'NB', copq, NULL)), \
        GROUP_CONCAT(if(app = 'IAVM', copq_target, NULL)),GROUP_CONCAT(if(app = 'MNT', copq_target, NULL)),GROUP_CONCAT(if(app = 'NB', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2022 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2022 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('IAVM','MNT','NB') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            IAVM_copq_accumulation = 0
            MNT_copq_accumulation = 0
            NB_copq_accumulation = 0

            IAVM_copq_target_accumulation = 0
            MNT_copq_target_accumulation = 0    
            NB_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2021實績' or yearmonth == '2022改善前':
                    tmp['IAVM_copq'] = float(r[1])
                    tmp['MNT_copq'] = float(r[2]) 
                    tmp['NB_copq'] = float(r[3]) 
                    tmp['IAVM_copq_target'] = float(r[4])
                    tmp['MNT_copq_target'] = float(r[5])
                    tmp['NB_copq_target'] = float(r[6])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        IAVM_copq_accumulation = IAVM_copq_accumulation + float(r[1])
                        MNT_copq_accumulation = MNT_copq_accumulation + float(r[2])
                        NB_copq_accumulation = NB_copq_accumulation + float(r[3])
                    else :
                        IAVM_copq_accumulation = 0
                        MNT_copq_accumulation = 0
                        NB_copq_accumulation = 0
                    IAVM_copq_target_accumulation = IAVM_copq_target_accumulation + float(r[4])
                    MNT_copq_target_accumulation = MNT_copq_target_accumulation + float(r[5])  
                    NB_copq_target_accumulation = NB_copq_target_accumulation + float(r[6])  

                    tmp['IAVM_copq'] = IAVM_copq_accumulation  
                    tmp['MNT_copq'] = MNT_copq_accumulation 
                    tmp['NB_copq'] = NB_copq_accumulation 
                    tmp['IAVM_copq_target'] = IAVM_copq_target_accumulation
                    tmp['MNT_copq_target'] = MNT_copq_target_accumulation
                    tmp['NB_copq_target'] = NB_copq_target_accumulation
                tmp['m2copq'] = r[7]        
                tmp['m2copq_target'] = r[8]
                tmp['provision'] = r[9]        
                tmp['purge'] = r[10]
                tmp['mcr'] = r[11]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳

    elif app == 'MD BU' : #"'CE','MP','TABLET'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'CE', copq, NULL)),GROUP_CONCAT(if(app = 'MP', copq, NULL)),GROUP_CONCAT(if(app = 'TABLET', copq, NULL)), \
        GROUP_CONCAT(if(app = 'CE', copq_target, NULL)),GROUP_CONCAT(if(app = 'MP', copq_target, NULL)),GROUP_CONCAT(if(app = 'TABLET', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2022 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2022 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('CE','MP','TABLET') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            CE_copq_accumulation = 0
            MP_copq_accumulation = 0
            TABLET_copq_accumulation = 0

            CE_copq_target_accumulation = 0
            MP_copq_target_accumulation = 0    
            TABLET_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2021實績' or yearmonth == '2022改善前':
                    tmp['CE_copq'] = float(r[1])
                    tmp['MP_copq'] = float(r[2]) 
                    tmp['TABLET_copq'] = float(r[3]) 
                    tmp['CE_copq_target'] = float(r[4])
                    tmp['MP_copq_target'] = float(r[5])
                    tmp['TABLET_copq_target'] = float(r[6])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        CE_copq_accumulation = CE_copq_accumulation + float(r[1])
                        MP_copq_accumulation = MP_copq_accumulation + float(r[2])
                        TABLET_copq_accumulation = TABLET_copq_accumulation + float(r[3])
                    else :
                        CE_copq_accumulation = 0
                        MP_copq_accumulation = 0
                        TABLET_copq_accumulation = 0
                    CE_copq_target_accumulation = CE_copq_target_accumulation + float(r[4])
                    MP_copq_target_accumulation = MP_copq_target_accumulation + float(r[5])  
                    TABLET_copq_target_accumulation = TABLET_copq_target_accumulation + float(r[6])  

                    tmp['CE_copq'] = CE_copq_accumulation  
                    tmp['MP_copq'] = MP_copq_accumulation 
                    tmp['TABLET_copq'] = TABLET_copq_accumulation 
                    tmp['CE_copq_target'] = CE_copq_target_accumulation
                    tmp['MP_copq_target'] = MP_copq_target_accumulation
                    tmp['TABLET_copq_target'] = TABLET_copq_target_accumulation
                tmp['m2copq'] = r[7]        
                tmp['m2copq_target'] = r[8]  
                tmp['provision'] = r[9]        
                tmp['purge'] = r[10]
                tmp['mcr'] = r[11]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    elif app == 'TV BU' : #"'TV','TV (SET)'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'TV', copq, NULL)),GROUP_CONCAT(if(app = 'TV (SET)', copq, NULL)), \
        GROUP_CONCAT(if(app = 'TV', copq_target, NULL)),GROUP_CONCAT(if(app = 'TV (SET)', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2022 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2022 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('TV','TV (SET)') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            TV_copq_accumulation = 0
            TV_SET_copq_accumulation = 0

            TV_copq_target_accumulation = 0
            TV_SET_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2021實績' or yearmonth == '2022改善前':
                    tmp['TV_copq'] = float(r[1])
                    tmp['TV_SET_copq'] = float(r[2])  
                    tmp['TV_copq_target'] = float(r[3])
                    tmp['TV_SET_copq_target'] = float(r[4])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        TV_copq_accumulation = TV_copq_accumulation + float(r[1])
                        TV_SET_copq_accumulation = TV_SET_copq_accumulation + float(r[2])
                    else :
                        TV_copq_accumulation = 0
                        TV_SET_copq_accumulation = 0
                    TV_copq_target_accumulation = TV_copq_target_accumulation + float(r[3])
                    TV_SET_copq_target_accumulation = TV_SET_copq_target_accumulation + float(r[4])  

                    tmp['TV_copq'] = TV_copq_accumulation  
                    tmp['TV_SET_copq'] = TV_SET_copq_accumulation 
                    tmp['TV_copq_target'] = TV_copq_target_accumulation
                    tmp['TV_SET_copq_target'] = TV_SET_copq_target_accumulation
                tmp['m2copq'] = r[5]        
                tmp['m2copq_target'] = r[6] 
                tmp['provision'] = r[7]        
                tmp['purge'] = r[8]
                tmp['mcr'] = r[9]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
    
    else : # app類
        cur.execute("select yearmonth,copq,copq_target,m2copq,m2copq_target,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2022 where app=%s and (yearmonthLog=%s or yearmonthLog is NULL)",(app,yearmonthLog))
        copq_accumulation = 0
        copq_target_accumulation = 0
        if cur.rowcount > 2 :
            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2021實績' or yearmonth == '2022改善前':
                    tmp['copq'] = float(r[1])
                    tmp['copq_target'] = float(r[2])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 :
                        copq_accumulation = copq_accumulation + float(r[1])
                    else :
                        copq_accumulation = 0
                    copq_target_accumulation = copq_target_accumulation + float(r[2])

                    tmp['copq'] = copq_accumulation  
                    tmp['copq_target'] = copq_target_accumulation
                tmp['m2copq'] = r[3]        
                tmp['m2copq_target'] = r[4]  
                tmp['provision'] = r[5]        
                tmp['purge'] = r[6]
                tmp['mcr'] = r[7]

                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    # 20200723 增加commentType 均銘 
    # comment
    if commentType == 'act' :
        cur.execute("select comment from rma.copq_comment_actachievement where app=%s and yearmonth=%s order by id desc limit 1",(app,yearmonthLog))
    elif commentType == 'xy' :
        cur.execute("select comment from rma.copq_comment_xy where yearmonth=%s order by id desc limit 1",(yearmonthLog))
        
    if cur.rowcount > 0 and '202212' in returnData :
        tmp = returnData['202212']; 
        for r in cur :
            tmp['comment'] = r[0]
        returnData['202212'] = tmp
    
    # 20200720 燈圖    
    print(returnData)
    #print('==================================')
    
    cur.execute("select app,handtype from copq_handtype where yearmonth=%s",(yearmonthLog))
    if cur.rowcount > 0 :
        for r in cur : 
            print(r)
            returnData['202212'][r[0]] = r[1]            
    else : # 還沒設本月燈圖
        returnData['202212'][r[0]] = 0;
        
    response = jsonify(returnData)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response 


##20221103 光庭需求，增加cell
@app.route("/getAccumulation_act_cell_2022", methods=['GET','POST'])
def getAccumulation_act_cell_2022():
    conn = pymysql.connect(host=host, port=port,user=user, passwd=passwd, db=db)
    cur = conn.cursor() 
    if request.method == 'POST':
        app = request.form.get('app');
        yearmonthLog = request.form.get('yearmonth');
        commentType = request.form.get('commentType'); #20200723 區別act/xy的comment
    else :	
        app = request.args.get('app');
        yearmonthLog = request.args.get('yearmonth');
        commentType = request.args.get('commentType'); #20200723 區別act/xy的comment
    #yearmonthLog='202201'    
    print('request.method:',request.method,' app:', app,' yearmonthLog:',yearmonthLog,' commentType:',commentType)
    
    returnData = OrderedDict();   
    
    # 20200602 增加 provision, purge
    # 20200702 增加 yearmonthLog條件，提供每月歷史資料查詢
    # 20200810 增加 mcr
    if app == 'OVERALL' : ####################################################################################                
        
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'AA BU', copq, NULL)), GROUP_CONCAT(if(app = 'ITI BU', copq, NULL)), \
        GROUP_CONCAT(if(app = 'MD BU', copq, NULL)), GROUP_CONCAT(if(app = 'TV BU', copq, NULL)), \
        GROUP_CONCAT(if(app = 'AA BU', copq_target, NULL)), GROUP_CONCAT(if(app = 'ITI BU', copq_target, NULL)), \
        GROUP_CONCAT(if(app = 'MD BU', copq_target, NULL)), GROUP_CONCAT(if(app = 'TV BU', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr from rma.copq_accumulation_actachievement_cell_2022 a \
        left join (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_cell_2022 \
        where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth where app in ('AA BU','ITI BU','MD BU','TV BU') \
        and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app")
        if cur.rowcount > 2 :
            AA_BU_copq_accumulation = 0
            ITI_BU_copq_accumulation = 0
            MD_BU_copq_accumulation = 0
            TV_BU_copq_accumulation = 0

            AA_BU_copq_target_accumulation = 0
            ITI_BU_copq_target_accumulation = 0
            MD_BU_copq_target_accumulation = 0
            TV_BU_copq_target_accumulation = 0
            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2021實績' or yearmonth == '2022改善前':
                    tmp['AA BU_copq'] = float(r[1])
                    tmp['ITI BU_copq'] = float(r[2])  
                    tmp['MD BU_copq'] = float(r[3])  
                    tmp['TV BU_copq'] = float(r[4]) 
                    tmp['AA BU_copq_target'] = float(r[5])
                    tmp['ITI BU_copq_target'] = float(r[6])
                    tmp['MD BU_copq_target'] = float(r[7])  
                    tmp['TV BU_copq_target'] = float(r[8])
                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        AA_BU_copq_accumulation = AA_BU_copq_accumulation + float(r[1])
                        ITI_BU_copq_accumulation = ITI_BU_copq_accumulation + float(r[2])
                        MD_BU_copq_accumulation = MD_BU_copq_accumulation + float(r[3])
                        TV_BU_copq_accumulation = TV_BU_copq_accumulation + float(r[4]) 
                    else :
                        AA_BU_copq_accumulation = 0
                        ITI_BU_copq_accumulation = 0
                        MD_BU_copq_accumulation = 0
                        TV_BU_copq_accumulation = 0
                    AA_BU_copq_target_accumulation = AA_BU_copq_target_accumulation + float(r[5])
                    ITI_BU_copq_target_accumulation = ITI_BU_copq_target_accumulation + float(r[6])  
                    MD_BU_copq_target_accumulation = MD_BU_copq_target_accumulation + float(r[7])
                    TV_BU_copq_target_accumulation = TV_BU_copq_target_accumulation + float(r[8])

                    tmp['AA BU_copq'] = AA_BU_copq_accumulation
                    tmp['ITI BU_copq'] = ITI_BU_copq_accumulation  
                    tmp['MD BU_copq'] = MD_BU_copq_accumulation  
                    tmp['TV BU_copq'] = TV_BU_copq_accumulation 
                    tmp['AA BU_copq_target'] = AA_BU_copq_target_accumulation
                    tmp['ITI BU_copq_target'] = ITI_BU_copq_target_accumulation
                    tmp['MD BU_copq_target'] = MD_BU_copq_target_accumulation  
                    tmp['TV BU_copq_target'] = TV_BU_copq_target_accumulation
                tmp['m2copq'] = r[9]        
                tmp['m2copq_target'] = r[10]  

                tmp['provision'] = r[11]        
                tmp['purge'] = r[12]
                tmp['mcr'] = r[13]
                returnData[yearmonth] = tmp
        else :
            returnData[0] = 0 #無資料回傳
            
    elif app == 'AA BU' : #"'AA','AUTO'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'AA', copq, NULL)),GROUP_CONCAT(if(app = 'AUTO', copq, NULL)), \
        GROUP_CONCAT(if(app = 'AA', copq_target, NULL)),GROUP_CONCAT(if(app = 'AUTO', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_cell_2022 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_cell_2022 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('AA','AUTO') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            AA_copq_accumulation = 0
            AUTO_copq_accumulation = 0

            AA_copq_target_accumulation = 0
            AUTO_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2021實績' or yearmonth == '2022改善前':
                    tmp['AA_copq'] = float(r[1])
                    tmp['AUTO_copq'] = float(r[2])  
                    tmp['AA_copq_target'] = float(r[3])
                    tmp['AUTO_copq_target'] = float(r[4])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        AA_copq_accumulation = AA_copq_accumulation + float(r[1])
                        AUTO_copq_accumulation = AUTO_copq_accumulation + float(r[2])
                    else :
                        AA_copq_accumulation = 0
                        AUTO_copq_accumulation = 0
                    AA_copq_target_accumulation = AA_copq_target_accumulation + float(r[3])
                    AUTO_copq_target_accumulation = AUTO_copq_target_accumulation + float(r[4])  

                    tmp['AA_copq'] = AA_copq_accumulation  
                    tmp['AUTO_copq'] = AUTO_copq_accumulation 
                    tmp['AA_copq_target'] = AA_copq_target_accumulation
                    tmp['AUTO_copq_target'] = AUTO_copq_target_accumulation
                tmp['m2copq'] = r[5]        
                tmp['m2copq_target'] = r[6]  
                tmp['provision'] = r[7]        
                tmp['purge'] = r[8]
                tmp['mcr'] = r[9]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    elif app == 'ITI BU' : #"'IAVM','MNT','NB'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'IAVM', copq, NULL)),GROUP_CONCAT(if(app = 'MNT', copq, NULL)),GROUP_CONCAT(if(app = 'NB', copq, NULL)), \
        GROUP_CONCAT(if(app = 'IAVM', copq_target, NULL)),GROUP_CONCAT(if(app = 'MNT', copq_target, NULL)),GROUP_CONCAT(if(app = 'NB', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_cell_2022 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_cell_2022 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('IAVM','MNT','NB') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            IAVM_copq_accumulation = 0
            MNT_copq_accumulation = 0
            NB_copq_accumulation = 0

            IAVM_copq_target_accumulation = 0
            MNT_copq_target_accumulation = 0    
            NB_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2021實績' or yearmonth == '2022改善前':
                    tmp['IAVM_copq'] = float(r[1])
                    tmp['MNT_copq'] = float(r[2]) 
                    tmp['NB_copq'] = float(r[3]) 
                    tmp['IAVM_copq_target'] = float(r[4])
                    tmp['MNT_copq_target'] = float(r[5])
                    tmp['NB_copq_target'] = float(r[6])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        IAVM_copq_accumulation = IAVM_copq_accumulation + float(r[1])
                        MNT_copq_accumulation = MNT_copq_accumulation + float(r[2])
                        NB_copq_accumulation = NB_copq_accumulation + float(r[3])
                    else :
                        IAVM_copq_accumulation = 0
                        MNT_copq_accumulation = 0
                        NB_copq_accumulation = 0
                    IAVM_copq_target_accumulation = IAVM_copq_target_accumulation + float(r[4])
                    MNT_copq_target_accumulation = MNT_copq_target_accumulation + float(r[5])  
                    NB_copq_target_accumulation = NB_copq_target_accumulation + float(r[6])  

                    tmp['IAVM_copq'] = IAVM_copq_accumulation  
                    tmp['MNT_copq'] = MNT_copq_accumulation 
                    tmp['NB_copq'] = NB_copq_accumulation 
                    tmp['IAVM_copq_target'] = IAVM_copq_target_accumulation
                    tmp['MNT_copq_target'] = MNT_copq_target_accumulation
                    tmp['NB_copq_target'] = NB_copq_target_accumulation
                tmp['m2copq'] = r[7]        
                tmp['m2copq_target'] = r[8]
                tmp['provision'] = r[9]        
                tmp['purge'] = r[10]
                tmp['mcr'] = r[11]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳

    elif app == 'MD BU' : #"'CE','MP','TABLET'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'CE', copq, NULL)),GROUP_CONCAT(if(app = 'MP', copq, NULL)),GROUP_CONCAT(if(app = 'TABLET', copq, NULL)), \
        GROUP_CONCAT(if(app = 'CE', copq_target, NULL)),GROUP_CONCAT(if(app = 'MP', copq_target, NULL)),GROUP_CONCAT(if(app = 'TABLET', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_cell_2022 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_cell_2022 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('CE','MP','TABLET') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            CE_copq_accumulation = 0
            MP_copq_accumulation = 0
            TABLET_copq_accumulation = 0

            CE_copq_target_accumulation = 0
            MP_copq_target_accumulation = 0    
            TABLET_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2021實績' or yearmonth == '2022改善前':
                    tmp['CE_copq'] = float(r[1])
                    tmp['MP_copq'] = float(r[2]) 
                    tmp['TABLET_copq'] = float(r[3]) 
                    tmp['CE_copq_target'] = float(r[4])
                    tmp['MP_copq_target'] = float(r[5])
                    tmp['TABLET_copq_target'] = float(r[6])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        CE_copq_accumulation = CE_copq_accumulation + float(r[1])
                        MP_copq_accumulation = MP_copq_accumulation + float(r[2])
                        TABLET_copq_accumulation = TABLET_copq_accumulation + float(r[3])
                    else :
                        CE_copq_accumulation = 0
                        MP_copq_accumulation = 0
                        TABLET_copq_accumulation = 0
                    CE_copq_target_accumulation = CE_copq_target_accumulation + float(r[4])
                    MP_copq_target_accumulation = MP_copq_target_accumulation + float(r[5])  
                    TABLET_copq_target_accumulation = TABLET_copq_target_accumulation + float(r[6])  

                    tmp['CE_copq'] = CE_copq_accumulation  
                    tmp['MP_copq'] = MP_copq_accumulation 
                    tmp['TABLET_copq'] = TABLET_copq_accumulation 
                    tmp['CE_copq_target'] = CE_copq_target_accumulation
                    tmp['MP_copq_target'] = MP_copq_target_accumulation
                    tmp['TABLET_copq_target'] = TABLET_copq_target_accumulation
                tmp['m2copq'] = r[7]        
                tmp['m2copq_target'] = r[8]  
                tmp['provision'] = r[9]        
                tmp['purge'] = r[10]
                tmp['mcr'] = r[11]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    elif app == 'TV BU' : #"'TV','TV (SET)'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'TV', copq, NULL)),GROUP_CONCAT(if(app = 'TV (SET)', copq, NULL)), \
        GROUP_CONCAT(if(app = 'TV', copq_target, NULL)),GROUP_CONCAT(if(app = 'TV (SET)', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_cell_2022 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_cell_2022 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('TV','TV (SET)') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            TV_copq_accumulation = 0
            TV_SET_copq_accumulation = 0

            TV_copq_target_accumulation = 0
            TV_SET_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2021實績' or yearmonth == '2022改善前':
                    tmp['TV_copq'] = float(r[1])
                    tmp['TV_SET_copq'] = float(r[2])  
                    tmp['TV_copq_target'] = float(r[3])
                    tmp['TV_SET_copq_target'] = float(r[4])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        TV_copq_accumulation = TV_copq_accumulation + float(r[1])
                        TV_SET_copq_accumulation = TV_SET_copq_accumulation + float(r[2])
                    else :
                        TV_copq_accumulation = 0
                        TV_SET_copq_accumulation = 0
                    TV_copq_target_accumulation = TV_copq_target_accumulation + float(r[3])
                    TV_SET_copq_target_accumulation = TV_SET_copq_target_accumulation + float(r[4])  

                    tmp['TV_copq'] = TV_copq_accumulation  
                    tmp['TV_SET_copq'] = TV_SET_copq_accumulation 
                    tmp['TV_copq_target'] = TV_copq_target_accumulation
                    tmp['TV_SET_copq_target'] = TV_SET_copq_target_accumulation
                tmp['m2copq'] = r[5]        
                tmp['m2copq_target'] = r[6] 
                tmp['provision'] = r[7]        
                tmp['purge'] = r[8]
                tmp['mcr'] = r[9]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
    
    else : # app類
        cur.execute("select yearmonth,copq,copq_target,m2copq,m2copq_target,provision,`purge`,mcr from rma.copq_accumulation_actachievement_cell_2022 where app=%s and (yearmonthLog=%s or yearmonthLog is NULL)",(app,yearmonthLog))
        copq_accumulation = 0
        copq_target_accumulation = 0
        if cur.rowcount > 2 :
            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2021實績' or yearmonth == '2022改善前':
                    tmp['copq'] = float(r[1])
                    tmp['copq_target'] = float(r[2])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 :
                        copq_accumulation = copq_accumulation + float(r[1])
                    else :
                        copq_accumulation = 0
                    copq_target_accumulation = copq_target_accumulation + float(r[2])

                    tmp['copq'] = copq_accumulation  
                    tmp['copq_target'] = copq_target_accumulation
                tmp['m2copq'] = r[3]        
                tmp['m2copq_target'] = r[4]  
                tmp['provision'] = r[5]        
                tmp['purge'] = r[6]
                tmp['mcr'] = r[7]

                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    # 20200723 增加commentType 均銘 
    # comment
    if commentType == 'act' :
        cur.execute("select comment from rma.copq_comment_actachievement where app=%s and yearmonth=%s order by id desc limit 1",(app,yearmonthLog))
    elif commentType == 'xy' :
        cur.execute("select comment from rma.copq_comment_xy where yearmonth=%s order by id desc limit 1",(yearmonthLog))
        
    if cur.rowcount > 0 and '202212' in returnData :
        tmp = returnData['202212']; 
        for r in cur :
            tmp['comment'] = r[0]
        returnData['202212'] = tmp
    
    # 20200720 燈圖    
    print(returnData)
    #print('==================================')
    
    cur.execute("select app,handtype from copq_handtype where yearmonth=%s",(yearmonthLog))
    if cur.rowcount > 0 :
        for r in cur : 
            print(r)
            returnData['202212'][r[0]] = r[1]            
    else : # 還沒設本月燈圖
        returnData['202212'][r[0]] = 0;
        
    response = jsonify(returnData)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response 

##20230208
@app.route("/getAccumulation_act_2023", methods=['GET','POST'])
def getAccumulation_act_2023():
    conn = pymysql.connect(host=host, port=port,user=user, passwd=passwd, db=db)
    cur = conn.cursor() 
    if request.method == 'POST':
        app = request.form.get('app');
        yearmonthLog = request.form.get('yearmonth');
        commentType = request.form.get('commentType'); #20200723 區別act/xy的comment
    else :	
        app = request.args.get('app');
        yearmonthLog = request.args.get('yearmonth');
        commentType = request.args.get('commentType'); #20200723 區別act/xy的comment
    #yearmonthLog='202201'    
    print('request.method:',request.method,' app:', app,' yearmonthLog:',yearmonthLog,' commentType:',commentType)
    
    returnData = OrderedDict();   
    
    # 20200602 增加 provision, purge
    # 20200702 增加 yearmonthLog條件，提供每月歷史資料查詢
    # 20200810 增加 mcr
    if app == 'OVERALL' : ####################################################################################                
        
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'AA BU', copq, NULL)), GROUP_CONCAT(if(app = 'ITI BU', copq, NULL)), \
        GROUP_CONCAT(if(app = 'MD BU', copq, NULL)), GROUP_CONCAT(if(app = 'TV BU', copq, NULL)), \
        GROUP_CONCAT(if(app = 'AA BU', copq_target, NULL)), GROUP_CONCAT(if(app = 'ITI BU', copq_target, NULL)), \
        GROUP_CONCAT(if(app = 'MD BU', copq_target, NULL)), GROUP_CONCAT(if(app = 'TV BU', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr from rma.copq_accumulation_actachievement_2023 a \
        left join (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2023 \
        where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth where app in ('AA BU','ITI BU','MD BU','TV BU') \
        and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app")
        if cur.rowcount > 2 :
            AA_BU_copq_accumulation = 0
            ITI_BU_copq_accumulation = 0
            MD_BU_copq_accumulation = 0
            TV_BU_copq_accumulation = 0

            AA_BU_copq_target_accumulation = 0
            ITI_BU_copq_target_accumulation = 0
            MD_BU_copq_target_accumulation = 0
            TV_BU_copq_target_accumulation = 0
            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['AA BU_copq'] = float(r[1])
                    tmp['ITI BU_copq'] = float(r[2])  
                    tmp['MD BU_copq'] = float(r[3])  
                    tmp['TV BU_copq'] = float(r[4]) 
                    tmp['AA BU_copq_target'] = float(r[5])
                    tmp['ITI BU_copq_target'] = float(r[6])
                    tmp['MD BU_copq_target'] = float(r[7])  
                    tmp['TV BU_copq_target'] = float(r[8])
                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        AA_BU_copq_accumulation = AA_BU_copq_accumulation + float(r[1])
                        ITI_BU_copq_accumulation = ITI_BU_copq_accumulation + float(r[2])
                        MD_BU_copq_accumulation = MD_BU_copq_accumulation + float(r[3])
                        TV_BU_copq_accumulation = TV_BU_copq_accumulation + float(r[4]) 
                    else :
                        AA_BU_copq_accumulation = 0
                        ITI_BU_copq_accumulation = 0
                        MD_BU_copq_accumulation = 0
                        TV_BU_copq_accumulation = 0
                    AA_BU_copq_target_accumulation = AA_BU_copq_target_accumulation + float(r[5])
                    ITI_BU_copq_target_accumulation = ITI_BU_copq_target_accumulation + float(r[6])  
                    MD_BU_copq_target_accumulation = MD_BU_copq_target_accumulation + float(r[7])
                    TV_BU_copq_target_accumulation = TV_BU_copq_target_accumulation + float(r[8])

                    tmp['AA BU_copq'] = AA_BU_copq_accumulation
                    tmp['ITI BU_copq'] = ITI_BU_copq_accumulation  
                    tmp['MD BU_copq'] = MD_BU_copq_accumulation  
                    tmp['TV BU_copq'] = TV_BU_copq_accumulation 
                    tmp['AA BU_copq_target'] = AA_BU_copq_target_accumulation
                    tmp['ITI BU_copq_target'] = ITI_BU_copq_target_accumulation
                    tmp['MD BU_copq_target'] = MD_BU_copq_target_accumulation  
                    tmp['TV BU_copq_target'] = TV_BU_copq_target_accumulation
                tmp['m2copq'] = r[9]        
                tmp['m2copq_target'] = r[10]  

                tmp['provision'] = r[11]        
                tmp['purge'] = r[12]
                tmp['mcr'] = r[13]
                returnData[yearmonth] = tmp
        else :
            returnData[0] = 0 #無資料回傳
            
    elif app == 'AA BU' : #"'AA','AUTO'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'AA', copq, NULL)),GROUP_CONCAT(if(app = 'AUTO', copq, NULL)), \
        GROUP_CONCAT(if(app = 'AA', copq_target, NULL)),GROUP_CONCAT(if(app = 'AUTO', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2023 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2023 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('AA','AUTO') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            AA_copq_accumulation = 0
            AUTO_copq_accumulation = 0

            AA_copq_target_accumulation = 0
            AUTO_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['AA_copq'] = float(r[1])
                    tmp['AUTO_copq'] = float(r[2])  
                    tmp['AA_copq_target'] = float(r[3])
                    tmp['AUTO_copq_target'] = float(r[4])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        AA_copq_accumulation = AA_copq_accumulation + float(r[1])
                        AUTO_copq_accumulation = AUTO_copq_accumulation + float(r[2])
                    else :
                        AA_copq_accumulation = 0
                        AUTO_copq_accumulation = 0
                    AA_copq_target_accumulation = AA_copq_target_accumulation + float(r[3])
                    AUTO_copq_target_accumulation = AUTO_copq_target_accumulation + float(r[4])  

                    tmp['AA_copq'] = AA_copq_accumulation  
                    tmp['AUTO_copq'] = AUTO_copq_accumulation 
                    tmp['AA_copq_target'] = AA_copq_target_accumulation
                    tmp['AUTO_copq_target'] = AUTO_copq_target_accumulation
                tmp['m2copq'] = r[5]        
                tmp['m2copq_target'] = r[6]  
                tmp['provision'] = r[7]        
                tmp['purge'] = r[8]
                tmp['mcr'] = r[9]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    elif app == 'ITI BU' : #"'IAVM','MNT','NB'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'IAVM', copq, NULL)),GROUP_CONCAT(if(app = 'MNT', copq, NULL)),GROUP_CONCAT(if(app = 'NB', copq, NULL)), \
        GROUP_CONCAT(if(app = 'IAVM', copq_target, NULL)),GROUP_CONCAT(if(app = 'MNT', copq_target, NULL)),GROUP_CONCAT(if(app = 'NB', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2023 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2023 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('IAVM','MNT','NB') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            IAVM_copq_accumulation = 0
            MNT_copq_accumulation = 0
            NB_copq_accumulation = 0

            IAVM_copq_target_accumulation = 0
            MNT_copq_target_accumulation = 0    
            NB_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['IAVM_copq'] = float(r[1])
                    tmp['MNT_copq'] = float(r[2]) 
                    tmp['NB_copq'] = float(r[3]) 
                    tmp['IAVM_copq_target'] = float(r[4])
                    tmp['MNT_copq_target'] = float(r[5])
                    tmp['NB_copq_target'] = float(r[6])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        IAVM_copq_accumulation = IAVM_copq_accumulation + float(r[1])
                        MNT_copq_accumulation = MNT_copq_accumulation + float(r[2])
                        NB_copq_accumulation = NB_copq_accumulation + float(r[3])
                    else :
                        IAVM_copq_accumulation = 0
                        MNT_copq_accumulation = 0
                        NB_copq_accumulation = 0
                    IAVM_copq_target_accumulation = IAVM_copq_target_accumulation + float(r[4])
                    MNT_copq_target_accumulation = MNT_copq_target_accumulation + float(r[5])  
                    NB_copq_target_accumulation = NB_copq_target_accumulation + float(r[6])  

                    tmp['IAVM_copq'] = IAVM_copq_accumulation  
                    tmp['MNT_copq'] = MNT_copq_accumulation 
                    tmp['NB_copq'] = NB_copq_accumulation 
                    tmp['IAVM_copq_target'] = IAVM_copq_target_accumulation
                    tmp['MNT_copq_target'] = MNT_copq_target_accumulation
                    tmp['NB_copq_target'] = NB_copq_target_accumulation
                tmp['m2copq'] = r[7]        
                tmp['m2copq_target'] = r[8]
                tmp['provision'] = r[9]        
                tmp['purge'] = r[10]
                tmp['mcr'] = r[11]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳

    elif app == 'MD BU' : #"'CE','MP','TABLET'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'CE', copq, NULL)),GROUP_CONCAT(if(app = 'MP', copq, NULL)),GROUP_CONCAT(if(app = 'TABLET', copq, NULL)), \
        GROUP_CONCAT(if(app = 'CE', copq_target, NULL)),GROUP_CONCAT(if(app = 'MP', copq_target, NULL)),GROUP_CONCAT(if(app = 'TABLET', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2023 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2023 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('CE','MP','TABLET') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            CE_copq_accumulation = 0
            MP_copq_accumulation = 0
            TABLET_copq_accumulation = 0

            CE_copq_target_accumulation = 0
            MP_copq_target_accumulation = 0    
            TABLET_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['CE_copq'] = float(r[1])
                    tmp['MP_copq'] = float(r[2]) 
                    tmp['TABLET_copq'] = float(r[3]) 
                    tmp['CE_copq_target'] = float(r[4])
                    tmp['MP_copq_target'] = float(r[5])
                    tmp['TABLET_copq_target'] = float(r[6])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        CE_copq_accumulation = CE_copq_accumulation + float(r[1])
                        MP_copq_accumulation = MP_copq_accumulation + float(r[2])
                        TABLET_copq_accumulation = TABLET_copq_accumulation + float(r[3])
                    else :
                        CE_copq_accumulation = 0
                        MP_copq_accumulation = 0
                        TABLET_copq_accumulation = 0
                    CE_copq_target_accumulation = CE_copq_target_accumulation + float(r[4])
                    MP_copq_target_accumulation = MP_copq_target_accumulation + float(r[5])  
                    TABLET_copq_target_accumulation = TABLET_copq_target_accumulation + float(r[6])  

                    tmp['CE_copq'] = CE_copq_accumulation  
                    tmp['MP_copq'] = MP_copq_accumulation 
                    tmp['TABLET_copq'] = TABLET_copq_accumulation 
                    tmp['CE_copq_target'] = CE_copq_target_accumulation
                    tmp['MP_copq_target'] = MP_copq_target_accumulation
                    tmp['TABLET_copq_target'] = TABLET_copq_target_accumulation
                tmp['m2copq'] = r[7]        
                tmp['m2copq_target'] = r[8]  
                tmp['provision'] = r[9]        
                tmp['purge'] = r[10]
                tmp['mcr'] = r[11]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    elif app == 'TV BU' : #"'TV','TV (SET)'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'TV', copq, NULL)),GROUP_CONCAT(if(app = 'TV (SET)', copq, NULL)), \
        GROUP_CONCAT(if(app = 'TV', copq_target, NULL)),GROUP_CONCAT(if(app = 'TV (SET)', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_2023 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2023 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('TV','TV (SET)') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            TV_copq_accumulation = 0
            TV_SET_copq_accumulation = 0

            TV_copq_target_accumulation = 0
            TV_SET_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['TV_copq'] = float(r[1])
                    tmp['TV_SET_copq'] = float(r[2])  
                    tmp['TV_copq_target'] = float(r[3])
                    tmp['TV_SET_copq_target'] = float(r[4])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        TV_copq_accumulation = TV_copq_accumulation + float(r[1])
                        TV_SET_copq_accumulation = TV_SET_copq_accumulation + float(r[2])
                    else :
                        TV_copq_accumulation = 0
                        TV_SET_copq_accumulation = 0
                    TV_copq_target_accumulation = TV_copq_target_accumulation + float(r[3])
                    TV_SET_copq_target_accumulation = TV_SET_copq_target_accumulation + float(r[4])  

                    tmp['TV_copq'] = TV_copq_accumulation  
                    tmp['TV_SET_copq'] = TV_SET_copq_accumulation 
                    tmp['TV_copq_target'] = TV_copq_target_accumulation
                    tmp['TV_SET_copq_target'] = TV_SET_copq_target_accumulation
                tmp['m2copq'] = r[5]        
                tmp['m2copq_target'] = r[6] 
                tmp['provision'] = r[7]        
                tmp['purge'] = r[8]
                tmp['mcr'] = r[9]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
    
    else : # app類
        cur.execute("select yearmonth,copq,copq_target,m2copq,m2copq_target,provision,`purge`,mcr from rma.copq_accumulation_actachievement_2023 where app=%s and (yearmonthLog=%s or yearmonthLog is NULL)",(app,yearmonthLog))
        copq_accumulation = 0
        copq_target_accumulation = 0
        if cur.rowcount > 2 :
            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['copq'] = float(r[1])
                    tmp['copq_target'] = float(r[2])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 :
                        copq_accumulation = copq_accumulation + float(r[1])
                    else :
                        copq_accumulation = 0
                    copq_target_accumulation = copq_target_accumulation + float(r[2])

                    tmp['copq'] = copq_accumulation  
                    tmp['copq_target'] = copq_target_accumulation
                tmp['m2copq'] = r[3]        
                tmp['m2copq_target'] = r[4]  
                tmp['provision'] = r[5]        
                tmp['purge'] = r[6]
                tmp['mcr'] = r[7]

                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    # 20200723 增加commentType 均銘 
    # comment
    if commentType == 'act' :
        cur.execute("select comment from rma.copq_comment_actachievement where app=%s and yearmonth=%s order by id desc limit 1",(app,yearmonthLog))
    elif commentType == 'xy' :
        cur.execute("select comment from rma.copq_comment_xy where yearmonth=%s order by id desc limit 1",(yearmonthLog))
        
    if cur.rowcount > 0 and '202312' in returnData :
        tmp = returnData['202312']; 
        for r in cur :
            tmp['comment'] = r[0]
        returnData['202312'] = tmp
    
    # 20200720 燈圖    
    print(returnData)
    #print('==================================')
    
    cur.execute("select app,handtype from copq_handtype where yearmonth=%s",(yearmonthLog))
    if cur.rowcount > 0 :
        for r in cur : 
            print(r)
            returnData['202312'][r[0]] = r[1]            
    else : # 還沒設本月燈圖
        returnData['202312'][r[0]] = 0;
        
    response = jsonify(returnData)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response 


##20230208  
@app.route("/getAccumulation_act_cell_2023", methods=['GET','POST'])
def getAccumulation_act_cell_2023():
    conn = pymysql.connect(host=host, port=port,user=user, passwd=passwd, db=db)
    cur = conn.cursor() 
    if request.method == 'POST':
        app = request.form.get('app');
        yearmonthLog = request.form.get('yearmonth');
        commentType = request.form.get('commentType'); #20200723 區別act/xy的comment
    else :	
        app = request.args.get('app');
        yearmonthLog = request.args.get('yearmonth');
        commentType = request.args.get('commentType'); #20200723 區別act/xy的comment
    print('request.method:',request.method,' app:', app,' yearmonthLog:',yearmonthLog,' commentType:',commentType)
    
    returnData = OrderedDict();   
    
    # 20200602 增加 provision, purge
    # 20200702 增加 yearmonthLog條件，提供每月歷史資料查詢
    # 20200810 增加 mcr
    if app == 'OVERALL' : ####################################################################################                
        
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'AA BU', copq, NULL)), GROUP_CONCAT(if(app = 'ITI BU', copq, NULL)), \
        GROUP_CONCAT(if(app = 'MD BU', copq, NULL)), GROUP_CONCAT(if(app = 'TV BU', copq, NULL)), \
        GROUP_CONCAT(if(app = 'AA BU', copq_target, NULL)), GROUP_CONCAT(if(app = 'ITI BU', copq_target, NULL)), \
        GROUP_CONCAT(if(app = 'MD BU', copq_target, NULL)), GROUP_CONCAT(if(app = 'TV BU', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr from rma.copq_accumulation_actachievement_cell_2023 a \
        left join (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_cell_2023 \
        where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth where app in ('AA BU','ITI BU','MD BU','TV BU') \
        and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app")
        if cur.rowcount > 2 :
            AA_BU_copq_accumulation = 0
            ITI_BU_copq_accumulation = 0
            MD_BU_copq_accumulation = 0
            TV_BU_copq_accumulation = 0

            AA_BU_copq_target_accumulation = 0
            ITI_BU_copq_target_accumulation = 0
            MD_BU_copq_target_accumulation = 0
            TV_BU_copq_target_accumulation = 0
            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['AA BU_copq'] = float(r[1])
                    tmp['ITI BU_copq'] = float(r[2])  
                    tmp['MD BU_copq'] = float(r[3])  
                    tmp['TV BU_copq'] = float(r[4]) 
                    tmp['AA BU_copq_target'] = float(r[5])
                    tmp['ITI BU_copq_target'] = float(r[6])
                    tmp['MD BU_copq_target'] = float(r[7])  
                    tmp['TV BU_copq_target'] = float(r[8])
                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        AA_BU_copq_accumulation = AA_BU_copq_accumulation + float(r[1])
                        ITI_BU_copq_accumulation = ITI_BU_copq_accumulation + float(r[2])
                        MD_BU_copq_accumulation = MD_BU_copq_accumulation + float(r[3])
                        TV_BU_copq_accumulation = TV_BU_copq_accumulation + float(r[4]) 
                    else :
                        AA_BU_copq_accumulation = 0
                        ITI_BU_copq_accumulation = 0
                        MD_BU_copq_accumulation = 0
                        TV_BU_copq_accumulation = 0
                    AA_BU_copq_target_accumulation = AA_BU_copq_target_accumulation + float(r[5])
                    ITI_BU_copq_target_accumulation = ITI_BU_copq_target_accumulation + float(r[6])  
                    MD_BU_copq_target_accumulation = MD_BU_copq_target_accumulation + float(r[7])
                    TV_BU_copq_target_accumulation = TV_BU_copq_target_accumulation + float(r[8])

                    tmp['AA BU_copq'] = AA_BU_copq_accumulation
                    tmp['ITI BU_copq'] = ITI_BU_copq_accumulation  
                    tmp['MD BU_copq'] = MD_BU_copq_accumulation  
                    tmp['TV BU_copq'] = TV_BU_copq_accumulation 
                    tmp['AA BU_copq_target'] = AA_BU_copq_target_accumulation
                    tmp['ITI BU_copq_target'] = ITI_BU_copq_target_accumulation
                    tmp['MD BU_copq_target'] = MD_BU_copq_target_accumulation  
                    tmp['TV BU_copq_target'] = TV_BU_copq_target_accumulation
                tmp['m2copq'] = r[9]        
                tmp['m2copq_target'] = r[10]  

                tmp['provision'] = r[11]        
                tmp['purge'] = r[12]
                tmp['mcr'] = r[13]
                returnData[yearmonth] = tmp
        else :
            returnData[0] = 0 #無資料回傳
            
    elif app == 'AA BU' : #"'AA','AUTO'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'AA', copq, NULL)),GROUP_CONCAT(if(app = 'AUTO', copq, NULL)), \
        GROUP_CONCAT(if(app = 'AA', copq_target, NULL)),GROUP_CONCAT(if(app = 'AUTO', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_cell_2023 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_cell_2023 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('AA','AUTO') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            AA_copq_accumulation = 0
            AUTO_copq_accumulation = 0

            AA_copq_target_accumulation = 0
            AUTO_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['AA_copq'] = float(r[1])
                    tmp['AUTO_copq'] = float(r[2])  
                    tmp['AA_copq_target'] = float(r[3])
                    tmp['AUTO_copq_target'] = float(r[4])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        AA_copq_accumulation = AA_copq_accumulation + float(r[1])
                        AUTO_copq_accumulation = AUTO_copq_accumulation + float(r[2])
                    else :
                        AA_copq_accumulation = 0
                        AUTO_copq_accumulation = 0
                    AA_copq_target_accumulation = AA_copq_target_accumulation + float(r[3])
                    AUTO_copq_target_accumulation = AUTO_copq_target_accumulation + float(r[4])  

                    tmp['AA_copq'] = AA_copq_accumulation  
                    tmp['AUTO_copq'] = AUTO_copq_accumulation 
                    tmp['AA_copq_target'] = AA_copq_target_accumulation
                    tmp['AUTO_copq_target'] = AUTO_copq_target_accumulation
                tmp['m2copq'] = r[5]        
                tmp['m2copq_target'] = r[6]  
                tmp['provision'] = r[7]        
                tmp['purge'] = r[8]
                tmp['mcr'] = r[9]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    elif app == 'ITI BU' : #"'IAVM','MNT','NB'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'IAVM', copq, NULL)),GROUP_CONCAT(if(app = 'MNT', copq, NULL)),GROUP_CONCAT(if(app = 'NB', copq, NULL)), \
        GROUP_CONCAT(if(app = 'IAVM', copq_target, NULL)),GROUP_CONCAT(if(app = 'MNT', copq_target, NULL)),GROUP_CONCAT(if(app = 'NB', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_cell_2023 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_cell_2023 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('IAVM','MNT','NB') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            IAVM_copq_accumulation = 0
            MNT_copq_accumulation = 0
            NB_copq_accumulation = 0

            IAVM_copq_target_accumulation = 0
            MNT_copq_target_accumulation = 0    
            NB_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['IAVM_copq'] = float(r[1])
                    tmp['MNT_copq'] = float(r[2]) 
                    tmp['NB_copq'] = float(r[3]) 
                    tmp['IAVM_copq_target'] = float(r[4])
                    tmp['MNT_copq_target'] = float(r[5])
                    tmp['NB_copq_target'] = float(r[6])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        IAVM_copq_accumulation = IAVM_copq_accumulation + float(r[1])
                        MNT_copq_accumulation = MNT_copq_accumulation + float(r[2])
                        NB_copq_accumulation = NB_copq_accumulation + float(r[3])
                    else :
                        IAVM_copq_accumulation = 0
                        MNT_copq_accumulation = 0
                        NB_copq_accumulation = 0
                    IAVM_copq_target_accumulation = IAVM_copq_target_accumulation + float(r[4])
                    MNT_copq_target_accumulation = MNT_copq_target_accumulation + float(r[5])  
                    NB_copq_target_accumulation = NB_copq_target_accumulation + float(r[6])  

                    tmp['IAVM_copq'] = IAVM_copq_accumulation  
                    tmp['MNT_copq'] = MNT_copq_accumulation 
                    tmp['NB_copq'] = NB_copq_accumulation 
                    tmp['IAVM_copq_target'] = IAVM_copq_target_accumulation
                    tmp['MNT_copq_target'] = MNT_copq_target_accumulation
                    tmp['NB_copq_target'] = NB_copq_target_accumulation
                tmp['m2copq'] = r[7]        
                tmp['m2copq_target'] = r[8]
                tmp['provision'] = r[9]        
                tmp['purge'] = r[10]
                tmp['mcr'] = r[11]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳

    elif app == 'MD BU' : #"'CE','MP','TABLET'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'CE', copq, NULL)),GROUP_CONCAT(if(app = 'MP', copq, NULL)),GROUP_CONCAT(if(app = 'TABLET', copq, NULL)), \
        GROUP_CONCAT(if(app = 'CE', copq_target, NULL)),GROUP_CONCAT(if(app = 'MP', copq_target, NULL)),GROUP_CONCAT(if(app = 'TABLET', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_cell_2023 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_cell_2023 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('CE','MP','TABLET') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            CE_copq_accumulation = 0
            MP_copq_accumulation = 0
            TABLET_copq_accumulation = 0

            CE_copq_target_accumulation = 0
            MP_copq_target_accumulation = 0    
            TABLET_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['CE_copq'] = float(r[1])
                    tmp['MP_copq'] = float(r[2]) 
                    tmp['TABLET_copq'] = float(r[3]) 
                    tmp['CE_copq_target'] = float(r[4])
                    tmp['MP_copq_target'] = float(r[5])
                    tmp['TABLET_copq_target'] = float(r[6])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        CE_copq_accumulation = CE_copq_accumulation + float(r[1])
                        MP_copq_accumulation = MP_copq_accumulation + float(r[2])
                        TABLET_copq_accumulation = TABLET_copq_accumulation + float(r[3])
                    else :
                        CE_copq_accumulation = 0
                        MP_copq_accumulation = 0
                        TABLET_copq_accumulation = 0
                    CE_copq_target_accumulation = CE_copq_target_accumulation + float(r[4])
                    MP_copq_target_accumulation = MP_copq_target_accumulation + float(r[5])  
                    TABLET_copq_target_accumulation = TABLET_copq_target_accumulation + float(r[6])  

                    tmp['CE_copq'] = CE_copq_accumulation  
                    tmp['MP_copq'] = MP_copq_accumulation 
                    tmp['TABLET_copq'] = TABLET_copq_accumulation 
                    tmp['CE_copq_target'] = CE_copq_target_accumulation
                    tmp['MP_copq_target'] = MP_copq_target_accumulation
                    tmp['TABLET_copq_target'] = TABLET_copq_target_accumulation
                tmp['m2copq'] = r[7]        
                tmp['m2copq_target'] = r[8]  
                tmp['provision'] = r[9]        
                tmp['purge'] = r[10]
                tmp['mcr'] = r[11]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    elif app == 'TV BU' : #"'TV','TV (SET)'"###################################################################################
        cur.execute("select a.yearmonth, \
        GROUP_CONCAT(if(app = 'TV', copq, NULL)),GROUP_CONCAT(if(app = 'TV (SET)', copq, NULL)), \
        GROUP_CONCAT(if(app = 'TV', copq_target, NULL)),GROUP_CONCAT(if(app = 'TV (SET)', copq_target, NULL)), \
        b.m2copq,b.m2copq_target,b.provision,b.`purge`,b.mcr \
        from rma.copq_accumulation_actachievement_cell_2023 a left join \
        (select m2copq_target,m2copq,yearmonth,provision,`purge`,mcr from rma.copq_accumulation_actachievement_cell_2023 where app='"+app+"' and (yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL)) b on a.yearmonth = b.yearmonth \
        where app in ('TV','TV (SET)') and yearmonthLog="+yearmonthLog+" or yearmonthLog is NULL group by yearmonth order by yearmonth,app") 
        if cur.rowcount > 2 :
            TV_copq_accumulation = 0
            TV_SET_copq_accumulation = 0

            TV_copq_target_accumulation = 0
            TV_SET_copq_target_accumulation = 0    

            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['TV_copq'] = float(r[1])
                    tmp['TV_SET_copq'] = float(r[2])  
                    tmp['TV_copq_target'] = float(r[3])
                    tmp['TV_SET_copq_target'] = float(r[4])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 and float(r[2]) > 0 :
                        TV_copq_accumulation = TV_copq_accumulation + float(r[1])
                        TV_SET_copq_accumulation = TV_SET_copq_accumulation + float(r[2])
                    else :
                        TV_copq_accumulation = 0
                        TV_SET_copq_accumulation = 0
                    TV_copq_target_accumulation = TV_copq_target_accumulation + float(r[3])
                    TV_SET_copq_target_accumulation = TV_SET_copq_target_accumulation + float(r[4])  

                    tmp['TV_copq'] = TV_copq_accumulation  
                    tmp['TV_SET_copq'] = TV_SET_copq_accumulation 
                    tmp['TV_copq_target'] = TV_copq_target_accumulation
                    tmp['TV_SET_copq_target'] = TV_SET_copq_target_accumulation
                tmp['m2copq'] = r[5]        
                tmp['m2copq_target'] = r[6] 
                tmp['provision'] = r[7]        
                tmp['purge'] = r[8]
                tmp['mcr'] = r[9]
                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
    
    else : # app類
        cur.execute("select yearmonth,copq,copq_target,m2copq,m2copq_target,provision,`purge`,mcr from rma.copq_accumulation_actachievement_cell_2023 where app=%s and (yearmonthLog=%s or yearmonthLog is NULL)",(app,yearmonthLog))
        copq_accumulation = 0
        copq_target_accumulation = 0
        if cur.rowcount > 2 :
            for r in cur :
                tmp = OrderedDict();       

                yearmonth = r[0]
                if yearmonth == '2022實績' or yearmonth == '2023改善前':
                    tmp['copq'] = float(r[1])
                    tmp['copq_target'] = float(r[2])

                else : # 202101 ~ 202112 copq實績有值才累計，否則為0
                    if float(r[1]) > 0 :
                        copq_accumulation = copq_accumulation + float(r[1])
                    else :
                        copq_accumulation = 0
                    copq_target_accumulation = copq_target_accumulation + float(r[2])

                    tmp['copq'] = copq_accumulation  
                    tmp['copq_target'] = copq_target_accumulation
                tmp['m2copq'] = r[3]        
                tmp['m2copq_target'] = r[4]  
                tmp['provision'] = r[5]        
                tmp['purge'] = r[6]
                tmp['mcr'] = r[7]

                returnData[yearmonth] = tmp    
        else :
            returnData[0] = 0 #無資料回傳
        
    # 20200723 增加commentType 均銘 
    # comment
    if commentType == 'act' :
        cur.execute("select comment from rma.copq_comment_actachievement where app=%s and yearmonth=%s order by id desc limit 1",(app,yearmonthLog))
    elif commentType == 'xy' :
        cur.execute("select comment from rma.copq_comment_xy where yearmonth=%s order by id desc limit 1",(yearmonthLog))
        
    if cur.rowcount > 0 and '202312' in returnData :
        tmp = returnData['202312']; 
        for r in cur :
            tmp['comment'] = r[0]
        returnData['202312'] = tmp
    
    # 20200720 燈圖    
    print(returnData)
    #print('==================================')
    
    cur.execute("select app,handtype from copq_handtype where yearmonth=%s",(yearmonthLog))
    if cur.rowcount > 0 :
        for r in cur : 
            print(r)
            returnData['202312'][r[0]] = r[1]            
    else : # 還沒設本月燈圖
        returnData['202312'][r[0]] = 0;
        
    response = jsonify(returnData)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response 

# 20200708 加上yearmonth來區隔每年月的comment，可回溯修改。均銘
##20200720 燈圖 均銘
@app.route("/getComment_act", methods=['GET'])
def getComment_act():
    conn = pymysql.connect(host=host, port=port,user=user, passwd=passwd, db=db)
    cur = conn.cursor()     
    
    app = request.args.get('app');       
    yearmonth = request.args.get('yearmonth');       
    returnData = OrderedDict();
    
    comment_list = OrderedDict();
    cur.execute("select comment, creationdate,PERNR,userChineseName from copq_comment_actachievement where app=%s and yearmonth=%s order by id desc",(app,yearmonth)) 
    c = 0
    for r in cur :
        tmp = OrderedDict();        
        tmp['comment'] = r[0]
        tmp['creationdate'] = r[1]
        tmp['PERNR'] = r[2]        
        tmp['userChineseName'] = r[3]
        comment_list[c] = tmp
        c = c + 1
        #returnData.append(tmp)
    
    # 20200720 燈圖
    handtype_list = OrderedDict();
    if app == 'OVERALL' :
        cur.execute("select app,handtype from copq_handtype where yearmonth=%s",(yearmonth))        
        c = 0
        for r in cur :
            tmp = OrderedDict()
            tmp['app'] = r[0]
            tmp['handtype'] = r[1]
            handtype_list[c] = tmp
            c = c + 1
            
    returnData['comment_list'] = comment_list
    returnData['handtype_list'] = handtype_list    
    response = jsonify(returnData)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response     

##20200720 燈圖 均銘
@app.route("/submitComment_act", methods=['GET'])
def submitComment_act():
    conn = pymysql.connect(host=host, port=port,user=user, passwd=passwd, db=db)
    cur = conn.cursor() 
    
    comment = request.args.get('comment');
    app = request.args.get('app');
    #handtype = request.args.get('handtype');
    userChineseName = request.args.get('userChineseName');
    PERNR = request.args.get('PERNR');
    creationdate = datetime.datetime.fromtimestamp(round(time.time(), 0)).strftime('%Y-%m-%d %H:%M:%S')
    yearmonth = request.args.get('yearmonth');
    #handset = json.loads(request.args.get('handset'),encoding='utf8');
    handset = json.loads(request.args.get('handset') );
    handtype = ''
    #print(app,' ',comment,' ',handtype,' ',creationdate,' yearmonth:',yearmonth,' ',PERNR,' ',userChineseName,' ',handset)
     
    cur.execute("insert into copq_comment_actachievement(app,comment,handtype,creationdate,PERNR,userChineseName,yearmonth)values(%s,%s,%s,%s,%s,%s,%s) ",(app,comment,handtype,creationdate,PERNR,userChineseName,yearmonth)) 
    
    # copq_handtype update
    if app == 'OVERALL' and len(handset) > 0 : 
        for app in handset :             
            if cur.execute("insert ignore into copq_handtype (yearmonth,app,handtype)values(%s,%s,%s)",(yearmonth,app,handset[app])) == 0 :
                print("insert fail ",yearmonth,' ',app,' ',handset[app])
                cur.execute("update copq_handtype set handtype = %s where yearmonth = %s and app = %s",(handset[app],yearmonth,app))
     
    cur.execute("COMMIT") 
    
    returnData = ['寫入成功'];    
    response = jsonify(returnData)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response 

# 20200810 避免前端年月查詢寫死，自動取得最新的年月，更新前端
@app.route("/getYmEnd", methods=['GET','POST'])
def getYmEnd():
    conn = pymysql.connect(host=host, port=port,user=user, passwd=passwd, db=db) 
    cur = conn.cursor() 
    
    returnData = OrderedDict();
    returnData[0] = 202212
    #cur.execute('SELECT max(yearmonthLog) FROM copq_accumulation_actachievement')
    cur.execute('SELECT max(yearmonthLog) FROM copq_accumulation_actachievement_2023')
    yearmonthLog = cur.fetchone()
    if yearmonthLog is not None :
        returnData[0] = yearmonthLog[0];
    response = jsonify(returnData)
    response.headers.add('Access-Control-Allow-Origin', '*')    
    return response
    
if __name__ == '__main__':    
    app.run(host='0.0.0.0', port=81) #server
    #app.run(host='127.0.0.1', port=81) #local
