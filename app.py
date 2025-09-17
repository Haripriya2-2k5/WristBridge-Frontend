# frontend/app.py
import streamlit as st
import requests
import time
from streamlit_folium import st_folium
import folium
import os

BACKEND = st.sidebar.text_input("Backend URL", value="http://localhost:8000")

st.set_page_config(layout="wide", page_title="WristBridge Caregiver Panel")

st.title("WristBridge — Caregiver Panel (Demo)")

tab = st.sidebar.radio("Page", ["Dashboard", "Send Message", "Simulate Watch"])

def fetch_sos():
    try:
        r = requests.get(f"{BACKEND.rstrip('/')}/sos", timeout=5)
        return r.json()
    except Exception as e:
        st.error("Failed to fetch SOS: " + str(e))
        return []

def fetch_messages():
    try:
        r = requests.get(f"{BACKEND.rstrip('/')}/messages", timeout=5)
        return r.json()
    except Exception as e:
        st.error("Failed to fetch messages: " + str(e))
        return []

if tab == "Dashboard":
    st.header("Recent SOS")
    sos = fetch_sos()
    col1, col2 = st.columns([2,1])
    with col1:
        if not sos:
            st.info("No SOS events")
        else:
            for ev in sos:
                st.write(f"**{ev.get('user_id')}** — {ev.get('note')} — {ev.get('created_at')}")
                st.write(f"Location: {ev.get('lat')}, {ev.get('lon')}")
                if st.button(f"Resolve {ev.get('id')}", key=f"res_{ev.get('id')}"):
                    # naive delete via direct DB? For now just inform user; backend needs delete endpoint
                    st.warning("To resolve, delete from backend (not implemented).")
    with col2:
        st.subheader("Map view")
        m = folium.Map(location=[20.5937,78.9629], zoom_start=5)
        for ev in sos:
            folium.Marker([ev.get('lat'), ev.get('lon')], popup=f"{ev.get('user_id')}: {ev.get('note')}").add_to(m)
        st_folium(m, width=500, height=400)

    st.markdown("---")
    st.header("Recent Messages")
    msgs = fetch_messages()
    if msgs:
        for m in msgs[:50]:
            st.write(f"{m.get('created_at')} — From: {m.get('sender_id')} -> {m.get('recipient_id')}")
            if m.get('text'):
                st.write(m.get('text'))
            if m.get('media_url'):
                st.write("Media:", m.get('media_url'))
                if st.button("Play media", key=m.get('id')):
                    # get filename and stream
                    url = m.get('media_url')
                    fname = os.path.basename(url)
                    r = requests.get(f"{BACKEND.rstrip('/')}/uploads/{fname}")
                    st.audio(r.content)

elif tab == "Send Message":
    st.header("Send text message")
    sender = st.text_input("Sender id", value="user_deaf_1")
    recipient = st.text_input("Recipient id (optional) -- leave blank for broadcast", value="")
    txt = st.text_area("Text")
    if st.button("Send"):
        payload = {"sender_id": sender, "recipient_id": recipient or None, "msg_type": "text", "text": txt}
        r = requests.post(f"{BACKEND.rstrip('/')}/send_message", json=payload)
        st.write(r.json())

    st.markdown("---")
    st.header("Send voice file (simulate blind user voice)")
    up = st.file_uploader("Upload WAV/MP3 to send as voice", type=["wav","mp3"])
    if up is not None:
        if st.button("Send voice"):
            files = {"file": (up.name, up.getvalue(), up.type)}
            data = {"sender_id": sender, "recipient_id": recipient or None}
            r = requests.post(f"{BACKEND.rstrip('/')}/send_voice/", files=files, data=data)
            st.write(r.json())

elif tab == "Simulate Watch":
    st.header("Simulated Watch UI (quick actions)")
    uid = st.text_input("User id", value="user_deaf_1")
    if st.button("Send SOS (simulate)"):
        payload = {"user_id": uid, "lat": 12.9716, "lon": 77.5946, "note": "Simulated SOS from watch"}
        r = requests.post(f"{BACKEND.rstrip('/')}/send_sos", json=payload)
        st.write(r.json())
    st.write("You can use the Send Message page to post message or voice from simulated watch.")
