import sqlite3
import pandas as pd
from datetime import datetime
from db import *
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

df = pd.read_csv("users.csv", sep=';')
a=df.values.tolist()
for i in a:
    print(i)
    current_datetime = datetime.now().strftime('%d.%m.%Y %H:%M')
    cursor.execute(f"INSERT INTO users (id,username,balance,date) VALUES ({int(i[1])},'{i[0]}',110,'{current_datetime}')")
conn.commit()

df = pd.read_csv("pc_info.csv", sep=';')
a=df.values.tolist()
a=a[::-1]
for i in a:
    print(i)
    cursor.execute(f"INSERT INTO pc_info (date,time,temperature ,cpu,ram ,work_time) VALUES ('{i[0]}','{i[1]}','{i[2]}' ,'{i[3]}','{i[4]}' ,'{i[5]}')")
conn.commit()

df = pd.read_csv("users.csv", sep=';')
a=df.values.tolist()
for i in a:
    if i[3]==1:
        if i[4]=="Yes":
            eee="Да"
        else:
            eee="Нет"
        nev_file(i[0],i[1],i[2],i[3],eee)