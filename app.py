import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "tugra_elite_2026"

ADMIN_USER = "tugra"
ADMIN_PASS = "1234"

def init_db():
    conn = sqlite3.connect('opticgrid.db')
    c = conn.cursor()
    # Tabloyu müşteri bilgilerini de alacak şekilde güncelledik
    c.execute('''CREATE TABLE IF NOT EXISTS sonuclar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  ad TEXT, yas TEXT, cinsiyet TEXT, yuz_tipi TEXT, oneri TEXT, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'logged_in' in session: return redirect(url_for('analysis'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
        session['logged_in'] = True
        return redirect(url_for('analysis'))
    return "Hatalı Giriş", 401

@app.route('/analysis')
def analysis():
    if 'logged_in' not in session: return redirect(url_for('index'))
    return render_template('analysis.html')

@app.route('/save_result', methods=['POST'])
def save_result():
    if 'logged_in' not in session: return "Unauthorized", 403
    data = request.json
    conn = sqlite3.connect('opticgrid.db')
    c = conn.cursor()
    c.execute("INSERT INTO sonuclar (ad, yas, cinsiyet, yuz_tipi, oneri) VALUES (?,?,?,?,?)",
               (data.get('ad'), data.get('yas'), data.get('cinsiyet'), data.get('yuz_tipi'), data.get('oneri')))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
