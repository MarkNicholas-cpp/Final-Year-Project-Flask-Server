from flask import jsonify, request
from flask import Blueprint
from flask_mysqldb import MySQL 
import config

search_routes = Blueprint('search_routes', __name__)

mysql = MySQL()
mysql.host = config.MYSQL_HOST
mysql.user = config.MYSQL_USER
mysql.password = config.MYSQL_PASSWORD
mysql.db = config.MYSQL_DB
@search_routes.route("/search")
def say_hello(): 
    return "hello"
    
@search_routes.route("/getSearchOptions")
def get_search_options():
    try:
        search_query = request.args.get("query")
        query_params = ()
        query = "SELECT `COL 2`,`COL 3` FROM `booksdata`"
        if search_query:
            regex_pattern = f"^{search_query}"
            query += " WHERE `COL 2` REGEXP %s OR `COL 3` REGEXP %s"
            query_params = (regex_pattern, regex_pattern)
        else:
            query += " LIMIT 100"
        cur = mysql.connection.cursor()
        cur.execute(query, query_params)
        data = cur.fetchall()
        cur.close()
        res = []
        for i in data:
            for j in i:
                res.append(j)
        res = list(set(res))
        return jsonify(res)

    except Exception as e:
        print(e)
        return str(e)





