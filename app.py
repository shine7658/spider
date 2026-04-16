import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template, request
from datetime import datetime

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)


app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入宋媫的網站20260409</h1>"
    link +="<a href = /mis>課程</a><hr>"
    link +="<a href = /today>現在日期時間</a><hr>"
    link +="<a href = /me>關於我</a><hr>"
    link +="<a href = /welcome?u=zhe&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link +="<a href = /account>POST傳值(帳號密碼)</a><hr>"
    link +="<a href = /math>次方與根號計算</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/read2>讀取Firestore資料(根據姓名關鍵字:楊)</a><hr>"
    link += "<a href=/read3>讀取Firestore資料(根據姓名關鍵字:input)</a><hr>"
    link += "<a href=/spider1>爬蟲子青老師本學期課程</a><hr>"
    return link


@app.route("/spider1")
def spider1():
    Result = ""
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".team-box a")

    for i in result:
        Result += str(i.text) + i.get("href") + "<br>"
    return Result

@app.route("/read3", methods=["GET", "POST"])
def read3():
    if request.method == "POST":
        # 獲取 HTML 表單中 name="keyword" 的值
        keyword = request.values.get("keyword")
       
        Result = f"<h3>查詢結果 (關鍵字: {keyword})：</h3>"
        db = firestore.client()
        collection_ref = db.collection("靜宜資管2026B")
        docs = collection_ref.get()    
       
        found = False
        for doc in docs:
            teacher = doc.to_dict()
            if keyword in teacher.get("name", ""):
                # 這裡可以自訂顯示格式，例如：老師姓名、研究室
                name = teacher.get("name")
                lab = teacher.get("lab", "無資料")
                Result += f"<p><b style='color:blue'>{name}</b> 老師的研究室是在 {lab}</p>"
                found = True

        if not found:
            Result = "抱歉，查無此關鍵字姓名之老師資料"    
       
        Result += "<br><a href='/read3'>返回查詢頁面</a> | <a href='/'>返回首頁</a>"
        return Result
    else:
        # GET 請求時，顯示輸入框畫面 (對齊照片 1 的介面)
        html = """
        <h2>靜宜資管老師查詢</h2>
        <form action="/read3" method="POST">
            請輸入老師姓名關鍵字：
            <input type="text" name="keyword">
            <button type="submit">查詢</button>
        </form>
        <br><a href="/">返回首頁</a>
        """
        return html

@app.route("/read2")
def read2():
    Result = ""
    keyword = "楊"
    db = firestore.client()
    collection_ref = db.collection("靜宜資管2026B")
    docs = collection_ref.get()    
    for doc in docs:
        teacher = doc.to_dict()
        if keyword in teacher["name"]:
            Result += str(teacher) + "<br>"

    if Result == "":
        Result = "抱歉,查無此關鍵字姓名之老師資料"    
    return Result

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管2026B")
    docs = collection_ref.order_by("lab",direction = firestore.Query.DESCENDING).get()    
    for doc in docs:        
        Result += str(doc.to_dict()) + "<br>"    
    return Result

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime = str(now))

@app.route("/me")
def me():
    now = datetime.now()
    return render_template("mis2B.html")

@app.route("/welcome",methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name = user, dep = d, course = c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd
        return result
    else:
        return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    x_val = request.form.get("x")
    y_val = request.form.get("y")
    opt = request.form.get("opt")

    if request.method == "POST":
        try:
            x = float(x_val)
            y = float(y_val)

            if opt == "∧":
                result = x ** y
            elif opt == "√":
                if y == 0:
                    result = "數學不能開0次方根"
                else:
                    result = x ** (1/y)
            else:
                result = "請選擇運算符號"
        except ValueError:
            result = "請輸入有效的數字"
        return render_template("math.html", final_result= result)
    return render_template("math.html")

if __name__ == "__main__":
    app.run(debug=True)