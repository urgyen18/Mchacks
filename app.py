from flask import Flask, render_template, request, session

import openai
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = "ough"

openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chatbot", methods=["POST"])
def chatbot():
    user_input = request.form.get("message")

    if 'chat_history' not in session:
        session['chat_history'] = []

    session['chat_history'].append({"role": "user", "content": user_input})

    response = openai.ChatCompletion.create(  
        model="gpt-3.5-turbo",  
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input},
        ],
        temperature=0.5,
        max_tokens=60,
        top_p=1,
        frequency_penalty=0,
        stop=["\nUser: ", "\nChatbot: "]
    )

    bot_response = response.choices[0].message['content'].strip()

    session['chat_history'].append({"role": "assistant", "content": bot_response})

    return render_template("chatbot.html", user_input=user_input, bot_response=bot_response, chat_history=session['chat_history'])


if __name__ == '__main__':
    app.run(debug=True)
