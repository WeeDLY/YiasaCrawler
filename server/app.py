from flask import Flask, Markup, render_template, request

app = Flask(__name__)

def start_server():
    app.run(host='0.0.0.0', port=5300)

@app.route('/')
def root():
    return "<title>Yiasa Crawler</title>Yiasa Crawler"