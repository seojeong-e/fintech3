import time
import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as bs
from sqlalchemy import create_engine, text
import pymysql
pymysql.install_as_MySQLdb()
from dbio2 import to_db, db_connect

def new_cols(df):
    new_cols = []
    for col in df.columns:

        if col[0] == col[1] == col[2]:
            new_cols.append(col[0].replace(" ", "_"))
        elif col[0] != col[1] != col[2]:
            new_cols.append("_".join(col).replace(" ", "_"))
        else:
            new_cols.append("_".join(col[:2]).replace(" ", "_"))
    return new_cols


def main():
    yesterday = datetime.today() - timedelta(days=1)
    date1 = f"{yesterday.date()}"
    date2 = date1.replace("-", "")

    url = "https://www.kebhana.com/cms/rate/wpfxd651_01i_01.do"
    payload = dict(ajax="true", tmpInqStrDt=date1, pbldDvCd=3, inqStrDt=date2, inqKindCd=1, requestTarget="searchContentDiv")
    r= requests.post(url, data=payload)
    print(r.status_code)
    df = pd.read_html(StringIO(r.text))
    df = df[0]
    df.columns = new_cols(df)
    df.insert(0, "날짜", date1)

    # DB에 수집하는 날짜의 데이터가 있는지 확인
    conn = db_connect("ex_rate")
    try:
        query = text(f"select * from ex_rate where 날짜 = `{date1}`")
        result = conn.execute(query).fetchone()
        if result:
            print(f"{date1} 환율 정보가 이미 DB에 있습니다.")
        else:
            print(f"{date1} 환율 정보가 DB에 없으므로 수집합니다.")
            to_db("ex_rate", "ex_rate", df)
    except:
        to_db("ex_rate", "ex_rate", df)
    finally:
        conn.close()

if __name__ == "__main__":
    main()