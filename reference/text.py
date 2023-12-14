from flask import Flask, render_template, request
import pandas as pd
from flask_cors import CORS
from openai import OpenAI
import twilio
import time

app = Flask(__name__)
CORS(app)

# OpenAI API key
api_key = "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"
openai_client = OpenAI(api_key=api_key)

# creating a function to check whether the Run is completed or not
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
def generate_interview_script():
    instruction = f"You are Jarvis, an AI assistant acting as an HR representative for conducting phone interviews. Today, you are interviewing candidates for the position of a Laravel Developer. Your task is to ask relevant questions about their experience, technical skills, and problem-solving abilities in a conversational manner. After the interview, provide a summary of the candidate's qualifications, give a rating on a scale of 1 to 5 based on their responses, and if they seem suitable, inquire about their availability for a second interview. Remember to maintain a professional and unbiased tone throughout the call. You should not answer anything irrelevant to the interview."
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
    for m in messages:
        print(f"{m.role}: {m.content[0].text.value}")


generate_interview_script()

if __name__ == '__main__':
    app.run(debug=True)
