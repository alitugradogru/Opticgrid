import streamlit as st
import cv2
import numpy as np

# Sayfa Yapılandırması (Giriş ekranı bypass edildi)
st.set_page_config(page_title="OpticGrid | Müşteri Analiz Paneli", layout="wide")

# --- STİL AYARLARI (Lüks Görünüm) ---
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #000; color: white; }
    h1 { color: #1a1a1a; font-family: 'Helvetica'; }
    </style>
    """, unsafe_allow_status_html=True)

# --- SESSION STATE KONTROLÜ ---
if 'step' not in st.session_state:
    st.session_state.step = 'customer_info'
if 'customer_data' not in st.session_state:
    st.session_state.customer_data = {}

# --- 1. ADIM: MÜŞTERİ BİLGİ FORMU ---
if st.session_state.step == 'customer_info':
    st.title("OpticGrid - Yeni Müşteri Kaydı")
    st.subheader("Analize başlamak için lütfen temel bilgileri girin.")
    
    with st.form("customer_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Ad Soyad")
            phone = st.text_input("Telefon Numarası")
        with col2:
            email = st.text_input("E-posta")
            age = st.number_input("Yaş", min_value=0, max_value=120)
        
        notes = st.text_area("Özel Notlar (Tercih edilen markalar, gözlük geçmişi vb.)")
        
        submit_button = st.form_submit_button("Analize Geç")
        
        if submit_button:
            if name and phone:
                st.session_state.customer_data = {
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "age": age,
                    "notes": notes
                }
                st.session_state.step = 'analysis'
                st.rerun()
            else:
                st.error("Lütfen en az Ad ve Telefon bilgilerini doldurun.")

# --- 2. ADIM: ANALİZ VE ÜRÜN ÖNERİSİ ---
elif st.session_state.step == 'analysis':
    st.sidebar.title("Müşteri Kartı")
    st.sidebar.write(f"**İsim:** {st.session_state.customer_data['name']}")
    st.sidebar.write(f"**Tel:** {st.session_state.customer_data['phone']}")
    if st.sidebar.button("Yeni Müşteri Kaydı"):
        st.session_state.step = 'customer_info'
        st.rerun()

    st.title("Yüz Analizi ve Optik Önerisi")
    
    col_cam, col_rec = st.columns([2, 1])
    
    with col_cam:
        st.write("### Canlı Kamera Analizi")
        img_file = st.camera_input("Yüz Hatlarını Analiz Et")
        
        if img_file:
            st.success("Yüz hatları başarıyla analiz edildi: **Köşeli Yüz Formu**")
            # Burada ileride facial_mesh fonksiyonlarını çağıracağız

    with col_rec:
        st.write("### Önerilen Modeller")
        st.info("Yüz tipine göre seçilen Dior ve Valentino koleksiyonları:")
        
        # Temsili Ürün Kartları
        st.image("https://via.placeholder.com/150", caption="Model #1: Dior Homme Classic")
        st.image("https://via.placeholder.com/150", caption="Model #2: Valentino Aviator")
        
        if st.button("Seçimi Kaydet ve Bitir"):
            st.success(f"{st.session_state.customer_data['name']} için analiz kaydedildi.")
