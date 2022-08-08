from dataclasses import replace
from datetime import datetime
import boto3
import json
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, redirect, url_for
import pymysql
import os
ACCESS_KEY = "AKIAY2PSFIV7PQAM2MUE"
SECRET_KEY = "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"
AWS_REGION = 'us-east-1'

ENDPOINT="clouddb.ccf0syj9wpze.us-east-1.rds.amazonaws.com"
PORT="3306"
USR="admin"
PASSWORD="password123"
DBNAME="appdb"

app = Flask(__name__)

@app.route('/', methods=['POST','GET'])
def login():
    if request.method == "POST":
        data = request.form
        email = data['email']
        password = data['password']

        conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
        cur = conn.cursor()
        data = cur.execute("select * from userdetails where email='"+email+"' and password='"+password+"';")
        if cur.fetchall():
            return redirect("/upload")
        
    return render_template('login.html')


@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == "POST":
        data = request.form
        email = data['email']
        password = data['password']

        conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO userdetails(email,password) VALUES('"+email+"','"+password+"');")
        print("Insert Success")
        conn.commit()

    return render_template('register.html')

@app.route('/upload', methods=['POST','GET'])
def upload():
    if request.method == 'POST':
        emails = request.form.getlist("email")
        client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, 
            aws_secret_access_key=SECRET_KEY)
        f = request.files['file']
        filename = secure_filename(f.filename)
        f.save(secure_filename(filename))
        client.upload_file(filename, "appdemocloud", filename)
        os.remove(filename)

        client = boto3.client('sns', aws_access_key_id=ACCESS_KEY, 
            aws_secret_access_key=SECRET_KEY,region_name=AWS_REGION)
        
        file = f"https://appdemocloud.s3.amazonaws.com/{filename}"

        topic = client.create_topic(Name="varun_topic_{}".format(datetime.now().strftime("%HH%MM%S%d%m%Y")))
        arn = topic['TopicArn']

        conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO fileinformation(filename,fileurl) VALUES('"+filename+"','"+file+"');")
        print("Insert Success")
        conn.commit()

        for e in emails:
            if e:
                client.subscribe(TopicArn=arn,Protocol='email',Endpoint=e)
        
        return f"<h4>Please verify the email and then click <a href='/verify?arn={arn}&file={file}'>here</a>"


    return render_template('index.html')


@app.route("/verify",methods=['GET'])
def verify():
    topic = request.args.get("arn")
    file = request.args.get("file")
    client = boto3.client('lambda', aws_access_key_id=ACCESS_KEY, 
            aws_secret_access_key=SECRET_KEY,region_name="us-east-1")

    client.invoke(FunctionName="clouddemo",Payload=json.dumps({"topic":topic,"file":file}))
    return redirect("/upload")




@app.route('/initialize')
def initialize():
    try:
        print("INITIALIZING DATABASE")
        conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
        cur = conn.cursor()
        try:
            cur.execute("DROP TABLE userdetails;")
            cur.execute("DROP TABLE fileinformation;")
            print("table deleted")
        except Exception as e:
            print("cannot delete table")
        cur.execute("CREATE TABLE userdetails(email VARCHAR(200), password VARCHAR(20));")
        print("table created")
        cur.execute("CREATE TABLE fileinformation(filename VARCHAR(200),fileurl VARCHAR(1000))")
        conn.commit()

        cur.execute("SELECT * FROM userdetails;")
        query_results = cur.fetchall()
        print(query_results)
        return redirect("/")
    except Exception as e:
        print("Database connection failed due to {}".format(e))
        return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)
