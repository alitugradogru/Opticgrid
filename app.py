from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# --- SADECE VERİTABANI KAYDI ---
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

@app.route('/')
def index(): return render_template('login.html')

@app.route('/check_login', methods=['POST'])
def check_login(): return render_template('details.html')

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    # Bilgileri analiz sayfasına aktarıyoruz
    return render_template('analysis.html', 
                           ad=request.form.get('ad'), 
                           yas=request.form.get('yas'), 
                           cinsiyet=request.form.get('cinsiyet'))

@app.route('/save_result', methods=['POST'])
def save_result():
    data = request.json
    save_to_db(data['ad'], data['yas'], data['cinsiyet'], data['yuz_tipi'], data['oneri'])
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
