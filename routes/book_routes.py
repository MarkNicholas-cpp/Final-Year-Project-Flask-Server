from flask import Blueprint, jsonify, request
import math
import pandas as pd
import pickle
from Model import BookRecommender
from db_util import get_connection

book_routes = Blueprint("book_routes", __name__)

books = pd.read_csv("./routes/Books.csv",low_memory=False)
ratings_df = pd.read_csv("./routes/Ratings.csv")
popular_books = pickle.load(open("popular_df.pkl", "rb"))

recommender = BookRecommender(ratings_df, books)


@book_routes.route("/")
def say_hello():
    return "Book Routes hello"


@book_routes.route("/getSearchBooks")
def get_search_books():
    connection = get_connection()
    if not connection:
        return jsonify({"error": "Failed to connect to the database"}), 500
    else:
        try:
            search_query = request.args.get("query")
            query_params = ()
            query = "SELECT * FROM `booksdata`"
            if search_query:
                regex_pattern = f"^{search_query}"
                query += " WHERE `COL 2` REGEXP %s OR `COL 3` REGEXP %s"
                query_params = (regex_pattern, regex_pattern)
            else:
                query += " LIMIT 100"
            cur = connection.cursor()
            cur.execute(query, query_params)
            data = cur.fetchall()
            cur.close()
            search_books = data
            res = [
                {
                    "ISBN": book[0],
                    "Book-Title": book[1],
                    "Book-Author": book[2],
                    "Year-Of-Publication": book[3],
                    "Publisher": book[4],
                    "Image-URL-S": book[5],
                    "Image-URL-M": book[6],
                    "Image-URL-L": book[7],
                    "Average-Rating": math.isnan(
                        ratings_df[ratings_df["ISBN"] == book[0]]["Book-Rating"].mean()
                    )
                    and 2
                    or round(ratings_df[ratings_df["ISBN"] == book[0]]["Book-Rating"].mean(),2),
                }
                for book in search_books
            ]
            return jsonify(res)
        except Exception as e:
            print(e)
            return str(e)


def get_books(limit, offset):
    connection = get_connection()
    if not connection:
        return jsonify({"error": "Failed to connect to the database"}), 500
    else:
        try:
            cur = connection.cursor()
            query = "SELECT * FROM booksdata LIMIT %s OFFSET %s"
            cur.execute(query, (limit, offset))
            books = cur.fetchall()
            cur.close()
            return books
        except Exception as e:
            return str(e)


@book_routes.route("/books")
def get_books_route():
    try:
        page = int(request.args.get("page", 0))
        page_size = int(request.args.get("page_size", 10))
        books = get_books(page_size, page)
        response = [
            {
                "ISBN": book[0],
                "Book-Title": book[1],
                "Book-Author": book[2],
                "Year-Of-Publication": book[3],
                "Publisher": book[4],
                "Image-URL-S": book[5],
                "Image-URL-M": book[6],
                "Image-URL-L": book[7],
                "Average-Rating": math.isnan(
                    ratings_df[ratings_df["ISBN"] == book[0]]["Book-Rating"].mean()
                )
                and 2
                or ratings_df[ratings_df["ISBN"] == book[0]]["Book-Rating"].mean(),
            }
            for book in books
        ]
        return jsonify(response)
    except ValueError:
        return "Invalid page number or page size parameter"


@book_routes.route("/popular")
def get_popular():
    popular_books_dict = popular_books.to_dict(orient="records")
    # Convert data to JSON format
    return popular_books_dict


def get_popular_books():
    min_num_ratings = 100
    top_n = 50
    ratings_with_name = ratings_df.merge(books, on="ISBN")
    num_rating_df = (
        ratings_with_name.groupby("Book-Title").count()["Book-Rating"].reset_index()
    )
    num_rating_df.rename(columns={"Book-Rating": "num_ratings"}, inplace=True)
    avg_rating_df = (
        ratings_with_name.groupby("Book-Title").mean(["Book-Rating"]).reset_index()
    )
    avg_rating_df.rename(columns={"Book-Rating": "Average-Rating"}, inplace=True)
    popular_df = num_rating_df.merge(avg_rating_df, on="Book-Title")
    popular_df = (
        popular_df[popular_df["num_ratings"] >= min_num_ratings]
        .sort_values("Average-Rating", ascending=False)
        .head(top_n)
    )
    popular_df = popular_df.merge(books, on="Book-Title").drop_duplicates("Book-Title")[
        [
            "Book-Title",
            "Book-Author",
            "Image-URL-L",
            "Year-Of-Publication",
            "Average-Rating",
            "Publisher",
        ]
    ]
    popular_df["Average-Rating"] = popular_df["Average-Rating"].round(2)
    return popular_df


def get_book_data(book_name):
    connection = get_connection()
    if not connection:
        return jsonify({"error": "Failed to connect to the database"}), 500
    else:
        try:
            cur = connection.cursor()
            cur.execute(
                "SELECT * FROM `booksdata` WHERE `COL 2` = %s OR `COL 3` = %s",
                (book_name, book_name),
            )
            book_data = cur.fetchall()
            cur.close()
            return book_data
        except Exception as e:
            return jsonify({"error" : str(e)}),500

@book_routes.route("/getBook/<book_name>", methods=["GET"])
def get_book(book_name):
    books = get_book_data(book_name)
    print(books)
    if books:
        response = [
            {
                "ISBN": book[0],
                "Book-Title": book[1],
                "Book-Author": book[2],
                "Year-Of-Publication": book[3],
                "Publisher": book[4],
                "Image-URL-S": book[5],
                "Image-URL-M": book[6],
                "Image-URL-L": book[7],
                "Average-Rating": math.isnan(
                    ratings_df[ratings_df["ISBN"] == book[0]]["Book-Rating"].mean()
                )
                and 2
                or round(
                    ratings_df[ratings_df["ISBN"] == book[0]]["Book-Rating"].mean(), 2
                ),
            }
            for book in books
        ]
        return jsonify(response)
    else:
        return jsonify({"error": "Book not found"}), 404

@book_routes.route("/recommend", methods=["GET"])
def recommend_books():
    book_name = request.args.get("book_name")
    print(book_name)
    recommendations = recommender.recommend_books(book_name)
    return (recommendations), 200
