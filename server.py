#env\Scripts\python.exe
# -*- coding: utf-8 -*-

import os
from flask import Flask, request, render_template, url_for, redirect, session, abort, jsonify
from werkzeug.exceptions import HTTPException
from datetime import datetime
import time
import sqlite3
import uuid

app = Flask(__name__, static_folder='public', template_folder='paginas')

app.secret_key = os.environ.get('SECRET')
UPLOAD_FOLDER = 'public\\postsimg'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['USERS'] = {os.environ.get('USER'): os.environ.get('SENHA')}
last_interaction_time = {}

def generate_unique_filename(filename):
    ext = filename.rsplit('.', 1)[1]    
    unique_filename = "{}.{}".format(uuid.uuid4().hex, ext)
    return unique_filename

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', postagem=reversed(access_db('SELECT * FROM postagem',(),'f')))

#@app.errorhandler(404)
#def not_found_error(error):    
#    return render_template('404.html'), 404

#@app.errorhandler(Exception)
#def handle_exception(e):
#    if isinstance(e, HTTPException):
#        return e
#
#    return render_template("500.html", erro=e), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in app.config['USERS'] and app.config['USERS'][username] == password:
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/editor')
def editor():
    if 'username' in session:
        return render_template('escrever.html')
    else:
        abort(404)

@app.route('/escrever', methods=['POST'])
def escrever_artigo():
    titulo = request.form['titulo']
    conteudo = request.form['conteudo']
    file = request.files['fileInput']
    access_db('INSERT INTO postagem (titulo, conteudo, data, autor, imagem) VALUES (?, ?, ?, ?, ?)', (titulo, conteudo, datetime.now().strftime("%d/%m/%Y às %H:%M"), session.get('username'), file.filename.rsplit('.', 1)[1] if file else '0'), 'c')
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], "{}.{}".format(access_db('select seq from sqlite_sequence where name="postagem"', (), 'f')[0][0], file.filename.rsplit('.', 1)[1]))
        file.save(filepath)
    return redirect(url_for('index'))

@app.route('/deletarpost/<post_id>')
def deletarpost(post_id):
    if 'username' in session:
      access_db('DELETE FROM postagem WHERE id == (?)', (post_id,), "c")
    return redirect(url_for('index'))

@app.route('/like', methods=['POST', 'GET'])
def like():
    now = time.time()
    post_id = request.args.get('post_id')
    if request.method == 'GET' and (now - last_interaction_time.get((request.remote_addr, post_id), 0)) > 2:
        post_id = request.args.get('post_id')
        
        liked_posts = request.cookies.get('liked_posts', '').split(',')
        post_likes = access_db('SELECT likes FROM postagem WHERE id == (?)', (post_id,), 'f')[0][0]

        if str(post_id) not in liked_posts:
            post_likes += 1
            liked_posts.append(str(post_id))
        else:
            post_likes -= 1
            liked_posts.remove(str(post_id))
        access_db('UPDATE postagem SET likes = (?) WHERE id == (?)', (post_likes, post_id), 'c')
        last_interaction_time[(request.remote_addr, post_id)] = now

        response = jsonify({'likes':post_likes})
        response.set_cookie('liked_posts', ','.join(liked_posts))

        return response
    return abort(500)

@app.route('/postagem/<id>')
def postagem(id):
    post = access_db('SELECT * FROM postagem WHERE id == (?) LIMIT 1', (id,), 'f')
    return render_template('postagem.html', post=post[0])

@app.route('/atualizacoes')
def atualizacoes():
    return render_template('atualizacoes.html')

@app.context_processor # Parâmetros padrões pros views  
def utility_processor():
    def logado():
        return session.get('username')
    def imgPath():
        return app.config['UPLOAD_FOLDER'].rsplit('\\')[1]
    return dict(logado=logado, imgPath=imgPath)

def access_db(command: str, params, method: str):
    conn = sqlite3.connect('datadados.db')
    cursor = conn.cursor()
    cursor.execute(command, params)
    results = cursor.fetchall() if method=='f' else conn.commit()
    conn.close()
    return results
  
if __name__ == '__main__':
    access_db('''
        CREATE TABLE IF NOT EXISTS postagem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            conteudo TEXT,
            data INTEGER,
            autor TEXT,
            imagem TEXT,
            likes INTEGER DEFAULT 0
        )
    ''', (), 'c')
    access_db('''
        CREATE TABLE IF NOT EXISTS comentarios (
            id INTEGER PRIMARY KEY,
            idPost INTERGER,
            conteudo TEXT,
            data INTEGER,
            autor TEXT,
            email TEXT,
            likes INTEGER DEFAULT 0
        )
    ''', (), 'c')   
    app.run(debug=True)