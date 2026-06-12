import sqlite3
import os
import json
import base64
import csv
from io import StringIO
import numpy as np
import requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response

app = Flask(__name__)
app.secret_key = "tugra_premium_key_2026"

# KULLANICI ADI VE ŞİFRELER (KAYA GİBİ GÜVENLİ)
ADMIN_USER = "tugra"
ADMIN_PASS = "1234"

DB_NAME = 'opticgrid.db'

# GITHUB CONFIGURATION (Render sıfırlama sorununu çözen kalıcı sistem)
GITHUB_TOKEN = ""  # Örn: "ghp_xxxxxxxxxxxx"
GITHUB_REPO = ""   # Örn: "alitudradogru/Opticgrid"
FILE_PATH = "templates/arsiv.json"

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

def sync_github_backup(action="save", ad=None, yas=None, cinsiyet=None, yuz_tipi=None, oneri=None, delete_name=None):
    """Verileri hem kaydederken hem de silerken GitHub reponla senkronize eder."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    current_content = []
    sha = None
    r = requests.get(url, headers=headers)
    
    if r.status_code == 200:
        res_json = r.json()
        sha = res_json.get('sha')
        content_decoded = base64.b64decode(res_json.get('content')).decode('utf-8')
        try:
            current_content = json.loads(content_decoded)
        except:
            current_content = []
            
    if action == "save":
        yeni_data = {"ad": ad, "yas": yas, "cinsiyet": cinsiyet, "yuz_tipi": yuz_tipi, "oneri": oneri}
        current_content.insert(0, yeni_data)
        msg = f"OpticGrid: {ad} arşive eklendi."
    elif action == "delete" and delete_name:
        current_content = [m for m in current_content if m.get('ad') != delete_name]
        msg = f"OpticGrid: {delete_name} arşivden silindi."
        
    updated_bytes = json.dumps(current_content, ensure_ascii=False, indent=4).encode('utf-8')
    updated_b64 = base64.b64encode(updated_bytes).decode('utf-8')
    
    payload = {"message": msg, "content": updated_b64, "branch": "main"}
    if sha:
        payload["sha"] = sha
        
    requests.put(url, headers=headers, json=payload)

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
    # KORUMA DUVARI
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template('analysis.html')

@app.route('/admin')
def admin():
    # KORUMA DUVARI
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
        
    # GitHub entegrasyonu aktifse verileri doğrudan repondaki kalıcı JSON'dan oku
    if GITHUB_TOKEN and GITHUB_REPO:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res_json = r.json()
            content_decoded = base64.b64decode(res_json.get('content')).decode('utf-8')
            try:
                musteriler = json.loads(content_decoded)
                # admin.html şablonu (id, ad, yas, cin, yuz, oneri, tarih) beklediği için simüle ediyoruz
                musteri_listesi = [(idx, m['ad'], m['yas'], m['cinsiyet'], m['yuz_tipi'], m['oneri'], 'Kalıcı Bulut') for idx, m in enumerate(musteriler)]
                return render_template('admin.html', musteriler=musteri_listesi)
            except:
                pass

    # GitHub bağlı değilse yerel SQLite veritabanından çek
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, ad, yas, cinsiyet, yuz_tipi, oneri, tarih FROM sonuclar ORDER BY tarih DESC")
    musteriler = c.fetchall()
    conn.close()
    return render_template('admin.html', musteriler=musteriler)

@app.route('/delete_customer/<int:cust_id>', methods=['POST', 'GET'])
def delete_customer(cust_id):
    """Müşteriyi hem yerel DB'den hem de GitHub kalıcı arşivinden siler."""
    if not session.get('logged_in'):
        return "Yetkisiz İşlem", 403
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT ad FROM sonuclar WHERE id = ?", (cust_id,))
    row = c.fetchone()
    
    if row:
        customer_name = row[0]
        c.execute("DELETE FROM sonuclar WHERE id = ?", (cust_id,))
        conn.commit()
        conn.close()
        # GitHub arşivinden de temizle
        try:
            sync_github_backup(action="delete", delete_name=customer_name)
        except:
            pass
    else:
        conn.close()
        
    return redirect(url_for('admin'))

@app.route('/export_csv')
def export_csv():
    """Tüm arşivi tek tıkla Excel uyumlu mükemmel bir CSV dosyası olarak bilgisayara indirir."""
    if not session.get('logged_in'):
        return "Yetkisiz İşlem", 403
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT ad, yas, cinsiyet, yuz_tipi, oneri, tarih FROM sonuclar ORDER BY tarih DESC")
    rows = c.fetchall()
    conn.close()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Müşteri Ad Soyad', 'Yaş', 'Cinsiyet', 'Yüz Geometrisi', 'Öneri Raporu', 'Tarama Tarihi'])
    cw.writerows(rows)
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=opticgrid_musteri_arsivi.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output

