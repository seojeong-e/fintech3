import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime
from sqlalchemy import create_engine, text
import pymysql
pymysql.install_as_MySQLdb()
load_dotenv(dotenv_path="./data/.env_db")

db_id = os.getenv("id")
db_pw = os.getenv("pw")
addr = os.getenv("addr")
port = os.getenv("port")

def db_connect(dbname):
    engine = create_engine(f"mysql+pymysql://{db_id}:{db_pw}@{addr}:{port}/{dbname}")
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


