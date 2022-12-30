from flask import Flask
import os
from helper import *

app = Flask(__name__)
app.config.from_object('config.Config')

@app.route('/')
def home():
    return getElectrictyUsageInfo("12/01/22","12/31/22")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=app.config['DEBUG'])