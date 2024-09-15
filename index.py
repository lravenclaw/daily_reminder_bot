import os

from flask import Flask
from main import main

import threading

app = Flask(__name__)

@app.route('/')
def index_route():
    return "Bot works!"

if __name__ == '__main__':
    bot_thread = threading.Thread(target=main)
    bot_thread.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)