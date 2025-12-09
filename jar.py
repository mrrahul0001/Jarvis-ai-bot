import streamlit as st
import google.generativeai as genai
from ddgs import DDGS
import wikipedia

# --- 1. CONFIG ---
st.set_page_config(page_title="JARVIS AI", page_icon="🤖")
st.title("🤖 JARVIS: The AI Agent")

# --- 2. SECURE SETUP ---
# Nayi Key yahan daalo (Purani delete kar dena)
# Hum Cloud ki Tijori (Secrets) se key mangenge
MY_API_KEY = st.secrets["GOOGLE_API_KEY"]

try:
    genai.configure(api_key=MY_API_KEY)
except:
    st.error("API Key missing!")

# --- 3. TOOLS ---
def search_internet(query):
    try:
        # DDGS kabhi kabhi heavy load par fail hota hai, isliye safe handling
        results = DDGS().text(query, region='in-en', max_results=3)
        if results:
            data = ""
            for r in results:
                data += f"Title: {r['title']}\nInfo: {r['body']}\n\n"
            return data
        return "No results found."
    except Exception as e:
        return f"Search Error: {e}"

def search_wikipedia(query):
    try:
        return wikipedia.summary(query, sentences=2)
    except:
        return "Wiki page not found."

tools_list = [search_internet, search_wikipedia]

# --- 4. SMART MODEL LOADING (Cache) ---
# @st.cache_resource ka matlab: "Ye connection ek baar banao, baar-baar nahi"
# Isse tumhara quota bachega jab tum code edit karoge.
@st.cache_resource
def load_model():
    # Hum 'system_instruction' yahi de denge.
    # Isse alag se message bhejne ki zaroorat nahi padegi (No Quota Wasted).
    model = genai.GenerativeModel(
        'gemini-2.5-flash', # 1.5 Flash sabse stable hai free tier ke liye
        tools=tools_list,
        system_instruction="You are JARVIS. Use tools for news/facts. Reply in Hinglish."
    )
    return model

model = load_model()

# --- 5. CHAT SESSION ---
if "chat" not in st.session_state:
    st.session_state.messages = []
    # Yahan hum koi message nahi bhej rahe, bas chat start kar rahe hain
    st.session_state.chat = model.start_chat(enable_automatic_function_calling=True)

# --- 6. DISPLAY HISTORY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 7. USER INPUT ---
user_input = st.chat_input("Pucho sawal...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Thinking... ⏳")
        
        try:
            # Message bhejo
            response = st.session_state.chat.send_message(user_input)
            ai_reply = response.text
            placeholder.markdown(ai_reply)
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            
        except Exception as e:
            # Agar abhi bhi error aaye, toh user ko batao wait kare
            placeholder.error(f"Error: {e}")
            if "429" in str(e):
                st.error("🛑 Quota Khatam! 1-2 minute ruko ya nayi key lagao.")