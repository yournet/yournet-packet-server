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

    user_score_hash_tags = db.relationship("UserScoreHashTag", backref="users")


class UserScoreHashTag(db.Model):
    __tablename__ = "user_score_hash_tag"

    user_score_hash_tag_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    hash_tag_id = db.Column(db.Integer, db.ForeignKey("hash_tag.hash_tag_id"))
    score = db.Column(db.Integer)
    count = db.Column(db.Integer)

    user = db.relationship("Users", backref="user_score_hash_tags1")
    hash_tag = db.relationship("HashTag", backref="user_score_hash_tags2")


class HashTag(db.Model):
    __tablename__ = "hash_tag"

    hash_tag_id = db.Column(db.Integer, primary_key=True)
    hash_tag_name = db.Column(db.String(255))


class Post(db.Model):
    __tablename__ = "post"

    post_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.String(255))
    post_image = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    like_count = db.Column(db.Integer, default=0)

    user = db.relationship("Users", backref="posts")
    user_score_hash_tags = db.relationship("UserScoreHashTag", secondary="post_user_score_hash_tag", backref="posts")


class PostUserScoreHashTag(db.Model):
    __tablename__ = "post_user_score_hash_tag"

    post_id = db.Column(db.Integer, db.ForeignKey("post.post_id"), primary_key=True)
    user_score_hash_tag_id = db.Column(db.Integer, db.ForeignKey("user_score_hash_tag.user_score_hash_tag_id"), primary_key=True)
    score = db.Column(db.Integer)


@app.route("/users/<int:user_id>/scores", methods=["GET"])
def get_user_scores(user_id):
    user = Users.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    scores = {}
    for score in user.user_score_hash_tags:
        hash_tag_name = score.hash_tag.hash_tag_name
        scores[hash_tag_name] = score.score

    return jsonify(scores)


@app.route("/users/<int:user_id>/similar", methods=["GET"])
def get_similar_users(user_id):
    # 사용자 정보 가져오기
    user = Users.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    # 사용자의 해시태그별 점수 가져오기
    user_scores = np.array([score.score for score in user.user_score_hash_tags]).reshape(1, -1)

    # 모든 사용자 정보 가져오기
    all_users = Users.query.all()
    user_vectors = []
    for u in all_users:
        scores = np.array([score.score for score in u.user_score_hash_tags])
        if scores.size == 0:  # 점수 배열이 비어있는 사용자는 제외
            continue
        scores = scores.reshape(1, -1)
        user_vectors.append(scores)

    if len(user_vectors) == 0:
        return jsonify({"error": "No similar users found"}), 404

    # 유사도 계산을 위해 사용자 벡터 연결
    user_vectors = np.concatenate(user_vectors)
    distances = pairwise_distances(user_scores, user_vectors)
    similar_user_indices = np.argsort(distances)[0][:5]  # 가장 유사한 사용자의 인덱스 가져오기

    similar_users = []
    for idx in similar_user_indices:
        similar_user = all_users[idx]
        similar_users.append({
            "user_id": similar_user.user_id,
            "name": similar_user.name,
            "email": similar_user.email
        })

    return jsonify(similar_users)


@app.route("/users/<int:user_id>/recommend", methods=["GET"])
def recommend_posts(user_id):
    user = Users.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    user_scores = [score.score for score in user.user_score_hash_tags]

    all_posts = Post.query.all()
    recommended_posts = []
    for post in all_posts:
        post_scores = [score.score for score in post.user_score_hash_tags]
        intersection = set(user_scores).intersection(post_scores)
        if len(intersection) > 0:
            recommended_posts.append({
                "post_id": post.post_id,
                "title": post.title,
                "content": post.content
            })

    return jsonify(recommended_posts)


if __name__ == "__main__":
    app.run()
