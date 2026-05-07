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
    link += "<a href=/movie1>爬取即將上映電影</a><hr>"
    link += "<a href=/spidermovie>讀取開眼電影即將上映影片，寫入Firestore</a><hr>"
    link += "<a href=/searchMovie>輸入片名關鍵字,可以查詢資料庫符合的電影</a><hr>"
    link += "<a href=/road>台中市十大肇事路口</a><hr>"

    return link

@app.route("/road")
def road():
    R = "<h1>台中市十大肇事路口(113年10月)<h1><br>"
    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
    Data = requests.get(url)

    JsonData = json.loads(Data.text)
    for item in JsonData:
        R += item["路口名稱"], "原因:",item["主要肇因"] + ",件數" + item["總件數"] + "<br>"

    return R

@app.route("/searchMovie", methods=["GET", "POST"])
def search_movie():
    if request.method == "POST":
        keyword = request.values.get("keyword")
        db = firestore.client()
        # 取得所有電影資料
        docs = db.collection("電影2B").get()
        
        R = f"<h3>搜尋：{keyword}</h3><table border='1'>"
        R += "<tr><th>編號</th><th>片名 介紹頁</th><th>海報</th><th>上映日期</th></tr>"
        
        n = 0
        for doc in docs:
            m = doc.to_dict()
            if keyword in m.get("title", ""):
                n += 1
                R += f"<tr>"
                R += f"<td>{n}</td>"
                R += f"<td><a href='{m.get('hyperlink')}' target='_blank'>{m.get('title')}</a></td>"
                R += f"<td><img src='{m.get('picture')}' width='100'></td>"
                R += f"<td>{m.get('showDate')}</td>"
                R += f"</tr>"
        
        return R + "</table><br><a href='/searchMovie'>重新查詢</a>"
    
    return """
        <form action="/searchMovie" method="POST">
            關鍵字：<input type="text" name="keyword">
            <button type="submit">搜尋電影</button>
        </form>
    """

@app.route("/spidermovie")
def spidermovie():
    R = ""
    db = firestore.client()

    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"

    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間: " ,"")

    result=sp.select(".filmListAllX li")
    total = 0
    for item in result:
        total += 1 
        movie_id = item.find("a").get("href").replace("/movie/" , "").replace("/","")
        title = item.find(class_="filmtitle").text
        picture = "http://www.atmovies.com.tw" + item.find("img").get("src")
        hyperlink = "http://www.atmovies.com.tw" + item.find("a").get("href")

        showDate = item.find(class_="runtime").text[5:15]
      

        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "lastUpdate": lastUpdate
        }

        doc_ref = db.collection("電影2B").document(movie_id)
        doc_ref.set(doc)

    R += "網站最近更新日期:" + lastUpdate + "<br>"
    R += "總共爬取" + str(total) + "部電影到資料庫"
    
    return R

@app.route("/movie1", methods=["GET", "POST"])
def movie1():
    if request.method == "POST":
        # 取得使用者輸入的關鍵字
        keyword = request.values.get("keyword")
       
        url = "https://www.atmovies.com.tw/movie/next/"
        Data = requests.get(url)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".filmListAllX li")
       
        R = f"<h2>您搜尋的關鍵字是：{keyword}</h2>"
        found = False
       
        for item in result:
            # 取得電影名稱
            movie_name = item.find("img").get("alt")
           
            # 檢查關鍵字是否在片名中 (不分大小寫可用 .lower())
            if keyword in movie_name:
                found = True
                introduce = "https://www.atmovies.com.tw" + item.find("a").get("href")
                post = "https://www.atmovies.com.tw" + item.find("img").get("src")
               
                R += f"<a href='{introduce}' target='_blank'>{movie_name}</a><br>"
                R += f"<img src='{post}' style='width:200px;'><br><br>"
       
        if not found:
            R += "<p>抱歉，查無包含此關鍵字的即將上映電影。</p>"
           
        return R + "<br><a href='/movie1'>重新查詢</a> | <a href='/'>回首頁</a>"
   
    else:
        # GET 請求：顯示查詢介面
        html = """
        <h2>即將上映電影查詢</h2>
        <form action="/movie1" method="POST">
            請輸入電影片名關鍵字：
            <input type="text" name="keyword" required>
            <button type="submit">搜尋</button>
        </form>
        <br><a href="/">回首頁</a>
        """
        return html

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