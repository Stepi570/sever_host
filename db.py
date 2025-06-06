import sqlite3
import pandas as pd
from datetime import datetime
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# cursor.execute(f"CREATE TABLE users (id BIGINT,username VARCHAR(200),balance BIGINT, date VARCHAR(100))")
# cursor.execute(f"CREATE TABLE bots (username VARCHAR(200), id BIGINT,filename VARCHAR(200),program SMALLINT, text_start VARCHAR(100))")
# cursor.execute(f"CREATE TABLE pc_info (date VARCHAR(255),time VARCHAR(255),temperature VARCHAR(255),cpu VARCHAR(255),ram VARCHAR(255),work_time VARCHAR(255))")

# conn.commit()

# df = pd.read_csv("users.csv", sep=';')
# a=df.values.tolist()
# for i in a:
#     print(i)
#     current_datetime = datetime.now().strftime('%d.%m.%Y %H:%M')
#     cursor.execute(f"INSERT INTO users (id,username,balance,date) VALUES ({int(i[1])},'{i[0]}',110,'{current_datetime}')")
# conn.commit()

def new_piople(id,us):
    if (cursor.execute(f"SELECT * FROM users WHERE id={id}")).fetchone() == None:
        current_datetime = datetime.now().strftime('%d.%m.%Y %H:%M')
        cursor.execute(f"INSERT INTO users (id,username,balance,date) VALUES ({id},'{us}',110,'{current_datetime}')")
        conn.commit()
        return True
    else:
        return False


def new_file_name(id,file_name):
    cursor.execute(f"UPDATE bots SET  filename='{file_name}' WHERE id={id}")
    conn.commit()
    return

def yes(id,yes):
    cursor.execute(f"UPDATE bots SET text_start='{yes}' WHERE id={id}")
    conn.commit()
    return

def file_info(id):
    f=(cursor.execute(f"SELECT * FROM bots WHERE id={id}")).fetchone()
    return f

def program(id):
    cursor.execute(f"UPDATE bots SET program=1 WHERE id={id}")
    conn.commit()
    return
    
def program(id):
    cursor.execute(f"UPDATE bots SET program=1 WHERE id={id}")
    conn.commit()
    return

def zero_program():
    cursor.execute(f"UPDATE bots SET program=0")
    conn.commit()
    return

def pcinfo(date,time,temperature ,cpu,ram ,work_time):
    cursor.execute(f"INSERT INTO pc_info (date,time,temperature ,cpu,ram ,work_time) VALUES ('{date}','{time}','{temperature}' ,'{cpu}','{ram}' ,'{work_time}')")
    conn.commit()
    return

def temperature():
    f=cursor.execute("SELECT temperature FROM pc_info").fetchall()
    return f

def timm():
    f=cursor.execute("SELECT time FROM pc_info").fetchall()
    return f

def userss():
    f=cursor.execute("SELECT * FROM users").fetchall()
    return f

def one_user(id):
    f=cursor.execute(f"SELECT * FROM users WHERE id={id}").fetchall()
    return f

def chek_file(id):
    f=(cursor.execute(f"SELECT filename FROM bots WHERE id={id}")).fetchone()
    return f
    
def nev_file(username, id,filename,program, text_start):
    cursor.execute(f"INSERT INTO bots (username, id,filename,program, text_start) VALUES ('{username}', {id},'{filename}',{program}, '{text_start}')")
    conn.commit()
    return

def replase_file(id,file):
    cursor.execute(f"UPDATE bots SET filename='{file}' WHERE  id={id}")
    conn.commit()
    return

def start_ckript():
    f=cursor.execute("SELECT id FROM bots WHERE program=1").fetchall()
    return f

def all_id():
    f=cursor.execute("SELECT id FROM users").fetchall()
    return f

def count_piple():
    f=cursor.execute("SELECT COUNT(*) FROM users").fetchmany()
    return f