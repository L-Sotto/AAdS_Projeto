FROM python

WORKDIR /app

#COPY main.py .
COPY . /app

#RUN pip install flask
RUN pip install -r requirements.txt

CMD ["python", "app.py"]

EXPOSE 6000