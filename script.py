#import 
from bs4 import BeautifulSoup
import gspread
import numpy as np 
import requests
import re
import time
import pandas as pd
import psycopg2
from header import host, user, password, db_name, update_time,data_header, table_name
from functions import check_del_dates

####################################
#1
sa = gspread.service_account()
sh = sa.open("PythonMiddle")    #name of the table
wks = sh.worksheet("Sheet1")    #name of the sheet

####################################
#2a   #Connecting to existing DataBase
conn = psycopg2.connect(dbname='python_db', user='postgres', host='localhost', password='19988991Radik')
conn.autocommit = True

#2b   #Reading data about exchange rate from official site cbr.ru
dollar_rub = 'https://cbr.ru/currency_base/daily/'
headers = {'User Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77'}
full_page = requests.get(dollar_rub, headers)
soup    = BeautifulSoup(full_page.content,'html.parser')
convert =  soup.findAll("td")
convert =  str(convert[54])[4:11]
convert =  convert[0:2]+'.'+convert[4:10]
dollar  =  float(convert)
flags_deadline=[]

try:

    while True:
        ####################################
        #1 
        sheet = wks.get_all_records()           #Reading the table from Google Sheet
        df =  pd.DataFrame.from_records(sheet)  #Transforming to DataFrame
        data = data_header + df.values.tolist() #Transforming Data from the Table to list using panda

        ####################################
        #2b 
        #Adding the 5's column about payment in rubles in list
        for elem in data[1:]:
            print(elem)
            elem.append(str(float(elem[2])*dollar))

        #Adding the 5's column about payment in rubles in database
        with conn.cursor() as cursor:
            for d in data:
                cursor.execute("INSERT into my_middle_python(number,number_order, cost_in_dollars,delivery_cost,cost_in_rubs) VALUES (%s, %s, %s, %s, %s)"    , d)

        ####################################
        #3 
        #Sleep and update
        if flags_deadline==[]:
            flags_deadline={data[i][1]:False for i in range(1,len(data))}#Auxiliary dict. It tells about what violations of the delivery time the telegram account was informed about  
        else:
            for elem in data[1:]:                                        #Adding emelent in dict after chaniging or adding a row in the google sheet
                if elem[1] not in flags_deadline.keys():
                    flags_deadline[elem[1]]=False

        print("sleeping")
        time.sleep(update_time)
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM my_middle_python;"
            )

        ####################################
        #4b
        #checking delivery dates
        check_del_dates(data,flags_deadline)


                

except Exception as _ex:
    print("[INFO] Error while working with PostgreSQL", _ex)

finally:
    if conn:
        conn.close()
        print("[INFO] PostgreSQL connection closed")
