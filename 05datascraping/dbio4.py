import pandas as pd
import os
from datetime import datetime
from sqlalchemy import create_engine, text
import pymysql
pymysql.install_as_MySQLdb()

def db_connect(dbname):
    engine_root = create_engine(f"mysql+pymysql://fintech_news:1234@172.20.0.152:3306")
    with engine_root.connect() as conn:
        conn.execute(text(f"create database if not exists {dbname}"))
        print(f"{dbname} 데이터베이스 확인/생성 완료")
        
    engine = create_engine(f"mysql+pymysql://fintech_news:1234@172.20.0.152:3306/{dbname}")
    conn = engine.connect()
    return conn


def load_data(dbname, table_name):
    conn = db_connect(dbname)
    data = pd.read_sql(table_name, con=conn)
    conn.close
    return data

def to_db(dbname, table_name, df):
    conn = db_connect(dbname)
    df.to_sql(table_name, con=conn, index=False, if_exists="append")
    conn.close()


