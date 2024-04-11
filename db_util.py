import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_HOST = os.getenv('DB_HOST')
DB_SSL_CA = os.getenv('DB_SSL_CA')
def get_connection():
    try:
        connection = mysql.connector.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            host=DB_HOST,
            ssl_ca=DB_SSL_CA
        )
        return connection

    except mysql.connector.Error as err:
        print(err)
        return err