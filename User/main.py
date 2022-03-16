from flask import Flask, session, render_template, request, redirect, abort
from werkzeug.exceptions import NotFound
import pymysql
from datetime import date, timedelta
import configparser

# ハッシュ関連
import hashlib
import string
import random


# 設定ファイルの読み込み
config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')

# Flaskの初期化
app = Flask(__name__)

# セッションの初期化
app.secret_key = 'morijyobi'
app.permanent_session_lifetime = timedelta(days=1)
    
# DBへの接続
def db_connect():
    return pymysql.connect(host='localhost',user=config_ini['DB']['User'], passwd=config_ini['DB']['Passwd'], db='bookMG_db',charset='utf8',cursorclass=pymysql.cursors.DictCursor)

# パスワードのハッシュ化
def calc_hash_pw(password, salt):

    text=(password + salt).encode('utf-8')
    result = hashlib.sha512(text).hexdigest()
    return result

# saltの作成
def make_salt():
   return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# favicon設定
@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

# トップページ、検索ページ
@app.route("/", methods=['GET','POST'])
def top():
    try:
        with db_connect() as db:
            with db.cursor() as cur:
                if request.method == 'POST':
                    keyword = request.form['keyword']
                    sql = "select * from books where title like %s"
                    cur.execute(sql, "%"+keyword+"%")

                else:
                    sql = "select * from books"
                    cur.execute(sql)

                results = cur.fetchall()
        
        if "id" in session:
            return render_template('top.html', results=results, id=session["id"])
        return render_template('top.html', results=results)
    except Exception as e:
            abort(e)

# 本の詳細画面
@app.route("/book", methods=['GET'])
def book():
    try:
        if request.method == 'GET':

            id = request.args.get('id')

            # DB setting
            with db_connect() as db:
                with db.cursor() as cur:
                    sql = "select * from books where id = %s"
                    cur.execute(sql, id)
                    result = cur.fetchone()
            
            if "id" in session:
                return render_template('book.html', result=result, id=session["id"])

            return render_template('book.html', result=result)
    except Exception as e:
            abort(e)
# ログイン
@app.route("/login", methods=['GET','POST'])
def login():
    try:
        if request.method == 'POST':

            id = request.form['id']

            with db_connect() as db:
                with db.cursor() as cur:
                    sql = "select * from users where id = %s"
                    cur.execute(sql, id)
                    result = cur.fetchone()
            if result:
                if calc_hash_pw(request.form['pw'],result['salt']) == result['hashed_pw']:

                    session.permanent = True  
                    session["id"] = id

                    return redirect('/')
            
            # ログイン失敗 
            return render_template('login.html',error="学籍番号かパスワードが違います。")

        else:
            return render_template('login.html')

    except Exception as e:
                abort(e)

# ログアウト
@app.route('/logout', methods=['GET'])
def logout():
    try:
        if "id" in session:
            session.pop('id',None)
            session.clear()
            return redirect("/")

    except Exception as e:
                abort(e)

# ユーザ登録
@app.route('/u_reg', methods=['GET','POST'])
def user_register():
    try:
        if request.method == 'POST':
            id = request.form['id']
            name = request.form['name']
            salt = make_salt()
            hashed_pw = calc_hash_pw(request.form['pw'],salt)

            with db_connect() as db:
                with db.cursor() as cur:
                    sql = "insert into users values (%s, %s, %s, %s)"
                    cur.execute(sql, (id, name, hashed_pw, salt))
            
                db.commit()
            
            print("登録")
            return redirect('/login')

        else:
            return render_template('user_register.html')

    except Exception as e:
                abort(e)

# 本棚
@app.route('/shelf', methods=['GET'])
def book_shelf():
    try:
        if "id" in session:
            with db_connect() as db:
                with db.cursor() as cur:
                    sql = "select id, books.title, lendings.loan_date from lendings, books \
                        where lendings.book_id = books.id and lendings.user_id = %s"
                    cur.execute(sql, session["id"])
                    results=cur.fetchall()

            dt = date.today()

            return render_template('book_shelf.html', results=results, d = dt)

        else:
            return redirect('/')

    except Exception as e:
                abort(e)

# 本の貸出処理
@app.route('/lental', methods=['GET'])
def book_lental():
    try:
        if "id" in session:
            book_id = int(request.args.get('book_id'))
            user_id = int(session['id'])
            loan_date = date.today() + timedelta(days=20)
            
            with db_connect() as db:
                with db.cursor() as cur:
                    sql = "insert into lendings value (%s, %s, %s)"
                    cur.execute(sql, (book_id,user_id,loan_date))

                    sql = "update books set numbers = numbers - 1  where id = %s"
                    cur.execute(sql, book_id)
                    
                db.commit()
            
            return render_template('/book_lental.html')
        
        else:
            return redirect('/')
            
    except Exception as e:
                abort(e)

# 本の返却処理
@app.route('/return', methods=['GET'])
def book_return():
    try:
        book_id = int(request.args.get('book_id'))
        user_id = int(session['id'])


        with db_connect() as db:
                with db.cursor() as cur:
                    sql = "delete from lendings where book_id = %s and user_id = %s"
                    cur.execute(sql, (book_id, user_id))

                    sql = "update books set numbers = numbers + 1 where id = %s"
                    cur.execute(sql, book_id)
                
                db.commit()
        
        return redirect('/shelf')

    except Exception as e:
                abort(e)

# エラー処理
@app.errorhandler(Exception)
def error_handler(e):
    # print(e)
    return render_template('error.html', error=e)

# エントリーポイント
if __name__ == "__main__":
    # app.run(host="127.0.0.1", port=8080)
    app.run(debug=True)