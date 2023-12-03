from flask import Flask, request, render_template
import processor

app = Flask(__name__)


@app.route("/")
def main():
    return "running"


@app.route("/cmd/main/receive/command", methods=["POST", "GET"])
def command_receiver():
    if request.method == "GET":
        return "No access"
    else:
        processed_response = processor.process("data")


if __name__ == "__main__":
    app.run(debug=True)
