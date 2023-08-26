#env\Scripts\python.exe
# -*- coding: utf-8 -*-

import os
from flask import Flask, request, render_template, url_for, redirect, session
from werkzeug.exceptions import HTTPException
import sqlite3
import uuid

app = Flask(__name__, static_folder='public', template_folder='paginas')

app.secret_key = os.environ.get('SECRET')
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['USERS'] = {os.environ.get('USER'): os.environ.get('SENHA')}

def generate_unique_filename(filename):
    ext = filename.rsplit('.', 1)[1]
    unique_filename = "{}.{}".format(uuid.uuid4().hex, ext)
    return unique_filename

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

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

@app.route('/postagem/<id:string>')
def postagens(id):
    postagem = access_db('SELECT * FROM postagens WHERE id == (?) LIMIT 1', (id,))
    return render_template('postagem.html', postagem=postagem)

@app.route('/atualizacoes')
def atualizacoes():
    return render_template('atualizacoes.html')

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
            id INTEGER PRIMARY KEY,
            titulo TEXT,
            conteudo TEXT,
            data INTEGER,
            autor TEXT,
            capa TEXT,
            likes INTEGER
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
            likes INTEGER
        )
    ''', (), 'c')   
    app.run(debug=True)