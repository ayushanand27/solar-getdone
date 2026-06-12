import streamlit as st

st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

from groq import Groq

from utils.app_state import setup_app

SUGGESTED_QUESTIONS = [
    "Should I export energy now?",
    "Is there a storm coming?",
    "How much H₂ can I generate today?",
    "What's my farm health status?",
]

ctx = setup_app()

h2_kg = ctx.get("h2_kg", round(sum(r * 0.22 * 0.7 for r in ctx["radiation"] if r > 100) / 1000, 2))
battery_level = ctx.get("battery_level", min(100, int(ctx["solar_output"] / 2)))
h2_level = ctx.get("h2_level", min(100, int(h2_kg * 40)))
health_score = ctx.get("health_score", 0)
health_grade = ctx.get("health_grade", "—")
sim_event = ctx.get("sim_event") or st.session_state.get("sim_event")
cv_threat = ctx.get("cv_threat")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def build_system_prompt():
    threat_note = ""
    if sim_event == "bird" or cv_threat == "bird":
        threat_note = f"Bird detected at {ctx['city_name']}. Shield on standby.\n"
    elif sim_event == "dust" or cv_threat == "dust":
        threat_note = f"Dust storm at {ctx['city_name']}. 25% efficiency loss.\n"

    return (
        "You are Solar OS AI Assistant — an expert in solar farm "
        "management, energy optimization, and edge AI. You have "
        "access to the current farm data:\n"
        f"Location: {ctx['city_name']}\n"
        f"Solar Output: {ctx['solar_output']} W/m²\n"
        f"Shield Status: {ctx['shield']}\n"
        f"Threat Level: {ctx['threat_level']}\n"
        f"Simulated Event: {sim_event or 'None'}\n"
        f"CV Threat: {cv_threat or 'None'}\n"
        f"Energy Mode: {ctx['mode']}\n"
        f"Temperature: {ctx['temp']}°C\n"
        f"Wind: {ctx['wind']} km/h\n"
        f"Battery: {battery_level}%\n"
        f"H₂ Tank: {h2_level}%\n"
        f"H₂ Generated Today: {h2_kg} kg\n"
        f"Health Score: {health_score}/100 ({health_grade})\n"
        f"Grid Tier: {ctx.get('grid_period', 'Unknown')} (₹{ctx.get('grid_price', 7)}/kWh)\n"
        f"{threat_note}"
        "\n"
        "Answer questions about the farm, energy decisions, "
        "weather, and solar optimization. Be concise and practical."
    )


def ask_groq(user_input):
    try:
        client = Groq(api_key=st.secrets["groq"]["api_key"])
        messages = [{"role": "system", "content": build_system_prompt()}] + st.session_state.chat_history
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=300,
        )
        return response.choices[0].message.content
    except (KeyError, FileNotFoundError, AttributeError):
        return "Groq API key not configured. Add `[groq] api_key` to `.streamlit/secrets.toml`."
    except Exception as exc:
        return f"Sorry, I couldn't reach the AI service. ({exc})"


def handle_user_message(user_input):
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    reply = ask_groq(user_input)
    st.session_state.chat_history.append({"role": "assistant", "content": reply})


st.title("🤖 Solar OS AI Assistant")
st.caption(f"Ask about your farm — live data for 📍 {ctx['city_name']}")

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.markdown("**Suggested questions**")
s1, s2 = st.columns(2)
for i, question in enumerate(SUGGESTED_QUESTIONS):
    col = s1 if i % 2 == 0 else s2
    with col:
        if st.button(question, key=f"suggest_{i}", use_container_width=True):
            st.session_state.pending_question = question

pending = st.session_state.pop("pending_question", None)
user_input = pending or st.chat_input("Ask about energy, weather, or farm optimization…")

if user_input:
    handle_user_message(user_input)
    st.rerun()
