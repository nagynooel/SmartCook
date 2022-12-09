import mysql.connector
from os import environ

root_db = mysql.connector.connect(
    host = environ.get("DATABASE_HOST"),
    user = environ.get("DATABASE_USER"),
    password = environ.get("DATABASE_PASSWORD")
)

root_c = root_db.cursor(buffered=True)

DATABASE_NAME = environ["DATABASE_NAME"]

# Drop database and create new one
root_c.execute(f"DROP DATABASE IF EXISTS {DATABASE_NAME}; CREATE DATABASE {DATABASE_NAME};")

db = mysql.connector.connect(
    host = environ.get("DATABASE_HOST"),
    user = environ.get("DATABASE_USER"),
    password = environ.get("DATABASE_PASSWORD"),
    database = DATABASE_NAME
)

c = db.cursor(buffered=True)

with open("tables.sql") as f:
    c.execute(f.read())