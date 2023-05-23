from flask import Flask, request
from scapy.all import *
#from celery import Celery
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import threading
import os

app = Flask(__name__)
#app.config["CELERY_BROKER_URL"] = "redis://localhost:6379/0"
#app.config["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/0"

# Celery 객체 생성
#celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"], backend=app.config["CELERY_RESULT_BACKEND"])

# MySQL Database 설정
username = str(os.environ.get("MYSQL_ID_YOURNET"))
password = str(os.environ.get("MYSQL_PASSWORD_YOURNET"))
engine = create_engine("mysql://"+username+":"+password+"@us-cdbr-east-06.cleardb.net:3306/heroku_ec04377ff1e0856")
Base = declarative_base()

# MySQL 테이블 모델 정의
class PacketLog(Base):
    __tablename__ = "packet_logs"
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(20))
    packet_data = Column(String(1000))
    timestamp = Column(DateTime)

# MySQL 세션 생성
Session = sessionmaker(bind=engine)
session = Session()

# Celery 작업 정의
#@celery.task

def process_packet(packet_data, ip_address, timestamp):
    # 패킷 데이터 처리 및 MySQL에 저장
    log = PacketLog(ip_address=ip_address, packet_data=packet_data, timestamp=timestamp)
    session.add(log)
    session.commit()

@app.route("/", methods=["POST"])
def capture_packet():
    packet_data = request.data.decode("utf-8")
    ip_address = request.remote_addr
    timestamp = datetime.now()

    # Celery 작업 실행
    process_packet.delay(packet_data, ip_address, timestamp)

    return "Packet captured and logged asynchronously!"

if __name__ == "__main__":
    app_thread = threading.Thread(target=process_packet)
    app_thread.start()
    app.run(debug=True)
