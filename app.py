import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image

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
st.write("Tölts fel doTERRA dokumentumokat (PDF, Word, TXT) vagy képeket (JPG, PNG), és kérdezz tőlük bármit!")

# --- 2. API Kulcs Kezelése ---
api_key = st.sidebar.text_input("Google Gemini API Kulcs", type="password")

if not api_key:
    st.info("👋 Kérlek, add meg a Gemini API kulcsodat az oldalsávban a folytatáshoz!")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. Fájlfeltöltő (Dokumentumok + Képek) ---
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Tananyagok & Képek feltöltése")

uploaded_files = st.sidebar.file_uploader(
    "Válassz ki vagy húzz ide fájlokat", 
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

context_text = ""
image_list = []
file_count = 0

if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            # PDF olvasás
            if file_extension == 'pdf':
                reader = PdfReader(uploaded_file)
                file_text = ""
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        file_text += text + "\n"
                if file_text:
                    context_text += f"\n--- Forrás (PDF): {uploaded_file.name} ---\n" + file_text
                    file_count += 1
                        
            # Word (.docx) olvasás
            elif file_extension == 'docx':
                doc = Document(uploaded_file)
                file_text = ""
                for paragraph in doc.paragraphs:
                    if paragraph.text:
                        file_text += paragraph.text + "\n"
                if file_text:
                    context_text += f"\n--- Forrás (Word): {uploaded_file.name} ---\n" + file_text
                    file_count += 1
                        
            # Sima szöveg (.txt) olvasás
            elif file_extension == 'txt':
                file_text = uploaded_file.getvalue().decode("utf-8")
                if file_text:
                    context_text += f"\n--- Forrás (TXT): {uploaded_file.name} ---\n" + file_text
                    file_count += 1

            # Képek (JPG, PNG) olvasás
            elif file_extension in ['png', 'jpg', 'jpeg']:
                img = Image.open(uploaded_file)
                image_list.append(img)
                file_count += 1
                
        except Exception as e:
            st.sidebar.error(f"Hiba a(z) {uploaded_file.name} olvasásakor: {e}")

st.sidebar.write(f"📊 **Aktív fájlok/képek száma:** {file_count} db")

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

    # Ha nincsenek feltöltve dokumentumok vagy képek
    if not uploaded_files or (not context_text and not image_list):
        with st.chat_message("assistant"):
            st.warning("⚠️ Még nem töltöttél fel fájlt vagy képet az oldalsávban! Kérlek, tölts fel legalább egy doTERRA anyagot a bal oldalon.")
        st.stop()

    # AI válasz generálása
    with st.chat_message("assistant"):
        with st.spinner("Keresés a tananyagokban és képeken..."):
            try:
                system_instruction = f"""
                Egy segítőkész doTERRA szakértő asszisztens vagy. 
                A feladatod, hogy kizárólag az alábbi TANANYAG szövegek és a feltöltött KÉPEK alapján válaszolj a felhasználó kérdésére.
                Ha a válasz nincs benne az anyagokban, udvariasan mondd el, hogy a feltöltött fájlok/képek között nem található erre információ.
                Mindig hivatkozz rá, hogy melyik forrásból származik az információ!
                
                SZÖVEGES TANANYAGOK:
                {context_text}
                """
                
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                # Összeállítjuk a küldendő tartalmat (Szöveges utasítás + kérdés + képek ha vannak)
                contents = [system_instruction, "Kérdés: " + user_prompt]
                for img in image_list:
                    contents.append(img)
                
                response = model.generate_content(contents)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Hiba történt a válaszadás során: {str(e)}")
