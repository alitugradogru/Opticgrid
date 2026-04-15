import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "tugra_premium_key_2026" # Güvenlik için anahtar

# SaaS Satış Bilgileri (Bunu ileride veritabanına bağlayabiliriz)
ADMIN_USER = "tugra"
ADMIN_PASS = "1234"

def init_db():
    conn = sqlite3.connect('opticgrid.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sonuclar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  ad TEXT, yas TEXT, cinsiyet TEXT, yuz_tipi TEXT, 
                  form TEXT, kopru TEXT, renk TEXT, oneri TEXT, 
                  tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# SİSTEMİN KALBİ: Giriş kontrolü
@app.route('/')
def index():
    # Eğer zaten giriş yapılmışsa doğrudan analize gönder
    if session.get('logged_in'):
        return redirect(url_for('analysis'))
    # Giriş yapılmamışsa MUTLAKA login sayfasını göster
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    # Satıcı (senin) belirlediğin kullanıcı adı ve şifre kontrolü
    user = request.form.get('username')
    pw = request.form.get('password')
    
    if user == ADMIN_USER and pw == ADMIN_PASS:
        session['logged_in'] = True
        return redirect(url_for('analysis'))
    else:
        # Hatalı girişte sayfayı yenileyip hata mesajı verebilirsin
        return "Erişim Reddedildi: Geçersiz Lisans Bilgileri", 401

@app.route('/analysis')
def analysis():
    # GÜVENLİK DUVARI: Burası çok kritik.
    # Kullanıcı login olmadan bu URL'i el yazıyla yazsa bile giremez.
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('analysis.html')

@app.route('/save_result', methods=['POST'])
def save_result():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 403
    
    data = request.json
    conn = sqlite3.connect('opticgrid.db')
    c = conn.cursor()
    c.execute("""INSERT INTO sonuclar (ad, yas, cinsiyet, yuz_tipi, form, kopru, renk, oneri) 
                 VALUES (?,?,?,?,?,?,?,?)""",
               (data.get('ad'), data.get('yas'), data.get('cinsiyet'), data.get('yuz_tipi'), 
                data.get('form'), data.get('kopru'), data.get('renk'), data.get('oneri')))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
