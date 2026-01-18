
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

try:
    # Get the API key from the environment variable
    api_key = os.environ["GEMINI_API_KEY"]
except KeyError:
    print("Error: The GEMINI_API_KEY environment variable is not set.")
    print("Please set it before running the script.")
    exit()

# Configure the generative AI library
genai.configure(api_key=api_key)

# Create a Gemini Pro model
model = genai.GenerativeModel('models/gemini-pro-latest')

# Generate content
print("Generating content with Gemini...")
response = model.generate_content("Tell me a fun fact about the Roman Empire.")

# Print the response
print(response.text)
