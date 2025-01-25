from flask import Flask, render_template


import openai

app = Flask(__name__)

app.config["SECRET_KEY"] = "ough"

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
