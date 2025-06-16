FROM python

WORKDIR /app

COPY main.py .

RUN pip install flask flask-cors pymongo pymediainfo

CMD ["python", "main.py"]

EXPOSE 5000