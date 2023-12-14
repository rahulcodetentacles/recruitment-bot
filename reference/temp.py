from flask import Flask, render_template, request
import pandas as pd
from flask_cors import CORS
from openai import OpenAI
from twilio.rest import Client
import time
import speech_recognition as sr
from gtts import gTTS
import os

app = Flask(__name__)
CORS(app)

# OpenAI API key
api_key = "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"
openai_client = OpenAI(api_key=api_key)

# Twilio credentials
twilio_account_sid = 'ACf26ff875de67d99c3e74e2219d1c224a'
twilio_auth_token = 'a881445337442d0f562e11d9316fe39c'
twilio_phone_number = 'YOUR_TWILIO_PHONE_NUMBER'
twilio_client = Client(twilio_account_sid, twilio_auth_token)

# Function to check whether the Run is completed or not
def poll_run(run, thread):
    while run.status != "completed":
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

# Load candidate data from Excel
def load_candidates(file_path):
    return pd.read_excel(file_path)

# Call OpenAI API to generate interview script
def generate_interview_script(position, experience):
    instruction = f"You are an HR recruiter conducting an interview for a {position} position with {experience} years of experience."
    assistant = openai_client.beta.assistants.create(
        name="HR Interviewer",
        instructions=instruction,
        model="gpt-3.5-turbo",
    )
    thread = openai_client.beta.threads.create()

    message = openai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="hi"
    )
    run = openai_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    run = poll_run(run, thread)
    messages = openai_client.beta.threads.messages.list(thread_id=thread.id)
    interview_script = ""
    for m in messages:
        interview_script += f"{m.role}: {m.content[0].text.value}\n"
    return interview_script

# Make voice call using Twilio
def make_voice_call(candidate_name, candidate_phone, interview_script):
    # Convert interview script to speech using gTTS
    tts = gTTS(text=interview_script, lang='en', slow=False)
    tts.save('interview_script.mp3')

    # Use Twilio API to make a voice call and play the interview script
    call = twilio_client.calls.create(
        to=candidate_phone,
        from_=twilio_phone_number,
        twiml=f'<Response><Play>interview_script.mp3</Play></Response>'
    )

    # Remove the generated interview script file after the call is made
    os.remove('interview_script.mp3')

    return call.sid

# Voice assistant functionality
def voice_assistant():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print('Listening....')
        r.pause_threshold = 1
        audio = r.listen(source)
    try:
        print("Recognizing.....")
        query = r.recognize_google(audio, language='en-in')
        print("User Said: {} \n".format(query))
    except Exception as e:
        print("Say That Again....")
        return "None"
    return query

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        position = request.form['position']
        experience = request.form['experience']
        excel_file = request.files['excel_file']

        # Process Excel file and get candidate information
        candidates = load_candidates(excel_file)

        # Generate interview script based on position and experience
        interview_script = generate_interview_script(position, experience)

        # Call candidates and conduct interviews
        for index, candidate in candidates.iterrows():
            make_voice_call(candidate['name'], str(candidate['phone']), interview_script)

        return "Interviews initiated successfully!"

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
