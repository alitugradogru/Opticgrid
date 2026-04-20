import streamlit as st
import cv2
import numpy as np

# Sayfa Yapılandırması
st.set_page_config(page_title="OpticGrid | Admin Login", layout="centered")

# --- SESSION STATE KONTROLÜ ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 1. AŞAM: ADMIN GİRİŞ EKRANI (KALDIRMAK İSTEDİĞİN KISIM BUYDU) ---
if not st.session_state.logged_in:
    st.title("OpticGrid Admin Paneli")
    st.subheader("Lütfen giriş yapın")
    
    with st.form("login_form"):
        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
        login_button = st.form_submit_button("Giriş Yap")
        
        if login_button:
            # Örnek basit kontrol
            if username == "admin" and password == "1234":
                st.session_state.logged_in = True
                st.success("Giriş başarılı!")
                st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre.")

# --- 2. AŞAM: SİSTEM ANA EKRANI ---
else:
    st.sidebar.button("Çıkış Yap", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.title("OpticGrid | Optik Analiz Sistemi")
    
    tab1, tab2 = st.tabs(["Yüz Analizi", "Müşteri Kayıtları"])
    
    with tab1:
        st.write("### Canlı Kamera Analizi")
        img_file = st.camera_input("Analiz Başlat")
        if img_file:
            st.info("Görüntü işleniyor...")
            
    with tab2:
        st.write("### Kayıtlı Müşteriler")
        st.write("Henüz kayıtlı müşteri bulunmuyor.")
