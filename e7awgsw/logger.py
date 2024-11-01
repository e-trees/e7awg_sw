import logging
import datetime
import os
import sys
from logging import getLogger, FileHandler, NullHandler, StreamHandler, Formatter, Logger

os.makedirs('./log', exist_ok = True)
formatter = Formatter(
    '%(asctime)s - [%(name)s] - %(levelname)s - %(filename)s - ln.%(lineno)d - %(funcName)s\n%(message)s\n')
file_name = datetime.datetime.now().strftime('err_log_%Y%m%d%H%M%S.txt')
fh = FileHandler('./log/' + file_name, delay = True)
fh.setFormatter(formatter)
invoked_script = os.path.splitext(os.path.basename(sys.argv[0]))[0]
file_logger = getLogger(invoked_script)
file_logger.setLevel(logging.INFO)
file_logger.addHandler(fh)

null_logger = getLogger('nullLibLog')
null_logger.addHandler(NullHandler())


sh = StreamHandler(sys.stderr)
sh.setFormatter(formatter)
stderr_logger = getLogger('stderrLog')
stderr_logger.addHandler(sh)


def get_file_logger() -> Logger:
    return file_logger


def get_null_logger() -> Logger:
    return null_logger


def get_stderr_logger() -> Logger:
    return stderr_logger


def log_error(msg: object, *loggers: Logger) -> None:
    for logger in loggers:
        if isinstance(msg, Exception):
            msg = '{}: {}'.format(type(msg).__name__, msg)
        logger.error(msg, stacklevel = 2)


def log_warning(msg, *loggers: Logger) -> None:
    for logger in loggers:
        if isinstance(msg, Exception):
            msg = '{}: {}'.format(type(msg).__name__, msg)
        logger.warning(msg, stacklevel = 2)
