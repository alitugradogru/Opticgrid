import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "tugra_premium_key_2026"

ADMIN_USER = "tugra"
ADMIN_PASS = "1234"

DB_NAME = 'opticgrid.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sonuclar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  ad TEXT, yas TEXT, cinsiyet TEXT, yuz_tipi TEXT, oneri TEXT,
                  tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    # Siteye ilk girildiğinde o şık gold/krem tanıtım sayfası açılsın
    return render_template('landing.html')

@app.route('/login_page')
def login_page():
    # Tanıtım sayfasındaki butona basıldığında giriş ekranı açılsın
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
        return "Erişim Reddedildi", 401

@app.route('/analysis')
def analysis():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('analysis.html')

@app.route('/scan_and_save', methods=['POST'])
def scan_and_save():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 403
    
    data = request.json
    en_boy_orani = data.get('en_boy_orani')
    ust_alt_orani = data.get('ust_alt_orani')
    alin_cene_orani = data.get('alin_cene_orani')  # Yeni eklenen oran!
    
    # Gerekli verilerin kontrolü
    if en_boy_orani is None or ust_alt_orani is None or alin_cene_orani is None:
        return jsonify({"status": "error", "message": "Tarama verileri (en_boy, ust_alt veya alin_cene) eksik."}), 400
    
    # --- YÜZ TİPİ VE ÖNERİ BELİRLEME MANTIĞI ---
    if 0.92 <= en_boy_orani <= 1.05:
        yuz_tipi = "Yuvarlak Yüz"
        oneri = "Yüzünüze keskinlik katacak kalın köşeli, asetat dikdörtgen veya sert kare çerçeveler seçilmelidir. Yuvarlak formlardan kesinlikle kaçının."

    elif en_boy_orani >= 1.25:
        if alin_cene_orani <= 1.10:
            yuz_tipi = "Dikdörtgen Yüz"
            oneri = "Yüzün dikey uzunluğunu dengelemek için geniş, büyük (oversized) ve dikey derinliği fazla olan kalın kemik çerçeveler seçilmelidir."
        else:
            yuz_tipi = "Oval Yüz"
            oneri = "Dengeli yüz oranlarınız sayesinde neredeyse her model size yakışır. Aviator, Wayfarer veya modern geometrik çerçeveleri tercih edebilirsiniz."

    elif 1.05 < en_boy_orani < 1.25:
        if ust_alt_orani > 1.22 and alin_cene_orani > 1.15:
            yuz_tipi = "Diamond Yüz"
            oneri = "Geniş elmacık kemiklerinizi dengelemek ve dar alın/çene hattınızı yumuşatmak için kedi gözü (cat-eye), oval veya üst kısmı belirgin kaşlı (clubmaster) modeller tercih edilmelidir."
            
        elif alin_cene_orani > 1.18:
            yuz_tipi = "Kalp Yüz"
            oneri = "Alın genişliğini dengelemek için çerçevesiz (rimless), yarım çerçeveli, transparan tonlardaki veya alt kısmı daha hacimli Pantos modeller seçilmelidir."
            
        elif 0.95 <= alin_cene_orani <= 1.05:
            yuz_tipi = "Kare Yüz"
            oneri = "Güçlü çene hattınızı yumuşatmak için tam yuvarlak (round), oval veya ince metal çerçeveler tercih edilmelidir. Sert ve kalın kare gözlüklerden uzak durmalısınız."
            
        else:
            yuz_tipi = "Oval Yüz"
            oneri = "Dengeli yüz oranlarınız sayesinde neredeyse her model size yakışır. Aviator, Wayfarer veya modern geometrik çerçeveleri tercih edebilirsiniz."

    else:
        yuz_tipi = "Dikdörtgen Yüz"
        oneri = "Yüzün dikey uzunluğunu dengelemek için geniş, büyük (oversized) ve dikey derinliği fazla olan kalın kemik çerçeveler seçilmelidir."

    # --- VERİTABANI KAYIT (Tüm yüz tipleri için ortak alan) ---
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO sonuclar (ad, yas, cinsiyet, yuz_tipi, oneri) VALUES (?,?,?,?,?)",
                  (data.get('ad'), data.get('yas'), data.get('cinsiyet'), yuz_tipi, oneri))
        conn.commit()
        conn.close()
    except Exception as e:
        return jsonify({"status": "error", "message": f"Veritabanı hatası: {str(e)}"}), 500
    
    # --- BAŞARILI YANIT ---
    return jsonify({
        "status": "success",
        "yuz_tipi": yuz_tipi,
        "oneri": oneri
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
