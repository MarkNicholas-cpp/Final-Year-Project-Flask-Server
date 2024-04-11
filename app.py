from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,    
    get_jwt_identity,
    jwt_required,
)
from db_util import get_connection
from routes.book_routes import book_routes
from routes.search_routes import search_routes

app = Flask(__name__)
# Enable CORS and Database Connection
CORS(app)
app.config.from_pyfile("config.py")
jwt = JWTManager(app)


@app.route("/Connect")
def connect():
    connection = get_connection()
    if not connection:
        return jsonify({"error": "Failed to connect to the database"}), 500
    else:
        return "Connected to the database"

# login With JWT
@app.route("/login", methods=["POST"])
def login():
    connection = get_connection()
    if not connection:
        return jsonify({"error": "Failed to connect to the database"}), 500
    else:
        try:
            print(request.json["userId"])
            cur = connection.cursor()
            cur.execute(
                "SELECT * FROM `usersdata` WHERE `COL 1` = %s ", (request.json["userId"],)
            )
            res = cur.fetchall()
            res = res[0]
            res = {
                "userId": res[0],
                "address": res[1],
                "age": res[2],
            }
            access_token = create_access_token(res)
            return jsonify({"token": access_token, "res": res}), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "user not found"}), 404


@app.route("/like/<ISBN>", methods=["GET"])
@jwt_required()
def like_or_dislike(ISBN):
        connection = get_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        else:     
            try:
                current_user = get_jwt_identity()
                user_id = current_user["userId"]

                # Check if the user has already liked the book
                cur = connection.cursor()
                cur.execute(
                    "SELECT * FROM book_likes WHERE `userId` = %s AND `ISBN` = %s",
                    (user_id, ISBN),
                )
                existing_like = cur.fetchone()

                if existing_like:
                    # If the user has already liked the book, remove the like
                    cur.execute(
                        "DELETE FROM book_likes WHERE `userId` = %s AND `ISBN` = %s",
                        (user_id, ISBN),
                    )
                    connection.commit()
                    return jsonify({"message": "Book disliked successfully"})
                else:
                    # If the user hasn't liked the book yet, add the like
                    cur.execute(
                        "INSERT INTO book_likes (`userId`, `ISBN`, `like`) VALUES (%s, %s, %s)",
                        (user_id, ISBN, True),
                    )
                    connection.commit()
                    return jsonify({"message": "Book liked successfully"})
            except Exception as e:
                print(e)
                return jsonify({"error": "An error occurred while liking/disliking the book"})


app.register_blueprint(book_routes)
app.register_blueprint(search_routes)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)
