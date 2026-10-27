import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. Oldal beállításai ---
st.set_page_config(
    page_title="doTERRA Tudástár & Kereső",
    page_icon="🌿",
    layout="wide"
)

# Egyedi stílus (doTERRA zöld színek)
st.markdown("""
    <style>
    .main { background-color: #f8fbf9; }
    .stButton>button { background-color: #4A6B5D; color: white; border-radius: 8px; }
    .stTextInput>div>div>input { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("🌿 doTERRA Csapat Tudástár & AI Kereső")
st.write("Töltsd fel a doTERRA PDF tananyagokat a bal oldali sávban, és kérdezz tőlük bármit!")

# --- 2. API Kulcs Kezelése ---
api_key = st.sidebar.text_input("Google Gemini API Kulcs", type="password")

if not api_key:
    st.info("👋 Kérlek, add meg a Gemini API kulcsodat az oldalsávban a folytatáshoz!")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. Fájlfeltöltő a webes felületen ---
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Tananyagok feltöltése")

uploaded_files = st.sidebar.file_uploader(
    "Válassz ki vagy húzz ide doTERRA PDF fájlokat", 
    type=["pdf"], 
    accept_multiple_files=True
)

context_text = ""
file_count = 0

if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    context_text += f"\n--- Forrás: {uploaded_file.name} ---\n" + text
            file_count += 1
        except Exception as e:
            st.sidebar.error(f"Hiba a(z) {uploaded_file.name} olvasásakor: {e}")

st.sidebar.write(f"📊 **Aktív tananyagok:** {file_count} db PDF")

# --- 4. Chat / Kereső felület ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Korábbi üzenetek megjelenítése
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kérdés bevitele
if user_prompt := st.chat_input("Pl.: Melyik olaj jó alvásproblémákra?"):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Ha nincsenek feltöltve dokumentumok a weboldalon
    if not uploaded_files or not context_text:
        with st.chat_message("assistant"):
            st.warning("⚠️ Még nem töltöttél fel PDF fájlt az oldalsávban! Kérlek, húzz be vagy tölts fel legalább egy doTERRA anyagot a bal oldalon.")
        st.stop()

    # AI válasz generálása
    with st.chat_message("assistant"):
        with st.spinner("Keresés a tananyagban..."):
            try:
                system_instruction = f"""
                Egy segítőkész doTERRA szakértő asszisztens vagy. 
                A feladatod, hogy kizárólag az alábbi TANANYAG alapján válaszolj a felhasználó kérdésére.
                Ha a válasz nincs benne a tananyagban, udvariasan mondd el, hogy a feltöltött fájlok között nem található erre információ.
                Mindig hivatkozz rá, hogy melyik fájlból származik az információ!
                
                TANANYAG:
                {context_text}
                """
                
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(system_instruction + "\n\nKérdés: " + user_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Hiba történt a válaszadás során: {str(e)}")
