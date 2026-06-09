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
    # Yeni zengin analiz sütunlarını veritabanına ekliyoruz
    c.execute('''CREATE TABLE IF NOT EXISTS sonuclar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  ad TEXT, yas TEXT, cinsiyet TEXT, yuz_tipi TEXT, 
                  stil_kimligi TEXT, morfoloji_denge TEXT, kopru_mimarisi TEXT, oneri TEXT,
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
        return "Erişim Reddedildi: Geçersiz Lisans Bilgileri", 401

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
    
    if en_boy_orani is None or ust_alt_orani is None:
        return jsonify({"status": "error", "message": "Tarama verileri eksik geldi."}), 400
    
    # 3 ANA BAŞLIKTA PREMIUM ANALİZ MOTORU
    yuz_tipi = "Belirlenemedi"
    stil_kimligi = ""
    morfoloji_denge = ""
    kopru_mimarisi = ""
    oneri = ""
    
    # 1. SENARYO: YUVARLAK YÜZ
    if 0.92 <= en_boy_orani <= 1.05:
        yuz_tipi = "Yuvarlak Yüz"
        stil_kimligi = "Architectural Modernism (Mimari Modernizm)"
        morfoloji_denge = "Yüzünüzün yumuşak ve dairesel hatlarını dengelemek için net kontrast yaratılması gerekir. Genişlik ve boy oranı birbirine yakın olduğu için dikey bir algı oluşturulmalıdır."
        kopru_mimarisi = "Yüksek ve Düz Yerleşimli Köprü. Gözleri daha ayrık, burnu daha uzun ve yüzü daha dengeli/ince gösteren üst hat yerleşimleri tercih edilmelidir."
        oneri = "Yüzünüze keskinlik katacak kalın köşeli, asetat dikdörtgen veya sert kare çerçeveler seçildi. Yuvarlak formlardan kesinlikle kaçının."
        
    # 2. SENARYO: OVAL YÜZ
    elif en_boy_orani >= 1.25:
        yuz_tipi = "Oval Yüz"
        stil_kimligi = "The Timeless Icon (Zamansız İkon)"
        morfoloji_denge = "Mevcut mükemmel simetriyi, ideal en-boy oranını ve doğal yüz hatlarını korumak esastır. Ekstra bir keskinleştirme veya yumuşatmaya ihtiyaç duymaz."
        kopru_mimarisi = "Standart / Anatomik Köprü. Yüzün doğal dengesini bozmayan, burun kemerine tam oturan geleneksel veya anahtarlık (keyhole) tasarımlar idealdir."
        oneri = "İdeal yüz oranlarınız sayesinde neredeyse her model size yakışır. Aviator, Wayfarer veya modern geometrik (çokgen) formlarla lüksün rafine halini yansıtabilirsiniz."
        
    # 3. SENARYO: KALP YÜZ
    elif 1.05 < en_boy_orani < 1.25 and ust_alt_orani > 1.15:
        yuz_tipi = "Kalp Yüz"
        stil_kimligi = "Minimalist Avant-Garde (Minimalist Avangart)"
        morfoloji_denge = "Geniş alın bölgesini dengelerken, aşağıya doğru daralan ve sivrileşen çene yapısını daha dolgun ve orantılı göstermek amaçlanır."
        kopru_mimarisi = "İnce Metal / Belirsiz Köprü. Alındaki görsel ağırlığı aşağıya çekmek adına üst kısmı hafifleten, dikkati burun ve çene hattına dağıtan tasarımlar."
        oneri = "Alın genişliğini bastırmak için çerçevesiz (rimless), yarım çerçeveli, transparan tonlardaki veya alt kısmı daha hacimli Pantos/çekik modeller seçildi."
        
    # 4. SENARYO: KARE YÜZ
    elif 1.05 < en_boy_orani < 1.25 and ust_alt_orani <= 1.15:
        yuz_tipi = "Kare Yüz"
        stil_kimligi = "Soft Tailoring / Quiet Luxury (Sade Lüks)"
        morfoloji_denge = "Oldukça güçlü, belirgin ve sert olan çene hatlarını, elmacık kemiği köşelerini zarafetle yumuşatmak ve yüz ifadesine anlam katmak hedeflenir."
        kopru_mimarisi = "Anahtarlık (Keyhole) veya Alçak Yerleşimli Köprü. Sert hatları kırmak amacıyla burnu yumuşakça saran ve odak noktasını gözlere çeken tasarımlar."
        oneri = "Güçlü çene hattınızı dengelemek için tam yuvarlak (round), oval veya ince metal çerçeveler tercih edilmiştir. Kalın ve sert kare gözlüklerden uzak durmalısınız."
        
    # 5. SENARYO: DİKDÖRTGEN YÜZ
    else:
        yuz_tipi = "Dikdörtgen Yüz"
        stil_kimligi = "Bold & Cinematic (Görkemli Sinematik)"
        morfoloji_denge = "Yüzün dikey uzunluğunu yatay olarak kesmek, yüzü daha kısa, kompakt ve ideal oranlara yakın göstermek ana stratejidir."
        kopru_mimarisi = "Kalın ve Alçak Yerleşimli Köprü. Yüzü tam ortadan ikiye bölerek dikey derinliği kıran ve yüz uzunluğunu illüzyonla azaltan belirgin köprüler."
        oneri = "Yüzün dikey uzunluğunu dengelemek için geniş, büyük (oversized) ve dikey derinliği fazla olan kalın kemik çerçeveler seçilmiştir. Küçük gözlükler yüzünüzü daha da uzun gösterir."

    # Veritabanına yeni premium başlıklarla kaydediyoruz
    conn = sqlite3.connect('opticgrid.db')
    c = conn.cursor()
    c.execute("""INSERT INTO sonuclar (ad, yas, cinsiyet, yuz_tipi, stil_kimligi, morfoloji_denge, kopru_mimarisi, oneri) 
                 VALUES (?,?,?,?,?,?,?,?)""",
               (data.get('ad'), data.get('yas'), data.get('cinsiyet'), yuz_tipi, stil_kimligi, morfoloji_denge, kopru_mimarisi, oneri))
    conn.commit()
    conn.close()
    
    # Frontend'e ekrana basması için fırlatıyoruz
    return jsonify({
        "status": "success",
        "yuz_tipi": yuz_tipi,
        "stil_kimligi": stil_kimligi,
        "morfoloji_denge": morfoloji_denge,
        "kopru_mimarisi": kopru_mimarisi,
        "oneri": oneri
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
