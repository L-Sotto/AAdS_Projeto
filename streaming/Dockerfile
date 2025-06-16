FROM python

WORKDIR /app

COPY main.py .

RUN pip install flask flask-cors pymongo 
RUN mkdir -p /app/video_cache
CMD ["python", "main.py"]

EXPOSE 7000