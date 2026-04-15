from flask import Flask, render_template, request, jsonify
import cv2
import mediapipe as mp
import numpy as np
import sqlite3
import base64
import os

app = Flask(__name__)

# --- DATABASE KURULUMU ---
def save_to_db(ad, yas, cinsiyet, yuz, oneri):
    try:
        conn = sqlite3.connect('opticgrid.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS musteriler 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, yas INTEGER, cinsiyet TEXT, yuz_tipi TEXT, oneri TEXT, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('INSERT INTO musteriler (ad, yas, cinsiyet, yuz_tipi, oneri) VALUES (?, ?, ?, ?, ?)', (ad, yas, cinsiyet, yuz, oneri))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Hatasi: {e}")

# --- AI MODELLERİ (Global Tanımlama ile Hızlandırma) ---
mp_face_mesh = mp.solutions.face_mesh
# Nesneyi burada bir kez oluşturuyoruz, her seferinde RAM harcamıyor
face_mesh_engine = mp_face_mesh.FaceMesh(
    static_image_mode=True, 
    max_num_faces=1, 
    min_detection_confidence=0.5
)

@app.route('/')
def index(): return render_template('login.html')

@app.route('/check_login', methods=['POST'])
def check_login(): return render_template('details.html')

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    return render_template('analysis.html', ad=request.form.get('ad'), yas=request.form.get('yas'), cinsiyet=request.form.get('cinsiyet'))

@app.route('/admin')
def admin_panel():
    conn = sqlite3.connect('opticgrid.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ad, yas, cinsiyet, yuz_tipi, oneri, tarih FROM musteriler ORDER BY tarih DESC')
    rows = cursor.fetchall()
    conn.close()
    return render_template('admin.html', musteriler=rows)

@app.route('/scan_web', methods=['POST'])
def scan_web():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'Resim verisi alınamadı'}), 400

        img_str = data['image'].split(',')[1]
        img_data = base64.b64decode(img_str)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({'error': 'Resim işlenemedi'}), 400

        # Görüntü boyutunu daha da düşürdük (RAM Dostu)
        frame = cv2.resize(frame, (320, 480)) 
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Hazır motoru kullanıyoruz
        results = face_mesh_engine.process(rgb)
        
        if results.multi_face_landmarks:
            h, w, _ = frame.shape
            lm = results.multi_face_landmarks[0].landmark
            y_yuk = np.linalg.norm(np.array([lm[10].x*w, lm[10].y*h]) - np.array([lm[152].x*w, lm[152].y*h]))
            y_gen = np.linalg.norm(np.array([lm[234].x*w, lm[234].y*h]) - np.array([lm[454].x*w, lm[454].y*h]))
            oran = y_yuk / y_gen

            c = data.get('cinsiyet', 'Erkek')
            if oran > 1.25:
                res, rnk = "UZUN / OVAL", ("Siyah" if c=="Erkek" else "Rose Gold")
                oneri = f"Yüzünüzün asaletini {rnk} tonlarında, geniş Wayfarer çerçevelerle taçlandırmalısınız."
            elif 0.95 < oran < 1.10:
                res, rnk = "YUVARLAK", ("Lacivert" if c=="Erkek" else "Bordo")
                oneri = f"Yumuşak hatlarınızı {rnk} rengi keskin köşeli çerçevelerle dengeleyin."
            else:
                res, rnk = "KARE / KALP", ("Gümüş" if c=="Erkek" else "Altın")
                oneri = f"Güçlü karakterinizi {rnk} tonlarındaki yuvarlak modellerle yumuşatın."
            
            save_to_db(data.get('ad'), data.get('yas'), c, res, oneri)
            return jsonify({'yuz_tipi': res, 'oneri': oneri})
        
        return jsonify({'error': 'Yüz algılanamadı, lütfen ışığa dönün.'}), 400
    except Exception as e:
        return jsonify({'error': 'Analiz yapılamadı'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
