import flask
import os
import shutil
from shlex import quote
from waitress import serve
from werkzeug.utils import secure_filename
import datetime
import linode_api4 as linode
from dotenv import load_dotenv

load_dotenv()
import logging
import logging.config

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": True,
    }
)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

token = os.getenv("LINODE_TOKEN")
client = linode.LinodeClient(token)
linodes = client.linode.instances()

loggerName = "MISST Server"
logger = logging.getLogger(loggerName)
logger.setLevel(logging.INFO)

logging.basicConfig(
    format=" %(name)s :: %(levelname)-8s :: %(message)s", level=logging.INFO
)

host = "127.0.0.1"
port = 5000

logger.info(f'Logger initialized ({str(datetime.datetime.now()).split(".")[0]})')

for current_linode in linodes:
    logger.info(
        f"Linode: {current_linode.label} {current_linode.id} {current_linode.ipv4}"
    )
    logger.info(f'Accrued Charges: ${client.account.alldata()["balance_uninvoiced"]}')

logger.info(f"Serving on {host}:{port}...")

# Create the application.
APP = flask.Flask(__name__)

# Create a URL route in our application for "/"
@APP.route("/")
def home():
    return "demucs-server V0.1"


queue_list = 0


@APP.route("/queue", methods=["POST"])
def queue():
    global queue_list
    queue_list += 1
    logger.info(f"Queue Depth: {queue_list}")
    while True:
        if queue_list == 1:
            queue_list -= 1
            break
    return "OK"


@APP.route("/check")
def check_alive():
    logger.info("Alive")
    return "OK"


@APP.route("/user/<path:userid>", methods=['GET', 'POST'])
def user(userid):
    ip = str(flask.request.data.decode("utf-8"))
    logger.info(f"User {userid} is online! ({str(datetime.datetime.now()).split('.')[0]}) ip: {ip}")
    return "OK"

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".zip"}

def allowed_file(filename):
    if os.path.splitext(filename)[1] in ALLOWED_EXTENSIONS:
        return secure_filename(filename)

@APP.route("/demucs-upload", methods=["POST"])
def upload():
    logger.info("==================== STARTING JOB ====================")
    file = flask.request.files["file"]
    filename = allowed_file(file.filename)
    if os.path.exists("./tmp"):
        pass
    else:
        os.mkdir("./tmp")
    file.save(f"./tmp/{filename}")
    file_path = os.path.abspath(f"./tmp/{filename}")
    cmd = os.system(f'python -m demucs -d cuda {quote(file_path)}')
    logger.info(f"Exited with status code {cmd}")
    if cmd == 0:
        logger.info(f"Preprocessed {filename} Successfully")
        pass
    else:
        logger.info(f"Preprocessing {filename} Failed")
        return flask.jsonify({"error": "Something went wrong"})
    logger.info("File Processed")
    for i in os.listdir("./tmp"):
        os.remove(f"./tmp/{i}")
    os.rmdir("./tmp")
    logger.info("Temp Folder Removed")
    filename = os.path.splitext(filename)[0]
    shutil.make_archive(
        f"./separated/mdx_extra_q/{filename}",
        "zip",
        f"./separated/mdx_extra_q/{filename}",
    )
    logger.info("Archive Created")
    for i in os.listdir(f"./separated/mdx_extra_q/{filename}"):
        os.remove(f"./separated/mdx_extra_q/{filename}/{i}")
    os.rmdir(f"./separated/mdx_extra_q/{filename}")
    logger.info("Temp Folder Removed")
    logger.info("Done")
    logger.info("==================== FINISHED JOB ====================")
    return "OK"


@APP.route("/download/<path:filename>", methods=["GET", "POST"])
def download(filename):
    dir = os.path.abspath("./separated/mdx_extra_q/")
    return flask.send_from_directory(directory=dir, path=allowed_file(filename))


if __name__ == "__main__":
    serve(APP, host=host, port=port, threads=1)
