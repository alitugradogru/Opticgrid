import sqlite3
import os
import math
import cv2
import numpy as np
import base64
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mediapipe as mp

app = Flask(__name__)
app.secret_key = "tugra_premium_key_2026"

ADMIN_USER = "tugra"
ADMIN_PASS = "1234"

# MediaPipe Face Mesh Modülünü Başlatıyoruz
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, min_detection_confidence=0.5)

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

# İKİ NOKTA ARASINDAKİ PİKSEL MESAFESİNİ HESAPLAYAN GEOMETRİK FONKSİYON
def mesafe_hesapla(p1, p2, img_w, img_h):
    x1, y1 = p1.x * img_w, p1.y * img_h
    x2, y2 = p2.x * img_w, p2.y * img_h
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# SİHİRLİ MATEMATİKSEL ANALİZ MOTORU
def yuz_analizi_yap(image_bytes):
    # Base64 görüntüyü OpenCV formatına çeviriyoruz
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None, "Görüntü işlenemedi"
    
    h, w, _ = img.shape
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_img)
    
    if not results.multi_face_landmarks:
        return None, "Yüz tespit edilemedi. Lütfen kameraya düzgün bakın."
    
    landmarks = results.multi_face_landmarks[0].landmark
    
    # Stratejik MediaPipe Noktalarının Seçilmesi
    # 10: Alın üstü, 152: Çene ucu, 234: Sol elmacık, 454: Sağ elmacık, 58: Sol çene köşesi, 288: Sağ çene köşesi
    yuz_uzunlugu = mesafe_hesapla(landmarks[10], landmarks[152], w, h)
    elmacik_genisligi = mesafe_hesapla(landmarks[234], landmarks[454], w, h)
    alin_genisligi = mesafe_hesapla(landmarks[109], landmarks[338], w, h)
    cene_genisligi = mesafe_hesapla(landmarks[58], landmarks[288], w, h)
    
    # Oranların Hesaplanması
    en_boy_orani = yuz_uzunlugu / elmacik_genisligi
    ust_alt_orani = alin_genisligi / cene_genisligi
    
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
        
    return yuz_tipi, oneri_gozluk

# YÖNLENDİRMELER VE GÜVENLİK DUVARI
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

# YENİ VE GERÇEKÇİ ANALİZ VE KAYIT LOGICI
@app.route('/scan_and_save', methods=['POST'])
def scan_and_save():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 403
    
    data = request.json
    img_base64 = data.get('image') # Frontend'den gelecek olan anlık kamera görüntüsü (base64 formatında)
    
    if not img_base64:
        return jsonify({"status": "error", "message": "Görüntü verisi alınamadı."}), 400
    
    # Base64 string'i decode edip temizleme
    if "," in img_base64:
        img_base64 = img_base64.split(",")[1]
    img_bytes = base64.b64decode(img_base64)
    
    # Gerçek analizi başlatıyoruz
    yuz_tipi, oneri_gozluk = yuz_analizi_yap(img_bytes)
    
    if yuz_tipi is None:
        return jsonify({"status": "error", "message": oneri_gozluk}), 400
        
    # Veritabanına Gerçek Sonuçları Yazıyoruz
    conn = sqlite3.connect('opticgrid.db')
    c = conn.cursor()
    c.execute("""INSERT INTO sonuclar (ad, yas, cinsiyet, yuz_tipi, form, kopru, renk, oneri) 
                 VALUES (?,?,?,?,?,?,?,?)""",
               (data.get('ad'), data.get('yas'), data.get('cinsiyet'), yuz_tipi, 
                data.get('form', 'Belirlenmedi'), data.get('kopru', 'Belirlenmedi'), 
                data.get('renk', 'Belirlenmedi'), oneri_gozluk))
    conn.commit()
    conn.close()
    
    # Frontend'e ekrana basması için gerçek sonuçları fırlatıyoruz
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
    # Geliştirme ortamında çalışması için MediaPipe kütüphanesini pip ile kurmalısın: pip install mediapipe opencv-python
    app.run(host='0.0.0.0', port=5000, debug=True)
