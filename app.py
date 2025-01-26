from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
import random 
from string import ascii_uppercase
import openai
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = "ough"
socketio = SocketIO(app)

openai.api_key = os.getenv('OPENAI_API_KEY')

rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for x in range(length):
            code += random.choice(ascii_uppercase) 
        
        if code not in rooms:
            break
    
    return code

@app.route("/")
def home():
    session.clear()
    return render_template("index.html")

@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    user_input = request.form.get("message")

    if not user_input: 
        return render_template("chatbot.html", chat_history=session.get('chat_history', []), error="Please enter a message.")

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

@app.route("/ambience")
def ambience():
    return render_template("ambience.html")

@app.route("/chatroom", methods=["POST", "GET"])
def trivia():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("chatroom.html", code=code, name=name)

        if join != False and not code:
            return render_template("chatroom.html", code=code, name=name)

        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("chatroom.html", code=code, name=name)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("chatroom.html")

@app.route("/room")
def room():
    room_code = session.get("room")
    if room_code not in rooms:
        return redirect(url_for("chatroom.html"))
    
    return render_template("room.html", room_code=room_code)

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    
    if not room or not name:
        return

    if room not in rooms:
        leave_room(room)
        return 

    join_room(room)
    
    send({"name": name, "message": "has entered the room"}, to=room)
    
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -=1
        if rooms[room]["members"] <=0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

@socketio.on("message")
def message(data):

    room = session.get("room")  
    
    if not room:  
        return
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    
    send(content, to=room)  
    rooms[room]["messages"].append(content)  
 
if __name__ == '__main__':
    app.run(debug=True)
