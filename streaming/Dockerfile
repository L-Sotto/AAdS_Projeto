FROM python

WORKDIR /app

COPY main.py .
#COPY . /app

#RUN pip install flask
#RUN pip install -r requirements.txt
RUN pip install flask flask-cors pymongo

CMD ["python", "main.py"]

EXPOSE 7000