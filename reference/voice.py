from openai import OpenAI
import pyttsx3
import speech_recognition as sr
import webbrowser

# OpenAI API key
api_key = "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"
openai_client = OpenAI(api_key=api_key)

def Reply(question):
    prompt=f'Chando: {question}\n Jarvis: '
    response=openai_client.chat.completions(prompt=prompt, engine="text-davinci-002", stop=['\Chando'], max_tokens=200)
    answer=response.choices[0].text.strip()
    return answer

engine=pyttsx3.init('sapi5')
voices=engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

def speak(text):
    engine.say(text)
    engine.runAndWait()

speak("Hello How Are You? ")

def takeCommand():
    r=sr.Recognizer()
    with sr.Microphone() as source:
        print('Listening....')
        r.pause_threshold = 1
        audio = r.listen(source)
    try:
        print("Recognizing.....")
        query=r.recognize_google(audio, language='en-in')
        print("Chando Said: {} \n".format(query))
    except Exception as e:
        print("Say That Again....")
        return "None"
    return query


if __name__ == '__main__':
    while True:
        query=takeCommand().lower()
        ans=Reply(query)
        print(ans)
        speak(ans)
        if 'open youtube' in query:
            webbrowser.open("www.youtube.com")
        if 'open google' in query:
            webbrowser.open("www.google.com")
        if 'bye' in query:
            break


