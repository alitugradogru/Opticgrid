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

# GERÇEK TARAMA VERİLERİNİ ALIP SENİN GÖZLÜK LİSTENLE EŞLEŞTİREN ENDPOINT
@app.route('/scan_and_save', methods=['POST'])
def scan_and_save():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 403
    
    data = request.json
    en_boy_orani = data.get('en_boy_orani')
    ust_alt_orani = data.get('ust_alt_orani')
    
    if en_boy_orani is None or ust_alt_orani is None:
        return jsonify({"status": "error", "message": "Tarama verileri eksik geldi."}), 400
    
    # SENİN DETAYLI GÖZLÜK ÖNERİ LİSTENİN ALGORİTMASI
    yuz_tipi = "Belirlenemedi"
    form = "-"
    kopru = "-"
    renk = "-"
    oneri = "-"
    
    if 0.92 <= en_boy_orani <= 1.05:
        yuz_tipi = "Yuvarlak Yüz"
        form = "Keskin Köşeli, Dikdörtgen (Rectangular), Geniş Kare (Square)"
        kopru = "Yüksek ve Düz Köprü (Gözleri daha ayrık ve dengeli gösterir)"
        renk = "Siyah, Mat Antrasit, Koyu Lacivert, Şeffaf Kristal"
        oneri = "Yüzünüzün yumuşak hatlarını dengelemek için sert ve köşeli formlar seçildi. Yuvarlak çerçevelerden kesinlikle kaçının."
        
    elif en_boy_orani >= 1.25:
        yuz_tipi = "Oval Yüz"
        form = "Aviator (Damla), Wayfarer, Clubmaster (Kaşlıklı), Geometrik (Çokgen)"
        kopru = "Standart / Anatomik Köprü"
        renk = "Havanna (Kaplumbağa kabuğu), Parlak Altın, Bal Köpüğü, Sıcak Kahve"
        oneri = "İdeal yüz oranlarınız sayesinde neredeyse her model size yakışır. Yüzünüzün en geniş kısmından biraz daha geniş çerçeveler harika duracaktır."
        
    elif 1.05 < en_boy_orani < 1.25 and ust_alt_orani > 1.15:
        yuz_tipi = "Kalp Yüz"
        form = "Çerçevesiz (Rimless), Yarım Çerçeve, Alt Kısmı Geniş Pantos modeller, Hafif Çekik Tasarımlar"
        kopru = "İnce Metal / Belirsiz Köprü"
        renk = "Açık Şeffaf Tonlar, Gümüş, Açık Gri, Nude renkler"
        oneri = "Alın bölgenizin genişliğini bastırmak ve dikkati çeneye çekmek için alt kısmı daha hacimli veya tamamen hafif/çerçevesiz modeller seçildi."
        
    elif 1.05 < en_boy_orani < 1.25 and ust_alt_orani <= 1.15:
        yuz_tipi = "Kare Yüz"
        form = "Tam Yuvarlak (Round), Oval, İnce Metal Çerçeveler, Cat-Eye (Kedi Gözü)"
        kopru = "Anahtarlık (Keyhole) veya Alçak Köprü"
        renk = "Fırçalanmış Gümüş, Rose Gold, Pastel Tonlar, Açık Karamel"
        oneri = "Güçlü çene hattınızı ve köşeli hatlarınızı yumuşatmak için yuvarlatılmış formlar tercih edilmiştir. Kalın ve kare çerçevelerden uzak durmalısınız."
        
    else:
        yuz_tipi = "Dikdörtgen Yüz"
        form = "Büyük (Oversized) Çerçeveler, Kalın Kemik Dikdörtgenler, Dikey Derinliği Fazla Olan Modeller"
        kopru = "Kalın Hematit / Kalın ve Alçak Yerleşimli Köprü"
        renk = "Koyu Karamel, Mat Siyah, Kalın Asetat Havanna"
        oneri = "Yüzünüzün dikey uzunluğunu dengelemek için geniş ve derinliği fazla olan kalın çerçeveler seçilmiştir. İnce ve küçük gözlükler yüzünüzü daha da uzun gösterir."

    # Veritabanına jilet gibi kaydediyoruz
    conn = sqlite3.connect('opticgrid.db')
    c = conn.cursor()
    c.execute("""INSERT INTO sonuclar (ad, yas, cinsiyet, yuz_tipi, form, kopru, renk, oneri) 
                 VALUES (?,?,?,?,?,?,?,?)""",
               (data.get('ad'), data.get('yas'), data.get('cinsiyet'), yuz_tipi, form, kopru, renk, oneri))
    conn.commit()
    conn.close()
    
    # Ekrana basılması için frontend'e yolluyoruz
    return jsonify({
        "status": "success",
        "yuz_tipi": yuz_tipi,
        "form": form,
        "kopru": kopru,
        "renk": renk,
        "oneri": oneri
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
