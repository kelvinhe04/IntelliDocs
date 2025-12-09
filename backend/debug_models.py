import google.generativeai as genai
import os

# Using the key provided by user
API_KEY = "AIzaSyB_GzkU8lg_xxW9vnZaMPbJwsQ40ZtyrZg"
genai.configure(api_key=API_KEY)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
