import google.generativeai as genai
import json
import os
import re
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Google Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Store conversation history
conversation_history = []
user_preferences = {}
details_collected = False
activities_selected = False


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
    global conversation_history, user_preferences, details_collected, activities_selected

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
        system_prompt = """
        Now that I have your trip details, let's plan activities!
        
        - Suggest relevant activities for {destination} along with open timings.
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
        """
    
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    formatted_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_history])
    response = model.generate_content([f"{system_prompt}\n{formatted_history}\nUser: {user_input}"])
    
    conversation_history.append({"role": "assistant", "content": response.text})

    json_output, json_extracted = extract_json(response.text)
    if json_extracted:
        for key, value in json_output.items():
            user_preferences[key] = value
        if not details_collected:
            details_collected = True
        elif not activities_selected:
            activities_selected = True
        else:
            return response.text, True
    
    return response.text, False


print("👋 Hello, I am your travel assistant. What's your dream destination?")
while True:
    user_input = input("You: ")
    if any(phrase in user_input.strip().lower() for phrase in ["exit", "quit", "done", "thanks", "bye"]):
        print("\n👋 Alright! Have a great day and safe travels! ✈️")
        break
    response, completed = travel_assistant(user_input)
    print("AI:", response)
    
    if completed:
        print("\n✅ Itinerary ready! Here’s your trip plan:")
        print(response)
        break
