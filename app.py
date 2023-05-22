from flask import Flask
import scapy.all as scapy
from elasticsearch import Elasticsearch
import requests

app = Flask(__name__)

def extract_keywords(content):
    url = "https://matgim.ai/public-api/api-keyword/extract"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "YOUR_API_KEY"  # Replace with your MATGIM API key
    }
    data = {
        "content": content
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        keywords = result.get("keywords", [])
        return keywords
    else:
        return []

@app.route("/")
def index():
    packets = scapy.sniff(count=1, filter="tcp port 80")
    for packet in packets:
        if packet.haslayer(scapy.TCP):
            http_request = packet.getlayer(scapy.TCP).payload
            content = http_request.body.decode("utf-8")

            # Extract the keywords using MATGIM API
            keywords = extract_keywords(content)

            # Save the keywords to Elasticsearch
            es = Elasticsearch()
            index = "keywords"
            doc = {
                "keywords": keywords
            }
            es.index(index=index, doc_type="_doc", body=doc)

    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True)
