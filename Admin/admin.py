from flask import Flask, session, abort, render_template, request, redirect
from datetime import timedelta
import configparser  # .ini管理モジュール
import pymysql  # DB管理モジュール
import hashlib  # ハッシュ化モジュール

# GoogleBookAPI 関連
import requests
from urllib.parse import unquote


# 設定ファイルの読み込み
config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')

# Flaskの初期化
app = Flask(__name__)

# セッションの初期化
app.secret_key = 'morijyobi2'
app.permanent_session_lifetime = timedelta(days=1)

# DBへの接続


def db_connect():
    return pymysql.connect(host='localhost', user=config_ini['DB']['User'], passwd=config_ini['DB']['Passwd'], db='bookMG_db', charset='utf8', cursorclass=pymysql.cursors.DictCursor)

# パスワードのハッシュ化


def calc_hash_pw(password, salt):
    text = (password + salt).encode('utf-8')
    result = hashlib.sha512(text).hexdigest()
    return result


# マイページ
@app.route('/', methods=["GET", 'POST'])
def index():
    try:
        print(session)

        if "user_id" in session:
            return render_template('index.html')

        else:
            return redirect('/login')

    except Exception as e:
        abort(e)

# ログイン画面
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            user_id = request.form['user_id']

            with db_connect() as db:
                with db.cursor() as cur:
                    sql = "select * from admins where user_id = %s"
                    cur.execute(sql, user_id)
                    result = cur.fetchone()
            if result:
                if calc_hash_pw(request.form['pw'], result['salt']) == result['hashed_pw']:

                    session.permanent = True
                    session["user_id"] = user_id

                    return redirect('/')

            # ログイン失敗
            return render_template('login.html', error="学籍番号かパスワードが違います。")

        else:
            return render_template('login.html')

    except Exception as e:
        abort(e)


# ログアウト
@app.route('/logout')
def logout():
    try:
        if "user_id" in session:
            session.pop('user_id', None)
            session.clear()
            return redirect("/login")
        
        else:
            return redirect('/login')

    except Exception as e:
        abort(e)


# 書籍登録
@app.route('/b_reg', methods=['GET', 'POST'])
def book_register():
    try:
        if "user_id" in session:
            if request.method == 'POST':
                # GooglBooksAPI
                url = 'https://www.googleapis.com/books/v1/volumes?q=isbn:' + request.form['ISBN']
                # 情報の取得,json変換
                response = requests.get(url).json()

                # 書籍データの整形
                search_result = response['items'][0]['volumeInfo']
                item = {
                    "title": search_result["title"],
                    "author": search_result["authors"][0],
                    "ISBN": search_result["industryIdentifiers"][0]["identifier"],
                    "imageLink": search_result["imageLinks"]["thumbnail"].replace("1", "2"),
                    "des": search_result["description"]
                }

                return render_template('book_register_confirm.html', item=item)

            else:

                return render_template('book_register.html', flg=request.args.get('flg'))
        
        else:
            return redirect('/login')

    except Exception as e:
            abort(e)


# 書籍登録確認
@app.route('/b_reg_cfm', methods=['GET'])
def book_register_confirm():
    try:
        if "user_id" in session:
            title = request.args.get('title')
            author = request.args.get('author')
            ISBN = request.args.get('ISBN')
            imageLink = unquote(request.args.get('imageLink'))
            des = request.args.get('des')

            with db_connect() as db:
                with db.cursor() as cur:
                    sql = "insert into books (title,author,ISBN,imageLink,des) values (%s,%s,%s,%s,%s)"
                    cur.execute(sql, (title, author, ISBN, imageLink, des))

                db.commit()

            return redirect('/b_reg')

        else:
            return redirect('/login')

    except Exception as e:
            abort(e)


# ユーザ管理
@app.route('/user', methods=['GET'])
def user_list():
    try:
        if "user_id" in session:
            with db_connect() as db:
                with db.cursor() as cur:
                    sql = "select * from users"
                    cur.execute(sql)
                    results = cur.fetchall()

            return render_template('user.html', results=results)

        else:
            return redirect('/login')

    except Exception as e:
            abort(e)


@app.route('/user_edit', methods=['GET', 'POST'])
def user_edit():
    try:
        if "user_id" in session:
            if request.method == 'POST':

                id = request.form['id']
                name = request.form['name']
                # pw = request.form['pw']

                with db_connect() as db:
                    with db.cursor() as cur:
                        sql = "update users set id = %s, name = %s where id = %s"
                        cur.execute(sql, (id, name, session['edit_id']))
                    
                    db.commit()
                
                session.pop('edit_id', None)
                return redirect('/user')
                
            else:

                id = request.args.get('id')

                with db_connect() as db:
                    with db.cursor() as cur:
                        sql = "select id,name from users where id = %s"
                        cur.execute(sql, id)
                        result = cur.fetchone()
                    
                    print(result)
                    session['edit_id'] = id

                return render_template('user_edit.html', result=result)
        else:
            return redirect('/login')

    except Exception as e:
            abort(e)


@app.route('/user_del', methods=['GET'])
def user_del():
    try:
        if "user_id" in session:
            id = request.args.get('id')

            with db_connect() as db:
                with db.cursor() as cur:
                    sql = "delete from users where id = %s"
                    cur.execute(sql, id)
                
                db.commit()

            return redirect('/user')

        else:
            return redirect('/login')

    except Exception as e:
            abort(e)

# エラー処理
@app.errorhandler(Exception)
def error_handler(e):
    # print(e)
    return render_template('error.html', error=e)


# エントリーポイント
if __name__ == "__main__":
    # app.run(host="127.0.10.1", port=8080)
    app.run(debug=True)
