from flask import Flask, render_template, request, redirect, url_for, session, flash, current_app
import pymysql
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from datetime import timedelta
import secrets

app = Flask(__name__)
app.secret_key = 'super secret key'
app.permanent_session_lifetime = timedelta(minutes=10)

def save_images(photo):
    hash_photo = secrets.token_urlsafe(10)
    _,file_extension = os.path.splitext(photo.filename)
    photo_name = hash_photo + file_extension
    file_path = os.path.join(current_app.root_path, 'static/images', photo_name)
    photo.save(file_path)
    return photo_name
    #os 라이브러리의 기능을 공부할 필요가 있어보인다.


@app.route("/", methods=['GET'])
def home():
    db = pymysql.connect(host='localhost', user='root', db='ma8tofu', password='sparta', charset='utf8')
    curs = db.cursor()
    res = []
    
    sql = "SELECT * FROM feed AS f inner JOIN user as u on f.user_id = u.id order by f.id desc;"
    curs.execute(sql)
    
    rows = curs.fetchall()
    for e in rows:
        temp = {'num':e[0],'title':e[1],'description':e[2],'time':e[3], 'image':e[4],'name':e[8]}
        res.append(temp)
    
    # db.commit()
    db.close()

    return render_template ("home.html", res= res)

@app.route("/login" , methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form['login_id']
        password = request.form['password'].encode('utf-8') # DB에 넣을려고 변환
        db = pymysql.connect(host='localhost', user='root', db='ma8tofu', password='sparta', charset='utf8')
        curs= db.cursor(pymysql.cursors.DictCursor)
        curs.execute("select * from user where login_id = %s",[login_id])
        user = curs.fetchone()
        db.close()

        if user :
            if bcrypt.hashpw(password, user["pw"].encode('utf-8')) == user["pw"].encode("utf-8"):
                session['name'] = user['name']
                session['user_id'] = user['id']
                return redirect(url_for("home")) 
            else:
                return redirect("/login")
        else:
            return redirect("/login")

    return render_template("login.html")
        


@app.route("/logout")
def logout():
    session.clear()
    flash("로그 아웃되셨습니다", 'success')
    return redirect("/login")

# mypost
@app.route("/mypage", methods=["POST", "GET"])
def mypage():
    if 'name' not in session:
        return redirect("/login")
    else:
        user_id = session['user_id']
        db = pymysql.connect(host='localhost', user='root', db='ma8tofu', password='sparta', charset='utf8')
        curs= db.cursor(pymysql.cursors.DictCursor)
        # curs = db.cursor()
        
        # sql = 'SELECT f.user_id, u.name, f.title ,f.description ,f.created_at ,f.image, f.id FROM feed AS f inner JOIN user as u on f.user_id = u.id WHERE f.user_id = %s'
        sql = 'SELECT * FROM feed AS f inner JOIN user as u on f.user_id = u.id WHERE f.user_id = %s'
        curs.execute(sql, user_id)
        rows = curs.fetchall()
        return render_template("mypage.html",rows=rows)
    

@app.route("/write", methods=["POST","GET"])
def write():
    if 'name' not in session:
        return redirect("/login")
    else:
        if request.method == "POST":
            title = request.form['title']
            descriptiron = request.form['description']
            image = save_images(request.files['image'])
            user_id = session['user_id']

            db = pymysql.connect(host='localhost', user='root', db='ma8tofu', password='sparta', charset='utf8')
            curs= db.cursor(pymysql.cursors.DictCursor)
            # curs = db.cursor() Tuple형
            curs.execute("INSERT INTO feed (title,description,image,user_id) VALUES (%s, %s, %s, %s)",[title, descriptiron, image, user_id])
            db.commit()
            db.close()
            flash("Your comment have been successfully inserted", "success")
            return redirect('/')
        
        return render_template("write.html")


@app.route("/sign_up", methods=['GET', 'POST'])
def sign_up():
    db = pymysql.connect(host='localhost', user='root', db='ma8tofu', password='sparta', charset='utf8')
    curs = db.cursor()
    if request.method == 'POST':
        email = request.form['email']
        password1 = request.form['password1'].encode('utf-8')
        password2 = request.form['password2'].encode('utf-8')
        login_id = request.form['login_id']
        name = request.form['name']

        if len(login_id) < 4:
            flash ('아이디가 4글자 이상이어야 합니다.', category='error')
        elif password1 != password2:
            flash ('비밀번호가 일치하지 않습니다.', category='error')
        elif len(password1) < 7 :
            flash('비밀번호가 최소 7 문자 이상이어야 합니다.' , category='error')
        elif len(name) < 3:
            flash('이름이 최소 3자 이어야 합니다.', category='error')
        else:
            hash_password = bcrypt.hashpw(password1, bcrypt.gensalt())
            curs.execute("INSERT INTO user (login_id,name,pw,email) VALUES (%s, %s, %s, %s)" ,
            (login_id,name,hash_password,email))
            db.commit()
            db.close()
            # session['name'] = request.form['name']
            return redirect(url_for("home"))
    else:
        return render_template("sign_up.html")


@app.route("/mypage/edit/<id>", methods=["POST", "GET"])
def editpage(id):
    if 'name' not in session:
        return redirect("/login")
    if request.method == "POST":
        title = request.form['title']
        descriptiron = request.form['description']
        image = save_images(request.files['image'])

        db = pymysql.connect(host='localhost', user='root', db='ma8tofu', password='sparta', charset='utf8')
        curs= db.cursor(pymysql.cursors.DictCursor)
        curs.execute("UPDATE feed SET title=%s ,description=%s, image=%s WHERE id=%s",[title, descriptiron, image, id])
        db.commit()
        db.close()
        return redirect('/mypage')
    db = pymysql.connect(host='localhost', user='root', db='ma8tofu', password='sparta', charset='utf8')
    curs= db.cursor(pymysql.cursors.DictCursor)
    sql = 'SELECT * FROM feed AS f inner JOIN user as u on f.user_id = u.id WHERE f.id = %s'
    curs.execute(sql,id)
    rows = curs.fetchall()
    if rows:
        return render_template("edit.html", rows=rows)
    else:
        return redirect("/")


@app.route("/mypage/delete/<id>")
def deletepage(id):
    db = pymysql.connect(host='localhost', user='root', db='ma8tofu', password='sparta', charset='utf8')
    curs = db.cursor(pymysql.cursors.DictCursor)
    sql = "DELETE FROM feed WHERE id=%s"
    curs.execute(sql,id)
    db.commit()
    db.close()
    return redirect("/mypage")


@app.route("/view/<id>")
def single(id):
    db = pymysql.connect(host='localhost', user='root', db='ma8tofu', password='sparta', charset='utf8')
    # curs = db.cursor()
    curs= db.cursor(pymysql.cursors.DictCursor)
    sql = "SELECT * FROM feed where id=%s;"
    curs.execute(sql,id)
    row = curs.fetchone()
    return render_template("view.html", row=row)


if __name__ == '__main__':
    app.run('127.0.0.1', port=5050, debug=True)
    # app.debug = True
    # app.run()
    #app.run(debug=True)
