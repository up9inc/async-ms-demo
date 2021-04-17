import logging
import os

from flask import Flask, send_file

app = Flask(__name__)


@app.route('/', methods=('get',))
def root():
    return send_file("spa.html")


@app.route('/', methods=('post',))
def post():
    return send_file("spa.html")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG if os.getenv('DEBUG') else logging.INFO,
                        format='[%(asctime)s %(name)s %(levelname)s] %(message)s')
    app.run(host='0.0.0.0')
