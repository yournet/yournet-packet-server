from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:urnotyelping00@34.22.93.25:3306/yournet"
db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    #role_flag = db.Column(db.Enum("ADMIN", "USER"), nullable=True)
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

if __name__ == "__main__":
    app.run()
