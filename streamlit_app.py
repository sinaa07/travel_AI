import google.generativeai as genai
import json
import os
import re
import streamlit as st
from dotenv import load_dotenv

api_key = st.secrets["secrets"]["gemini_api_key"]
genai.configure(api_key=api_key)

# Initialize chat history and user preferences in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
    ]

if "user_preferences" not in st.session_state:
    st.session_state.user_preferences = {}

if "details_collected" not in st.session_state:
    st.session_state.details_collected = False

if "activities_selected" not in st.session_state:
    st.session_state.activities_selected = False


def extract_json(response_text):
    """Extracts and parses JSON from the LLM's response."""
    try:
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        json_output = json.loads(response_text[json_start:json_end])
        return json_output, True
    except (ValueError, json.JSONDecodeError): 
        return None, False


def travel_assistant(user_input):
    
    # Retrieve session state variables
    details_collected = st.session_state.details_collected
    activities_selected = st.session_state.activities_selected
    user_preferences = st.session_state.user_preferences

    if not details_collected:
        system_prompt = """
        You are a highly personalized AI travel assistant.
        Your task is to extract travel details step-by-step while having a natural conversation.
        
        If any key detail is missing, ask a concise follow-up question.

        Extracted Details:
        - Destination
        - Source Location
        - Travel dates
        - Budget (low, mid-range, luxury)
        - Food preferences or dietary restrictions
        - Accommodation preference (hotel, Airbnb, hostel, resort)
        - Allergies of any kind
        - Transportation (flights, trains, self-drive, etc.)
        - Special requirements (accessibility, pet-friendly, etc.)

        Rules:
        - Engage naturally and enthusiastically.
        - Use emojis, but not too much.
        - Avoid repeating questions unnecessarily.
        - Once all details are collected, summarize the trip and transition to activity suggestions.
        """
    elif not activities_selected:
        system_prompt = f"""
        Now that I have your trip details, let's plan activities!
        
        - Suggest relevant activities for {user_preferences.get("destination", "your destination")} along with open timings.
        - Keep the activities latest and up to date with the destination.
        - Use emojis, but not too much.
        - User can pick from the suggestions or add their own.
        - Ensure activities fit within the budget preference.
        - Once activities are confirmed, move to itinerary generation.
        """.format(destination=user_preferences.get("destination", "your destination"))
    else:
        system_prompt = """
        Based on your preferences, I will generate a detailed itinerary.
        - Include day-by-day plans with time slots.
        - Ensure activities align with user preferences.
        - Keep the itinerary practical and enjoyable.
        - Make sure to provide estimated time slots for each activity for each day.
        - Give important considerations after the itinerary.
        """
    
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    formatted_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.chat_history])
    response = model.generate_content([f"{system_prompt}\n{formatted_history}\nUser: {user_input}"])
    
    st.session_state.chat_history.append({"role": "assistant", "content": response.text})

    json_output, json_extracted = extract_json(response.text)
    if json_extracted:
        for key, value in json_output.items():
            st.session_state.user_preferences[key] = value
        
        if not st.session_state.details_collected:
            st.session_state.details_collected = True
        elif not st.session_state.activities_selected:
            st.session_state.activities_selected = True
        else:
            return response.text, True

    return response.text, False

####################

# Streamlit UI
st.title("Your Personal Travel Planner! 🌍✈️")
st.write("✨ Hey there! Ready to plan your next adventure? Tell me your destination, and I'll craft the perfect itinerary for you! ✈️")

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input field
user_input = st.chat_input("Type your message...", key="unique_key_1")

if user_input:
    # Append user message and display it immediately
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Get AI response
    response_message, _ = travel_assistant(user_input)

    # Append AI response and display it
    with st.chat_message("assistant"):
        st.write(response_message)

####################
