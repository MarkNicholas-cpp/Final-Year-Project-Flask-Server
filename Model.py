# model.py

from flask import jsonify
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
import math


class BookRecommender:
    def __init__(self, ratings_df, books_df):
        self.ratings_df = ratings_df
        self.books_df = books_df
        self._preprocess()
        self._train_model()

    def _preprocess(self):
        ratings_with_name = self.ratings_df.merge(self.books_df, on="ISBN")
        user_counts = ratings_with_name.groupby("User-ID").count()["Book-Rating"]
        self.active_users = user_counts[user_counts > 25].index
        self.filtered_ratings = ratings_with_name[
            ratings_with_name["User-ID"].isin(self.active_users)
        ]

        # Filter books with more than 50 ratings
        book_counts = self.filtered_ratings.groupby("Book-Title").count()["Book-Rating"]
        self.popular_books = book_counts[book_counts >= 50].index
        self.final_ratings = self.filtered_ratings[
            self.filtered_ratings["Book-Title"].isin(self.popular_books)
        ]

    def _train_model(self):
        # Create pivot table
        self.pt = self.final_ratings.pivot_table(
            index="Book-Title", columns="User-ID", values="Book-Rating", fill_value=0
        )

        # Calculate cosine similarity
        self.similarity_scores = cosine_similarity(self.pt)

        # Initialize Nearest Neighbors model
        self.nn_model = NearestNeighbors(metric="cosine", algorithm="brute")
        self.nn_model.fit(self.pt)

    def recommend_books(self, book_name, num_recommendations=10):
        book_index = np.where(self.pt.index == book_name)[0]
        print(self.pt)
        if len(book_index) == 0:
            return f"Book not found {book_name}"
        book_index = book_index[0]
        distances, indices = self.nn_model.kneighbors(
            [self.pt.iloc[book_index]], n_neighbors=num_recommendations + 1
        )
        recommendations = []
        for idx in indices[0][1:]:
            book = self.books_df.iloc[idx]
            recommendation = {
                "ISBN": book["ISBN"],
                "Book-Title": book["Book-Title"],
                "Book-Author": book["Book-Author"],
                "Year-Of-Publication": book["Year-Of-Publication"],
                "Publisher": book["Publisher"],
                "Image-URL-S": book["Image-URL-S"],
                "Image-URL-M": book["Image-URL-M"],
                "Image-URL-L": book["Image-URL-L"],
                "Average-Rating": math.isnan(
                    self.ratings_df[self.ratings_df["ISBN"] == book[0]][
                        "Book-Rating"
                    ].mean()
                )
                and 2
                or round(
                    self.ratings_df[self.ratings_df["ISBN"] == book[0]][
                        "Book-Rating"
                    ].mean(),
                    2,
                ),
            }
            recommendations.append(recommendation)
        return jsonify(recommendations)
