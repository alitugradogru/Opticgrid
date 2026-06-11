import sqlite3
import os
import numpy as np
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
    return render_template('landing.html')

@app.route('/login_page')
def login_page():
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

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT ad, yas, cinsiyet, yuz_tipi, oneri, tarih FROM sonuclar ORDER BY tarih DESC")
    musteriler = c.fetchall()
    conn.close()
    return render_template('admin.html', musteriler=musteriler)

@app.route('/scan_and_save', methods=['POST'])
def scan_and_save():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 403
    
    data = request.json
    landmarks = data.get('landmarks')       
    image_width = data.get('image_width')   
    image_height = data.get('image_height') 
    
    if landmarks is None or image_width is None or image_height is None:
        return jsonify({"status": "error", "message": "Ham tarama verileri eksik."}), 400
    
    def get_pt(idx):
        try:
            lm = landmarks[idx]
            if isinstance(lm, dict):
                x, y = lm.get('x', 0), lm.get('y', 0)
            else:
                x, y = getattr(lm, 'x', 0), getattr(lm, 'y', 0)
            return np.array([x * image_width, y * image_height])
        except Exception:
            return np.array([0, 0])

    try:
        # Resmi MediaPipe Face Mesh Noktaları ile Gerçek Geometri Ölçümü
        alin_sol, alin_sag = get_pt(54), get_pt(284)
        elmacik_sol, elmacik_sag = get_pt(234), get_pt(454)
        cene_sol, cene_sag = get_pt(172), get_pt(397)
        yuz_ust, yuz_alt = get_pt(10), get_pt(152)

        W_alin = np.linalg.norm(alin_sol - alin_sag)
        W_elmacik = np.linalg.norm(elmacik_sol - elmacik_sag)
        W_cene = np.linalg.norm(cene_sol - cene_sag)
        H_yuz = np.linalg.norm(yuz_ust - yuz_alt)

        en_boy_orani = H_yuz / W_elmacik if W_elmacik != 0 else 1.0
        alin_cene_orani = W_alin / W_cene if W_cene != 0 else 1.0
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Hesaplama hatası: {str(e)}"}), 400

    # --- GERÇEK MATEMATİKSEL KARAR AGACI ---
    if 0.95 <= en_boy_orani <= 1.06:
        if 0.95 <= alin_cene_orani <= 1.06:
            yuz_tipi = "Kare Yüz"
            oneri = "Güçlü çene hattınızı yumuşatmak için tam yuvarlak (round), oval veya ince metal çerçeveler tercih edilmelidir. Sert ve kalın kare gözlüklerden uzak durmalısınız."
        else:
            yuz_tipi = "Yuvarlak Yüz"
            oneri = "Yüzünüze keskinlik katacak kalın köşeli, asetat dikdörtgen veya sert kare çerçeveler seçilmelidir. Yuvarlak formlardan kesinlikle kaçının."

    elif en_boy_orani > 1.32:
        yuz_tipi = "Dikdörtgen Yüz"
        oneri = "Yüzün dikey uzunluğunu dengelemek için geniş, büyük (oversized) ve dikey derinliği fazla olan kalın kemik çerçeveler seçilmelidir."

    else:
        if W_alin > W_elmacik and W_alin > W_cene:
            yuz_tipi = "Kalp Yüz"
            oneri = "Alın genişliğini dengelemek için çerçevesiz (rimless), yarım çerçeveli, transparan tonlardaki veya alt kısmı daha hacimli Pantos modeller seçilmelidir."
        elif W_elmacik > W_alin and W_elmacik > W_cene:
            if alin_cene_orani > 1.12:
                yuz_tipi = "Diamond Yüz"
                oneri = "Geniş elmacık kemiklerinizi dengelemek ve dar alın/çene hattınızı yumuşatmak için kedi gözü (cat-eye), oval veya üst kısmı belirgin kaşlı (clubmaster) modeller tercih edilmelidir."
            else:
                yuz_tipi = "Oval Yüz"
                oneri = "Dengeli yüz oranlarınız sayesinde neredeyse her model size yakışır. Aviator, Wayfarer veya modern geometrik çerçeveleri tercih edebilirsiniz."
        else:
            yuz_tipi = "Oval Yüz"
            oneri = "Dengeli yüz oranlarınız sayesinde neredeyse her model size yakışır. Aviator, Wayfarer veya modern geometrik çerçeveleri tercih edebilirsiniz."

    # --- VERİTABANI KAYIT ---
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO sonuclar (ad, yas, cinsiyet, yuz_tipi, oneri) VALUES (?,?,?,?,?)",
                  (data.get('ad'), data.get('yas'), data.get('cinsiyet'), yuz_tipi, oneri))
        conn.commit()
        conn.close()
    except Exception as e:
        return jsonify({"status": "error", "message": f"Veritabanı hatası: {str(e)}"}), 500
    
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
