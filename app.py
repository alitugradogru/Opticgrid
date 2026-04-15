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

# --- MEDIAPIPE (KÖKÜMÜZ: SUNUCUDA ÇALIŞIYOR) ---
mp_face_mesh = mp.solutions.face_mesh
# static_image_mode=False ve model_complexity=0 ile Render'ın CPU'sunu koruyoruz
face_mesh_engine = mp_face_mesh.FaceMesh(
    static_image_mode=False, 
    max_num_faces=1, 
    model_complexity=0, 
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

@app.route('/')
def index(): return render_template('login.html')

@app.route('/check_login', methods=['POST'])
def check_login(): return render_template('details.html')

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    return render_template('analysis.html', 
                           ad=request.form.get('ad'), 
                           yas=request.form.get('yas'), 
                           cinsiyet=request.form.get('cinsiyet'))

@app.route('/admin')
def admin_panel():
    try:
        conn = sqlite3.connect('opticgrid.db')
        cursor = conn.cursor()
        cursor.execute('SELECT ad, yas, cinsiyet, yuz_tipi, oneri, tarih FROM musteriler ORDER BY tarih DESC')
        rows = cursor.fetchall()
        conn.close()
        return render_template('admin.html', musteriler=rows)
    except:
        return "Henüz kayıt bulunamadı."

@app.route('/scan_web', methods=['POST'])
def scan_web():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'Veri alınamadı'}), 400

        # Base64 çözme
        img_str = data['image'].split(',')[1]
        img_data = base64.b64decode(img_str)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({'error': 'Resim işlenemedi'}), 400

        # --- KRİTİK HIZLANDIRMA: Çözünürlüğü mikro boyuta düşürdük ---
        frame = cv2.resize(frame, (240, 320)) 
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Analiz Başlıyor
        results = face_mesh_engine.process(rgb)
        
        if results.multi_face_landmarks:
            h, w, _ = frame.shape
            lm = results.multi_face_landmarks[0].landmark
            
            # Kök hesaplama mantığın
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
        
        return jsonify({'error': 'Yüz algılanamadı, lütfen ışığa yaklaşın.'}), 400

    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({'error': 'Sunucu çok yoğun, lütfen tekrar deneyin.'}), 500

if __name__ == '__main__':
    # Render için dinamik port
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
