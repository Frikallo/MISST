import os
import logging
from os.path import dirname, abspath

#innitialize logging
fh = logging.FileHandler('log.txt')
fh.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(fh)

logger.info('Starting the installation')
logger.info("Checking for Python 3.9")

try:
    os.system("python3 --version")
except:
    logger.info("Python 3.9 not found. Please install Python 3.9 and try again.")
    exit()
logger.info("Python 3.9 found. Continuing")

logger.info("Checking for pip")
try:
    os.system("pip --version")
except:
    logger.info("pip not found. Please install pip and try again.")
    exit()
logger.info("pip found. Continuing")

logger.info("Checking for git")
try:
    os.system("git --version")
except:
    logger.info("git not found. Please install git and try again.")
    exit()
logger.info("git found. Continuing")

logger.info("Installing dependencies")
userpath = os.path.expanduser('~')
logger.info(f"Install directory {userpath}\SUCK-MY-NUTS-KANYE")
install_path = os.path.abspath(f"{userpath}\SUCK-MY-NUTS-KANYE")
if os.path.exists(install_path):
    logger.info("Install directory already exists. Deleting and recreating")
    os.system(f"rd /s /q {install_path}")
os.system(f"mkdir {install_path}")
os.chdir(install_path)
logger.info("Installing repo & dependencies")
os.system("git clone https://github.com/Frikallo/SUCK-MY-NUTS-KANYE.git")
os.chdir(f"{install_path}\SUCK-MY-NUTS-KANYE")
os.system("pip install -r requirements.txt")
logger.info("Dependencies installed")
logger.info(f"Shortcut can be found in {userpath}/Desktop/SUCK-MY-NUTS-KANYE.exe")
os.chdir(f"{userpath}/Desktop")
os.systemm("curl -OL https://raw.githubusercontent.com/Frikallo/SUCK-MY-NUTS-KANYE/master/install-resources/SUCK-MY-NUTS-KANYE.exe")
logger.info(f"Log file can be found in {dirname(dirname(abspath(__file__)))}\log.txt")
logger.info("Installation complete")