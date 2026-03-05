import os
from . import pymysql

def get_conn():
    host = os.getenv("MYSQL_HOST")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    db = os.getenv("MYSQL_DB")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    if not all([host, user, password, db]):
        raise RuntimeError("Missing DB env vars: MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB")
    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db,
        port=port,
        connect_timeout=8,
        read_timeout=15,
        write_timeout=15,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
