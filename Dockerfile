FROM python:3.9

COPY . /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]