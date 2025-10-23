"""Streamlit fan portal for Papito Mamito."""

import json
from typing import Any

import requests
import streamlit as st

API_BASE = st.secrets.get("api_base", "http://localhost:8000")
API_KEY = st.secrets.get("api_key")
HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}


def call_api(method: str, path: str, **kwargs: Any) -> Any:
    """Helper to call the Papito API and surface errors to the UI."""

    response = requests.request(method, f"{API_BASE}{path}", headers=HEADERS, **kwargs)
    if not response.ok:
        st.error(f"Request failed: {response.status_code} - {response.text}")
        return None
    try:
        return response.json()
    except json.JSONDecodeError:
        return response.text


st.title("Papito Mamito Fan Portal")
st.caption("Value over vanity, always.")

tabs = st.tabs(["Daily Blessing", "Request Groove", "Supporters", "Merch"])

with tabs[0]:
    st.header("Generate Today's Blessing")
    title = st.text_input("Blog title", value="Gratitude Rising")
    focus_track = st.text_input("Focus track", value="We Rise!")
    theme = st.text_input("Gratitude theme", value="Thankful for the tribe.")
    if st.button("Create Blessing"):
        payload = {
            "title": title,
            "focus_track": focus_track,
            "gratitude_theme": theme,
        }
        data = call_api("POST", "/blogs", json=payload)
        if data:
            st.success("Blessing generated!")
            st.markdown(data.get("body", ""))

with tabs[1]:
    st.header("Request a New Groove")
    mood = st.selectbox("Mood", ["uplifting", "chill", "romantic", "anthemic"])
    theme = st.text_input("Theme focus", value="gratitude")
    generate_audio = st.checkbox("Generate audio (requires Suno credentials)")
    poll = st.checkbox("Poll for audio completion", value=True)
    if st.button("Create Groove"):
        payload = {"mood": mood, "theme_focus": theme}
        params = {"generate_audio": generate_audio, "poll": poll}
        data = call_api("POST", "/songs/ideate", json=payload, params=params)
        if data:
            st.json(data)
            audio = data.get("audio_result") or {}
            url = audio.get("audio_url")
            if url:
                st.audio(url)

with tabs[2]:
    st.header("Fan Shout-outs")
    fans = call_api("GET", "/fans") or []
    if not fans:
        st.info("No supporters recorded yet. Add some via the CLI or API.")
    for fan in fans:
        st.write(
            f"🎉 {fan['name']} ({fan['support_level']}) - "
            f"{fan.get('favorite_track') or 'No favourite yet'}"
        )

with tabs[3]:
    st.header("Merch Highlights")
    merch = call_api("GET", "/merch") or []
    if not merch:
        st.info("Merch catalog is empty. Add items via `papito merch add`.")
    for item in merch:
        st.subheader(item["name"])
        st.write(item["description"])
        st.write(f"Price: {item['price']} {item['currency']}")
        if item.get("url"):
            st.markdown(f"[Buy now]({item['url']})")
