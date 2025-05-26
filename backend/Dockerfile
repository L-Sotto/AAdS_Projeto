FROM python

WORKDIR /app

COPY main.py .

#RUN pip install flask
RUN pip install -r requirements.txt

CMD ["python", "main.py"]

EXPOSE 5000