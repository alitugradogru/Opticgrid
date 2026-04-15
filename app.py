from flask import Flask, render_template, request, jsonify
import cv2
import mediapipe as mp
import numpy as np
import sqlite3
import base64
import os

app = Flask(__name__)

# --- DATABASE ---
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

# --- AI MODEL (En Güvenli Kurulum) ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)

@app.route('/')
def index(): return render_template('login.html')

@app.route('/check_login', methods=['POST'])
def check_login(): return render_template('details.html')

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    return render_template('analysis.html', ad=request.form.get('ad'), yas=request.form.get('yas'), cinsiyet=request.form.get('cinsiyet'))

@app.route('/scan_web', methods=['POST'])
def scan_web():
    try:
        data = request.json
        if not data or 'image' not in data: return jsonify({'error': 'Veri yok'}), 400

        img_str = data['image'].split(',')[1]
        img_data = base64.b64decode(img_str)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None: return jsonify({'error': 'Resim hatasi'}), 400

        # Render'ın CPU'sunu yormamak için boyutu küçülttük
        frame = cv2.resize(frame, (320, 480))
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        
        if results.multi_face_landmarks:
            h, w, _ = frame.shape
            lm = results.multi_face_landmarks[0].landmark
            y_yuk = np.linalg.norm(np.array([lm[10].x*w, lm[10].y*h]) - np.array([lm[152].x*w, lm[152].y*h]))
            y_gen = np.linalg.norm(np.array([lm[234].x*w, lm[234].y*h]) - np.array([lm[454].x*w, lm[454].y*h]))
            oran = y_yuk / y_gen

            c = data.get('cinsiyet', 'Erkek')
            if oran > 1.25: res, rnk = "UZUN / OVAL", ("Siyah" if c=="Erkek" else "Rose Gold")
            elif 0.95 < oran < 1.10: res, rnk = "YUVARLAK", ("Lacivert" if c=="Erkek" else "Bordo")
            else: res, rnk = "KARE / KALP", ("Gümüs" if c=="Erkek" else "Altin")
            
            oneri = f"Yüz tipiniz {res}. Size en uygun çerçeveler {rnk} tonlarindadir."
            save_to_db(data.get('ad'), data.get('yas'), c, res, oneri)
            return jsonify({'yuz_tipi': res, 'oneri': oneri})
        
        return jsonify({'error': 'Yüz bulunamadi'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
