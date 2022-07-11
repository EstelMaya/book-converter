FROM python:3.10-alpine
COPY . .
RUN pip install -r requirements.txt
EXPOSE 80
CMD ["python", "-u" , "server.py"]
