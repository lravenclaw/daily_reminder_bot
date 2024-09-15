from flask import Flask
import main

app = Flask(__name__)

@app.route('/')
def index_route():
    return "Bot works\!"

if __name__ == '__main__':
    main.main()