import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "tugra_premium_key_2026"

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

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('analysis'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('username')
    pw = request.form.get('password')
    if user == ADMIN_USER and pw == ADMIN_PASS:
        session['logged_in'] = True
        return redirect(url_for('analysis'))
    else:
        return "Erişim Reddedildi: Geçersiz Lisans Bilgileri", 401

@app.route('/analysis')
def analysis():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('analysis.html')

# GERÇEK TARAMA VERİLERİNİ ALAN YENİ AKILLI ENDPOINT
@app.route('/scan_and_save', methods=['POST'])
def scan_and_save():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 403
    
    data = request.json
    
    # Frontend'deki MediaPipe'ın ölçtüğü GERÇEK oranlar buraya geliyor
    en_boy_orani = data.get('en_boy_orani')
    ust_alt_orani = data.get('ust_alt_orani')
    
    if not en_boy_orani or not ust_alt_orani:
        return jsonify({"status": "error", "message": "Tarama verileri eksik geldi."}), 400
    
    # Matematiksel Kurallarla Yüz Şekli Belirleme ve Dinamik Gözlük Eşleştirme
    yuz_tipi = "Belirlenemedi"
    oneri_gozluk = "Standart Model"
    
    if 0.92 <= en_boy_orani <= 1.05:
        yuz_tipi = "Yuvarlak (Round)"
        oneri_gozluk = "Köşeli, Dikdörtgen veya Kare çerçeveler yüzünüzü daha keskin gösterir."
    elif en_boy_orani >= 1.25:
        yuz_tipi = "Oval (Oval)"
        oneri_gozluk = "Harika! Neredeyse tüm gözlük tipleri (özellikle Aviator ve Wayfarer) size yakışır."
    elif 1.05 < en_boy_orani < 1.25 and ust_alt_orani > 1.15:
        yuz_tipi = "Kalp (Heart)"
        oneri_gozluk = "Alt kısmı daha geniş olan veya çerçevesiz/hafif modeller dengeli bir görünüm sağlar."
    elif 1.05 < en_boy_orani < 1.25 and ust_alt_orani <= 1.15:
        yuz_tipi = "Kare (Square)"
        oneri_gozluk = "Yuvarlak, Oval veya Yuvarlatılmış köşeli çerçeveler sert hatlarınızı yumuşatacaktır."
    else:
        yuz_tipi = "Dikdörtgen / Uzun"
        oneri_gozluk = "Geniş ve büyük çerçeveler, yüzünüzün uzunluğunu dengelemek için idealdir."
        
    # Veritabanına Gerçek Sonuçları Yazıyoruz
    conn = sqlite3.connect('opticgrid.db')
    c = conn.cursor()
    c.execute("""INSERT INTO sonuclar (ad, yas, cinsiyet, yuz_tipi, form, kopru, renk, oneri) 
                 VALUES (?,?,?,?,?,?,?,?)""",
               (data.get('ad'), data.get('yas'), data.get('cinsiyet'), yuz_tipi, 
                "Belirlendi", "Standart", "Doğal", oneri_gozluk))
    conn.commit()
    conn.close()
    
    return jsonify({
        "status": "success",
        "yuz_tipi": yuz_tipi,
        "oneri": oneri_gozluk
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
