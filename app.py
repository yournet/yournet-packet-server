from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sklearn.metrics import pairwise_distances
import numpy as np
from flask_cors import CORS

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:urnotyelping00@34.22.93.25:3306/yournet"
db = SQLAlchemy(app)
CORS(app)

# 사용자 정보 모델 정의
class Users(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    user_ip = db.Column(db.String(255), nullable=True)
    registeredip = db.Column(db.String(255), nullable=True)

    # 사용자와 UserScoreHashTag 모델 간의 관계 정의
    user_score_hash_tags = db.relationship("UserScoreHashTag", backref="users")


# 사용자 해시태그 점수 모델 정의
class UserScoreHashTag(db.Model):
    __tablename__ = "user_score_hash_tag"

    user_score_hash_tag_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    hash_tag_id = db.Column(db.Integer, db.ForeignKey("hash_tag.hash_tag_id"))
    score = db.Column(db.Integer)
    count = db.Column(db.Integer)

    # UserScoreHashTag와 Users 모델 간의 관계 정의
    user = db.relationship("Users", backref="user_score_hash_tags1")
    # UserScoreHashTag와 HashTag 모델 간의 관계 정의
    hash_tag = db.relationship("HashTag", backref="user_score_hash_tags2")


# 해시태그 모델 정의
class HashTag(db.Model):
    __tablename__ = "hash_tag"

    hash_tag_id = db.Column(db.Integer, primary_key=True)
    hash_tag_name = db.Column(db.String(255))


# 게시물 모델 정의
class Post(db.Model):
    __tablename__ = "post"

    post_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.String(255))
    post_image = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    like_count = db.Column(db.Integer, default=0)

    # Post와 Users 모델 간의 관계 정의
    user = db.relationship("Users", backref="posts")
    # Post와 UserScoreHashTag 모델 간의 관계 정의
    user_score_hash_tags = db.relationship("UserScoreHashTag", secondary="post_user_score_hash_tag", backref="posts")


# 게시물-사용자 해시태그 점수 모델 정의
class PostUserScoreHashTag(db.Model):
    __tablename__ = "post_user_score_hash_tag"

    post_id = db.Column(db.Integer, db.ForeignKey("post.post_id"), primary_key=True)
    user_score_hash_tag_id = db.Column(db.Integer, db.ForeignKey("user_score_hash_tag.user_score_hash_tag_id"), primary_key=True)
    score = db.Column(db.Integer)


# 특정 사용자의 점수 가져오기
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


# 유사한 사용자 가져오기
@app.route("/users/<int:user_id>/similar", methods=["GET"])
def get_similar_users(user_id):
    # 사용자 정보 가져오기
    user = Users.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    # 해시태그 정보 가져오기
    all_hash_tags = HashTag.query.all()
    hash_tag_count = len(all_hash_tags)

    # 사용자의 해시태그별 점수 가져오기
    user_scores = np.zeros(hash_tag_count)  # 모든 해시태그에 대해 0으로 초기화된 점수 배열
    for score in user.user_score_hash_tags:
        hash_tag_id = score.hash_tag_id
        hash_tag_index = hash_tag_id - 1  # 해시태그 ID는 1부터 시작하므로 인덱스는 0부터 시작
        user_scores[hash_tag_index] = score.score

    # 모든 사용자 정보 가져오기
    all_users = Users.query.all()
    user_vectors = []
    for u in all_users:
        scores = np.zeros(hash_tag_count)  # 모든 해시태그에 대해 0으로 초기화된 점수 배열
        for score in u.user_score_hash_tags:
            hash_tag_id = score.hash_tag_id
            hash_tag_index = hash_tag_id - 1  # 해시태그 ID는 1부터 시작하므로 인덱스는 0부터 시작
            scores[hash_tag_index] = score.score
        user_vectors.append(scores.reshape(1, -1))

    if len(user_vectors) == 0:
        return jsonify({"error": "No similar users found"}), 404

    # 유사도 계산을 위해 사용자 벡터 연결
    user_vectors = np.concatenate(user_vectors)

    distances = pairwise_distances(user_scores.reshape(1, -1), user_vectors)
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


# 유사한 사용자의 게시물 추천
@app.route("/users/<int:user_id>/recommend", methods=["GET"])
def recommend_posts(user_id):
    user = Users.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    # 유사한 사용자 가져오기
    similar_users = get_similar_users_func(user_id)

    # 유사한 사용자가 작성한 게시물 ID 수집
    post_ids = []
    for similar_user in similar_users:
        posts = Post.query.filter_by(user_id=similar_user["user_id"]).all()
        for post in posts:
            post_ids.append(post.post_id)

    # 추천 게시물 가져오기
    recommended_posts = Post.query.filter(Post.post_id.in_(post_ids)).all()

    # 응답 데이터 준비
    recommended_posts_data = []
    for post in recommended_posts:
        recommended_posts_data.append({
            "post_id": post.post_id,
            "title": post.title,
            "content": post.content,
            "user_id": post.user_id
        })

    return jsonify(recommended_posts_data)


# 사용자의 유사한 사용자 가져오기 (내부 함수)
def get_similar_users_func(user_id):
    # 사용자 정보 가져오기
    user = Users.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    # 해시태그 정보 가져오기
    all_hash_tags = HashTag.query.all()
    hash_tag_count = len(all_hash_tags)

    # 사용자의 해시태그별 점수 가져오기
    user_scores = np.zeros(hash_tag_count)  # 모든 해시태그에 대해 0으로 초기화된 점수 배열
    for score in user.user_score_hash_tags:
        hash_tag_id = score.hash_tag_id
        hash_tag_index = hash_tag_id - 1  # 해시태그 ID는 1부터 시작하므로 인덱스는 0부터 시작
        user_scores[hash_tag_index] = score.score

    # 모든 사용자 정보 가져오기
    all_users = Users.query.all()
    user_vectors = []
    for u in all_users:
        scores = np.zeros(hash_tag_count)  # 모든 해시태그에 대해 0으로 초기화된 점수 배열
        for score in u.user_score_hash_tags:
            hash_tag_id = score.hash_tag_id
            hash_tag_index = hash_tag_id - 1  # 해시태그 ID는 1부터 시작하므로 인덱스는 0부터 시작
            scores[hash_tag_index] = score.score
        user_vectors.append(scores.reshape(1, -1))

    if len(user_vectors) == 0:
        return jsonify({"error": "No similar users found"}), 404

    # 유사도 계산을 위해 사용자 벡터 연결
    user_vectors = np.concatenate(user_vectors)

    distances = pairwise_distances(user_scores.reshape(1, -1), user_vectors)
    similar_user_indices = np.argsort(distances)[0][:5]  # 가장 유사한 사용자의 인덱스 가져오기

    similar_users = []
    for idx in similar_user_indices:
        similar_user = all_users[idx]
        similar_users.append({
            "user_id": similar_user.user_id,
            "name": similar_user.name,
            "email": similar_user.email
        })

    return similar_users


if __name__ == "__main__":
    app.run()
