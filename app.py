# Import the necessary libraries
from flask import Flask, render_template, request
from flask_cors import CORS
from openai import OpenAI
import time
import speech_recognition as sr
import pyttsx3
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather


app = Flask(__name__)
CORS(app)

# OpenAI API key and Assistant ID
api_key = "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"
assistant_id = "asst_7jRqbGVgJasJTE7NRYJXoXDQ"
openai_client = OpenAI(api_key=api_key)

# Twilio credentials
TWILIO_ACCOUNT_SID = "AC3c5ee5a0e9bed2bd729dfd69fa3a8420"
TWILIO_AUTH_TOKEN = "5d0378bc91398311c528e16266a5ab49"
TWILIO_PHONE_NUMBER = "+1 9089230665"
CANDIDATE_PHONE_NUMBER = "+91 9561214824"

# Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Function to make voice call using Twilio
def make_phone_call(text, action_url):
    call = twilio_client.calls.create(
        to=CANDIDATE_PHONE_NUMBER,
        from_=TWILIO_PHONE_NUMBER,
        twiml=f'''
            <Response>
                <Say>{text}</Say>
                <Pause length="1"/> <!-- Add a pause after the intro message -->
                <Gather action="{action_url}" method="POST" input="speech">
                    <Say>Please respond to the questions using your voice or keypad.</Say>
                </Gather>
            </Response>
        '''
    )
    print("call sid: ", call.sid)
    return call.sid

# Function to update phone call
def update_phone_call(sid, text):
    call = twilio_client.calls(sid).update(
        twiml=f'<Response><Say>{text}</Say></Response>'
    )

@app.route("/voice", methods=['GET', 'POST'])
def answer_phone_call():
    # Start our TwiML response
    resp = VoiceResponse()
    print("initial response: ", resp)

    speech_result = request.form['SpeechResult']

    # Read a message aloud to the caller
    resp.gather(speech_result)

    print("answer phone call: ", resp)
    return str(resp)

# Function to check whether the Run is completed or not
def poll_run(run, thread):
    while run.status != "completed":
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

# Voice assistant functionality
def voice_assistant():
    r = sr.Recognizer()

    # Adjust the energy_threshold value according to your environment
    with sr.Microphone() as source:
        print('Listening....')
        r.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        r.energy_threshold = 300  # Adjust the energy threshold based on your environment
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
        call_sid = make_phone_call(intro_message, "https://5643-103-198-166-176.ngrok-free.app/voice")

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
            phone_answer = answer_phone_call()
            print("Candidate's Answer: ", phone_answer)

            # If the user's answer is not "None," proceed with generating the assistant's response
            if phone_answer:
                assistant_response = reply(phone_answer, thread, previous_response)
                speak(assistant_response)
                print("Call SID: ", call_sid)
                update_phone_call(call_sid, assistant_response)
                previous_response = assistant_response

                # Check if the OpenAI Assistant wants to end the interview
                if "INTERVIEW ENDED" in assistant_response:
                    speak("Thank you for your time. The interview is complete.")
                    update_phone_call(call_sid, "Thank you for your time. The interview is complete.")
                    break

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)