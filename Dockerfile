FROM python:3.10

WORKDIR /app
COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]
