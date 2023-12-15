from flask import Flask, Response

app = Flask(__name__)

@app.route("/voice")
def voice_response():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Thanks for trying our documentation. Enjoy!</Say>
    <Play>http://demo.twilio.com/docs/classic.mp3</Play>
</Response>"""
    return Response(xml, mimetype='text/xml')

voice_response()

if __name__ == "__main__":
    app.run(debug=True)