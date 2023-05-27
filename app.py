from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances
import numpy as np

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:urnotyelping00@34.22.93.25:3306/yournet"
db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    user_ip = db.Column(db.String(255), nullable=True)
    registeredip = db.Column(db.String(255), nullable=True)

    userScoreHashTag = db.relationship("UserScoreHashTag", backref="user")

class UserScoreHashTag(db.Model):
    __tablename__ = "user_score_hash_tag"

    user_score_hash_tag_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    hash_tag_id = db.Column(db.Integer, db.ForeignKey("hash_tag.hash_tag_id"))
    score = db.Column(db.Integer)
    count = db.Column(db.Integer)

    hashTag = db.relationship("HashTag", backref="userScoreHashtag")

class HashTag(db.Model):
    __tablename__ = "hash_tag"

    hash_tag_id = db.Column(db.Integer, primary_key=True)
    hash_tag_name = db.Column(db.String(255))

@app.route("/users/<int:user_id>/scores", methods=["GET"])
def get_user_scores(user_id):
    user = Users.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    scores = {}
    for score in user.userScoreHashTag:
        hash_tag_name = score.hashTag.hash_tag_name
        scores[hash_tag_name] = score.score

    return jsonify(scores)

@app.route("/users/<int:user_id>/similar", methods=["GET"])
def get_similar_users(user_id):
    user = Users.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    user_scores = np.array([score.score for score in user.userScoreHashTag]).reshape(1, -1)

    all_users = Users.query.all()
    user_vectors = []
    for u in all_users:
        scores = np.array([score.score for score in u.userScoreHashTag])
        if scores.size == 0:  # Skip users with empty score array
            continue
        scores = scores.reshape(1, -1)
        user_vectors.append(scores)

    if len(user_vectors) == 0:
        return jsonify({"error": "No similar users found"}), 404

    user_vectors = np.concatenate(user_vectors)
    distances = pairwise_distances(user_scores, user_vectors)
    similar_user_indices = np.argsort(distances)[0][:5]  # Get indices of 5 most similar users

    similar_users = []
    for idx in similar_user_indices:
        similar_user = all_users[idx]
        similar_users.append({
            "user_id": similar_user.user_id,
            "name": similar_user.name,
            "email": similar_user.email
        })

    return jsonify(similar_users)



if __name__ == "__main__":
    app.run()
