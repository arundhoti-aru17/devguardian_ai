FROM python:3.11

WORKDIR /app

COPY requirements_missing.txt .

RUN pip install -r requirements_missing.txt

COPY . .

CMD ["python", "app.py"]