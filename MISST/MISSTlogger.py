import datetime
import logging
import sys


class MISSTlogger:
    def __init__(self):
        loggerName = "MISST"
        logFormatter = logging.Formatter(fmt=" %(name)s :: %(levelname)-8s :: %(message)s")
        self.logger = logging.getLogger(loggerName)

        logging.basicConfig(
            filename="MISST.log",
            filemode="a",
            format=" %(name)s :: %(levelname)-8s :: %(message)s",
            level=logging.INFO,
        )

        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)

        self.logger.addHandler(consoleHandler)
        self.logger.info(f'Logger initialized ({str(datetime.datetime.now()).split(".")[0]})')

        sys.excepthook = self.handler
    
    def handler(self, type, value, tb):
        self.logger.exception("Uncaught exception: {0}".format(str(value)))