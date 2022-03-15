from flask import Flask, render_template, request, redirect, url_for, session
from urllib.parse import unquote
import hashlib, pymysql, requests, configparser

# 設定ファイルの読み込み
config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')

# Flaskの初期化
app = Flask(__name__)

# DBへの接続
def db_connect():
    return pymysql.connect(host='localhost',user=config_ini['DB']['User'], passwd=config_ini['DB']['Passwd'], db='bookMG_db',charset='utf8',cursorclass=pymysql.cursors.DictCursor)

# パスワードのハッシュ化
def calc_hash_pw(password, salt):

    text=(password + salt).encode('utf-8')
    result = hashlib.sha512(text).hexdigest()
    return result

# 書籍登録
@app.route('/b_reg', methods=['GET','POST'])
def book_register():
    if request.method == 'POST':
        #GooglBooksAPI
        url = 'https://www.googleapis.com/books/v1/volumes?q=isbn:' + request.form['ISBN']
        #情報の取得,json変換
        response = requests.get(url).json() 

        #書籍データの整形
        search_result = response['items'][0]['volumeInfo']
        item = {
            "title": search_result["title"],
            "author":search_result["authors"][0],
            "ISBN":search_result["industryIdentifiers"][0]["identifier"],
            "imageLink": search_result["imageLinks"]["thumbnail"].replace("1","2"),
            "des":search_result["description"]
        }

        return render_template('book_register_confirm.html', item=item)

    else:

        return render_template('book_register.html', flg=request.args.get('flg'))

@app.route('/b_reg_cfm', methods=['GET'])
def book_register_confirm():

    title = request.args.get('title')
    author = request.args.get('author')
    ISBN = request.args.get('ISBN')
    imageLink = unquote(request.args.get('imageLink'))
    des = request.args.get('des')

    with db_connect() as db:
        with db.cursor() as cur:
            sql = "insert into books (title,author,ISBN,imageLink,des) values (%s,%s,%s,%s,%s)"
            cur.execute(sql, (title,author,ISBN,imageLink,des))
        
        db.commit()
    
    return redirect('/b_reg')

# エントリーポイント
if __name__ == "__main__":
    # app.run(host="127.0.0.1", port=8000)
    app.run(debug=True)
