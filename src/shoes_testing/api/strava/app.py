from flask import Flask, current_app
app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello Maxou!"


if __name__ == "__main__":
    app.run(debug=True)
    print(current_app)