@app.route('/scan_and_save', methods=['POST'])
def scan_and_save():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 403
    
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "JSON verisi gelmedi."}), 400
        
    frames = data.get('frames')             
    image_width = data.get('image_width')   
    image_height = data.get('image_height') 
    
    if not frames or image_width is None or image_height is None:
        return jsonify({"status": "error", "message": "Çoklu tarama verileri eksik."}), 400
    
    def get_pt(lm_list, idx):
        try:
            lm = lm_list[idx]
            if isinstance(lm, dict):
                x, y = lm.get('x', 0), lm.get('y', 0)
            else:
                x, y = getattr(lm, 'x', 0), getattr(lm, 'y', 0)
            return np.array([x * image_width, y * image_height])
        except Exception:
            return np.array([0, 0])

    w_alin_list = []
    w_elmacik_list = []
    w_cene_list = []
    h_yuz_list = []

    try:
        for lm_list in frames:
            alin_sol, alin_sag = get_pt(lm_list, 54), get_pt(lm_list, 284)
            elmacik_sol, elmacik_sag = get_pt(lm_list, 234), get_pt(lm_list, 454)
            cene_sol, cene_sag = get_pt(lm_list, 172), get_pt(lm_list, 397)
            yuz_ust, yuz_alt = get_pt(lm_list, 10), get_pt(lm_list, 152)

            w_alin_list.append(np.linalg.norm(alin_sol - alin_sag))
            w_elmacik_list.append(np.linalg.norm(elmacik_sol - elmacik_sag))
            w_cene_list.append(np.linalg.norm(cene_sol - cene_sag))
            h_yuz_list.append(np.linalg.norm(yuz_ust - yuz_alt))

        W_alin = float(np.mean(w_alin_list))
        W_elmacik = float(np.mean(w_elmacik_list))
        W_cene = float(np.mean(w_cene_list))
        H_yuz = float(np.mean(h_yuz_list))

        en_boy_orani = H_yuz / W_elmacik if W_elmacik != 0 else 1.0
        alin_elmacik_orani = W_alin / W_elmacik if W_elmacik != 0 else 1.0
        cene_elmacik_orani = W_cene / W_elmacik if W_elmacik != 0 else 1.0
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Hesaplama hatası: " + str(e)}), 400

    # LENS TOLERANSLI EVRENSEL KARAR MOTORU
    if 0.92 <= alin_elmacik_orani <= 1.05 and 0.88 <= cene_elmacik_orani <= 1.05:
        if en_boy_orani > 1.30:
            yuz_tipi = "Dikdörtgen Yüz"
            oneri = "Yüzün dikey uzunluğunu dengelemek için geniş, büyük (oversized) ve dikey derinliği fazla olan kalın kemik çerçeveler seçilmelidir."
        else:
            yuz_tipi = "Kare Yüz"
            oneri = "Güçlü çene hattınızı yumuşatmak için tam yuvarlak (round), oval veya ince metal çerçeveler tercih edilmelidir. Sert ve kalın kare gözlüklerden uzak durmalısınız."

    elif W_elmacik >= W_alin * 1.06 and W_elmacik >= W_cene * 1.06:
        yuz_tipi = "Diamond Yüz"
        oneri = "Geniş elmacık kemiklerinizi dengelemek ve dar alın/çene hattınızı yumuşatmak için kedi gözü (cat-eye), oval veya üst kısmı belirgin kaşlı (clubmaster) modeller tercih edilmelidir."

    elif W_alin > W_elmacik * 0.98 and W_alin >= W_cene * 1.07:
        yuz_tipi = "Kalp Yüz"
        oneri = "Alın genişliğini dengelemek için çerçevesiz (rimless), yarım çerçeveli, transparan tonlardaki veya alt kısmı daha hacimli Pantos modeller seçilmelidir."

    elif en_boy_orani <= 1.12 and 0.88 <= alin_elmacik_orani <= 0.96:
        yuz_tipi = "Yuvarlak Yüz"
        oneri = "Yüzünüze keskinlik katacak kalın köşeli, asetat dikdörtgen veya sert kare çerçeveler seçilmelidir. Yuvarlak formlardan kesinlikle kaçının."

    else:
        yuz_tipi = "Oval Yüz"
        oneri = "Dengeli yüz oranlarınız sayesinde neredeyse her model size yakışır. Aviator, Wayfarer veya modern geometrik çerçeveleri tercih edebilirsiniz."

    ad_veri = data.get('ad', 'Bilinmeyen Müşteri')
    yas_veri = data.get('yas', '0')
    cinsiyet_veri = data.get('cinsiyet', 'Belirtilmemiş')

    # VERİTABANI YEREL KAYIT
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO sonuclar (ad, yas, cinsiyet, yuz_tipi, oneri) VALUES (?,?,?,?,?)",
                  (ad_veri, yas_veri, cinsiyet_veri, yuz_tipi, oneri))
        conn.commit()
        conn.close()
    except Exception as e:
        return jsonify({"status": "error", "message": "Veritabanı hatası: " + str(e)}), 500
    
    # GITHUB KALICI SENKRONİZASYON
    try:
        sync_github_backup(action="save", ad=ad_veri, yas=yas_veri, cinsiyet=cinsiyet_veri, yuz_tipi=yuz_tipi, oneri=oneri)
    except:
        pass
    
    return jsonify({"status": "success", "yuz_tipi": yuz_tipi, "oneri": oneri})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
