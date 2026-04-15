import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
# Güvenlik anahtarı - oturumları korur
app.secret_key = "opticgrid_luxury_key_2026"

# --- AYARLAR KÜTÜPHANESİ ---
# Şifreni veya kullanıcı adını buradan tek seferde değiştirebilirsin
AYARLAR = {
    "kullanici": "tugra",
    "sifre": "1234"
}

# VERİTABANI KURULUMU
def init_db():
    conn = sqlite3.connect('opticgrid.db')
    cursor = conn.cursor()
    # Sonuçları kaydedeceğimiz tabloyu oluşturur
    cursor.execute('''CREATE TABLE IF NOT EXISTS sonuclar 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       ad TEXT, 
                       yuz_tipi TEXT, 
                       oneri TEXT, 
                       tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# 1. ANA SAYFA (GİRİŞ EKRANI)
@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('analysis'))
    return render_template('login.html')

# 2. GİRİŞ KONTROLÜ (LOGIN)
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Yukarıdaki AYARLAR kütüphanesine göre kontrol eder
    if username == AYARLAR["kullanici"] and password == AYARLAR["sifre"]:
        session['logged_in'] = True
        session['username'] = username
        return redirect(url_for('analysis'))
    else:
        return "<h3>Hatalı Giriş!</h3><p>Kullanıcı adı veya şifre yanlış. Lütfen geri dönüp tekrar deneyin.</p>", 401

# 3. ANALİZ SAYFASI
@app.route('/analysis')
def analysis():
    if 'logged_in' not in session:
        return redirect(url_for('index'))
    return render_template('analysis.html')

# 4. VERİ KAYDETME (API)
@app.route('/save_result', methods=['POST'])
def save_result():
    if 'logged_in' not in session: 
        return "Yetkisiz Erişim", 403
        
    data = request.json
    try:
        conn = sqlite3.connect('opticgrid.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sonuclar (ad, yuz_tipi, oneri) VALUES (?,?,?)",
                       (data.get('ad', 'Misafir'), data.get('yuz_tipi'), data.get('oneri')))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Veri başarıyla kaydedildi."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 5. ÇIKIŞ YAP (LOGOUT)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Render üzerinde çalışması için port ayarı
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
