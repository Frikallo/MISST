import flask
import os
import shutil
from waitress import serve
import datetime
import logging
import logging.config
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})
os.chdir(os.path.dirname(os.path.abspath(__file__)))

loggerName = 'MISST Server'
logger = logging.getLogger(loggerName)
logger.setLevel(logging.INFO)

logging.basicConfig(format=' %(name)s :: %(levelname)-8s :: %(message)s',
                    level=logging.INFO)

host = '127.0.0.1'
port = 5000

logger.info(f'Logger initialized ({str(datetime.datetime.now()).split(".")[0]})')
logger.info(f'Host: {host}')
logger.info(f'Port: {port}')

# Create the application.
APP = flask.Flask(__name__)

# Create a URL route in our application for "/"
@APP.route('/')
def home():
    return "demucs-server V0.1"

queue_list = 0

@APP.route('/queue', methods=['POST'])
def queue():
    global queue_list
    queue_list += 1
    print(queue_list)
    while True:
        if queue_list == 1:
            break
    return "OK"

@APP.route('/demucs-upload', methods=['POST'])
def upload(queue_list=queue_list):
    f = flask.request.files['file']
    f_extension = flask.request.files['file'].filename.split('.')[-1]
    if os.path.exists('./tmp'):
        pass
    else:
        os.mkdir('./tmp')
    f.save(f'./tmp/{f.filename}.{f_extension}')
    logger.info(f.filename)
    logger.info(f_extension)
    file_path = os.path.abspath(f'./tmp/{f.filename}.{f_extension}')
    cmd = os.system(f'python -m demucs -d cuda "{file_path}"')
    logger.info(f'done: {cmd}')
    if cmd == 0:
        pass
    else:
        return flask.jsonify({"error": "Something went wrong"})
    logger.info("File Processed")
    for i in os.listdir('./tmp'):
        os.remove(f'./tmp/{i}')
    os.rmdir('./tmp')
    logger.info("Temp Folder Removed")
    shutil.make_archive(f'./separated/mdx_extra_q/{f.filename}', 'zip', f'./separated/mdx_extra_q/{f.filename}')
    logger.info("Archive Created")
    for i in os.listdir(f'./separated/mdx_extra_q/{f.filename}'):
        os.remove(f'./separated/mdx_extra_q/{f.filename}/{i}')
    os.rmdir(f'./separated/mdx_extra_q/{f.filename}')
    logger.info("Temp Folder Removed")
    logger.info("Done")
    queue_list -= 1
    return "OK"

@APP.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    dir = os.path.abspath('./separated/mdx_extra_q/')
    return flask.send_from_directory(directory=dir, path=filename)

if __name__ == '__main__':
    serve(APP, host=host, port=port, threads=1)