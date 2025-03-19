#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask, request, render_template, url_for, redirect, session, abort, jsonify
from werkzeug.exceptions import HTTPException
from datetime import datetime, timedelta
from PIL import Image
import time
import sqlite3

app = Flask(__name__, static_folder='public', template_folder='paginas')

app.secret_key = os.environ.get('SECRET')
UPLOAD_FOLDER = 'public/postimg'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
last_interaction_time = {}
  
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', postagem=reversed(access_db('SELECT * FROM postagem',(),'f')))

@app.errorhandler(404)
def not_found_error(error):    
    return render_template('404.html'), 404

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e

    return render_template("500.html", erro=e), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        requestUser = access_db('SELECT senha FROM usuarios WHERE nome == (?) LIMIT 1', (username,), 'f')
        if requestUser != [] and requestUser[0][0] == password:
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/adicionaradm', methods=['GET', 'POST'])
def addadmin():
    if 'username' in session:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            access_db('INSERT INTO usuarios (nome, senha, admin) VALUES (?, ?, ?)', (username, password, 1), 'c')
        return render_template('addadmin.html', admins=access_db('SELECT nome FROM usuarios WHERE admin == (?)',(1,),'f'))
    abort(404)

@app.route('/editor')
def editor():
    if 'username' in session:
        return render_template('escrever.html')
    else:
        abort(404)

@app.route('/escrever', methods=['POST'])
def escrever_artigo():
    if 'username' in session:
      titulo = request.form['titulo']
      conteudo = request.form['conteudo']
      file = request.files['fileInput']
      access_db('INSERT INTO postagem (titulo, conteudo, data, autor, imagem) VALUES (?, ?, ?, ?, ?)', (titulo, conteudo,(datetime.now()-timedelta(hours=3)).strftime("%d/%m/%Y às %H:%M"), session.get('username'), file.filename.rsplit('.', 1)[1] if file else '0'), 'c')
      if file:
          filepath = os.path.join(app.config['UPLOAD_FOLDER'], "{}.{}".format(access_db('select seq from sqlite_sequence where name="postagem"', (), 'f')[0][0], file.filename.rsplit('.', 1)[1]))
          file.save(filepath)
          if file.filename.rsplit('.', 1)[1] != 'gif':
              Image.open(filepath).save(filepath, quality=75)
      return redirect(url_for('index'))
    abort(404)

@app.route('/editar/<post_id>')
def editar(post_id):
    if 'username' in session:
      post = access_db('SELECT * FROM postagem WHERE id == (?) AND autor == (?) LIMIT 1', (post_id, session.get('username')), 'f')
      if post:
        return render_template('editar.html', post=post[0])
      else:
        return render_template('editar.html', post=0)
    else:
        abort(404)

@app.route('/editar_post/<post_id>', methods=['POST'])
def editar_artigo(post_id):
    if 'username' in session:
      titulo = request.form['titulo']
      conteudo = request.form['conteudo']
      file = request.files['fileInput']
      if file:
          access_db('UPDATE postagem SET titulo=(?), conteudo=(?), imagem=(?), editado=1 WHERE id == (?)', (titulo, conteudo, file.filename.rsplit('.', 1)[1] if file else '0', post_id), 'c')
          filepath = os.path.join(app.config['UPLOAD_FOLDER'], "{}.{}".format(post_id, file.filename.rsplit('.', 1)[1]))
          file.save(filepath)
          if file.filename.rsplit('.', 1)[1] != 'gif':
              Image.open(filepath).save(filepath, quality=75)
      else:
        access_db('UPDATE postagem SET titulo=(?), conteudo=(?), editado=1 WHERE id == (?)', (titulo, conteudo, post_id), 'c')
      return redirect(url_for('postagem', id=post_id))
    abort(404)
  
@app.route('/deletarpost/<post_id>')
def deletarpost(post_id):
    if 'username' in session:
      imagem = access_db('select imagem from postagem where id==(?) and autor==(?)', (post_id, session.get('username')), 'f')
      if imagem[0][0] != '0':
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], "{}.{}".format(post_id, imagem[0][0]))
        os.remove(filepath)
      access_db('DELETE FROM postagem WHERE id == (?) and autor==(?) LIMIT 1', (post_id, session.get('username')), "c")
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
        return app.config['UPLOAD_FOLDER'].rsplit('/')[1]
    def autor(nome):
        return nome == session['username'].encode('utf-8')
    return dict(logado=logado, imgPath=imgPath, autor=autor)

def access_db(command, params, method):
    conn = sqlite3.connect('.data/datadados.db')
    conn.text_factory = str
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
            likes INTEGER DEFAULT 0,
            editado INTEGER DEFAULT 0
        )
    ''', (), 'c')
    access_db('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            senha TEXT,
            admin INTEGER DEFAULT 0
        )
    ''', (), 'c')
    app.run(debug=True)
