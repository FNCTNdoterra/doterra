import streamlit as st
import google.generativeai as genai
import os
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
st.write("Kérdezz bármit a feltöltött tananyagokból, termékismertetőkből vagy üzleti útmutatókból!")

# --- 2. API Kulcs Kezelése ---
# Az API kulcsot a Streamlit Secrets-ből vagy a sidebar-ból kérjük be
api_key = st.sidebar.text_input("Google Gemini API Kulcs", type="password")

if not api_key:
    st.info("👋 Kérlek, add meg a Gemini API kulcsodat az oldalsávban a folytatáshoz! (Ez teljesen ingyenes)")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. Dokumentumok betöltése és feldolgozása ---
@st.cache_data
def load_docs():
    """Beolvassa a 'docs' mappában lévő összes PDF fájlt."""
    text_content = ""
    docs_folder = "docs"
    
    if not os.path.exists(docs_folder):
        os.makedirs(docs_folder)
        
    pdf_files = [f for f in os.listdir(docs_folder) if f.endswith('.pdf')]
    
    if not pdf_files:
        return None, 0
        
    for pdf_file in pdf_files:
        reader = PdfReader(os.path.join(docs_folder, pdf_file))
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content += f"\n--- Forrás: {pdf_file} ---\n" + text
                
    return text_content, len(pdf_files)

# Fájlok beolvasása
context_text, file_count = load_docs()

st.sidebar.markdown("---")
st.sidebar.write(f"📁 **Betöltött tananyagok:** {file_count} db PDF")

# --- 4. Chat / Kereső felület ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Korábbi üzenetek megjelenítése
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kérdés bevitele
if user_prompt := st.chat_input("Pl.: Melyik olaj jó alvásproblémákra?"):
    # Felhasználó kérdésének megjelenítése
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Ha nincsenek feltöltött dokumentumok
    if not context_text:
        with st.chat_message("assistant"):
            st.error("Még nincsenek feltöltve PDF fájlok a 'docs' mappába! Kérlek, tölts fel anyagokat a projekthez.")
        st.stop()

    # AI válasz generálása
    with st.chat_message("assistant"):
        with st.spinner("Keresés a tananyagban..."):
            try:
                # Szigorú Prompt a tananyag használatára
                system_instruction = f"""
                Egy segítőkész doTERRA szakértő asszisztens vagy. 
                A feladatod, hogy kizárólag az alábbi TANANYAG alapján válaszolj a felhasználó kérdésére.
                Ha a válasz nincs benne a tananyagban, udvariasan mondd el, hogy a meglévő doTERRA fájlok között nem található erre információ.
                Mindig hivatkozz rá, hogy melyik fájlból származik az információ, ha lehetséges!
                
                TANANYAG:
                {context_text}
                """
                
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(system_instruction + "\n\nKérdés: " + user_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Hiba történt a válaszadás során: {str(e)}")