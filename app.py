# Import the necessary libraries
from flask import Flask, render_template, request
from flask_cors import CORS
from openai import OpenAI
import time
import speech_recognition as sr
from gtts import gTTS
import os
import pyttsx3

app = Flask(__name__)
CORS(app)

# OpenAI API key and Assistant ID
api_key = "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"
assistant_id = "asst_7jRqbGVgJasJTE7NRYJXoXDQ"
openai_client = OpenAI(api_key=api_key)

# Function to check whether the Run is completed or not
def poll_run(run, thread):
    while run.status != "completed":
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

# Function to make voice call using gTTS
def make_voice_call(interview_script):
    tts = gTTS(text=interview_script, lang='en', slow=False)
    tts.save('interview_script.mp3')
    os.system('start interview_script.mp3')
    os.remove('interview_script.mp3')

# Voice assistant functionality
def voice_assistant():
    r = sr.Recognizer()

    # Adjust the energy_threshold value according to your environment
    with sr.Microphone() as source:
        print('Listening....')
        r.adjust_for_ambient_noise(source, duration=1)  # Adjust for ambient noise
        r.energy_threshold = 500  # Adjust the energy threshold based on your environment
        audio = r.listen(source, timeout=None)

    try:
        print("Recognizing.....")
        query = r.recognize_google(audio, language='en-in')
        return query
    except Exception as e:
        print("Say That Again....")
        return "None"


# Function to make voice call using pyttsx3 (text-to-speech)
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# OpenAI Assistant for generating responses
def reply(query, thread, previous_response=""):
    message = openai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=query
    )
    run = openai_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    run = poll_run(run, thread)
    messages = openai_client.beta.threads.messages.list(thread_id=thread.id)
    response = ""

    for m in messages:
        if m.role == "assistant" and m.content[0].text.value != query and m.content[0].text.value != previous_response:
            response = f"{m.content[0].text.value}"
            print(response)
            return response

    if not response:
        response = reply("I didn't understand that. Can you please repeat?", thread, previous_response)
        return response

    return response

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get form input values
        position = request.form.get('position')
        experience = request.form.get('experience')

        # Generate dynamic introductory message
        intro_message = f"Hello, we are conducting an interview for the position of {position}. " \
                        f"We are looking for candidates with at least {experience} years of experience."
        speak(intro_message)

        # update Assistant
        instruction = f"You are Jarvis, an AI assistant acting as an HR representative for conducting phone interviews. Today, you are interviewing candidates for the position of a {position} with {experience} years of experience. Your task is to ask relevant questions about their experience, technical skills, and problem-solving abilities in a conversational manner. After the interview, provide a summary of the candidate's qualifications, give a rating on a scale of 1 to 5 based on their responses, and if they seem suitable, inquire about their availability for a second interview. Remember to maintain a professional and unbiased tone throughout the call. You should not answer anything irrelevant to the interview."
        assistant = openai_client.beta.assistants.update(
            assistant_id,
            instructions=instruction
        )
        thread = openai_client.beta.threads.create()
        previous_response = ""

        # Interview loop
        while True:
            user_answer = voice_assistant()
            print("Candidate's Answer: ", user_answer)

            # If the user's answer is not "None," proceed with generating the assistant's response
            if user_answer != None:
                assistant_response = reply(user_answer, thread, previous_response)
                speak(assistant_response)
                previous_response = assistant_response

                # Check if the OpenAI Assistant wants to end the interview
                if "INTERVIEW ENDED" in assistant_response:
                    speak("Thank you for your time. The interview is complete.")
                    break

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
