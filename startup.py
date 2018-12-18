import time
import threading
import argparse

import database.database as database
from Yiasa.spider import Spider
import util.logger as logger
import debug.debug as debug
import Yiasa.main as main

def startup(debugMode):
    log = logger.Logger('yiasa_log', 'logs')
    log.log(logger.LogLevel.INFO, 'Yiasabot is starting. DebugMode: %s' % debugMode, forcePrint=True)

    db_status = check_database(log)
    if db_status is None:
        return

    if debugMode:
        debug.debug(log)
    else:
        main.start(log)


def check_database(log):
    """ Checks that database is up and running correctly """
    db = database.Database(log, 'yiasa.db')
    status = db.check_database()
    if status is False:
        log.log(logger.LogLevel.CRITICAL, 'Database is not set up correctly')
        return None
    
    log.log(logger.LogLevel.INFO, 'Database is correctly set up')
    return db


def parse_arguments():
    """ Parse args from user """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    args = parser.parse_args()
    startup(args.debug)

if __name__ == '__main__':
    parse_arguments()