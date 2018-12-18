import time
import threading
import argparse

import database.database as database
import util.logger as logger
import debug.debug as debug
import yiasa.main as main
import yiasa.handler as handler

def startup(args):
    log = logger.Logger('yiasa_log', 'logs')
    log.log(logger.LogLevel.INFO, 'Yiasabot is starting. DebugMode: %s' % args.debug, forcePrint=True)

    db = check_database(log)
    if db is None:
        return

    if args.debug:
        debug.debug(log, db)
    else:
        #handler.Handler.threads = args.threads
        main.start(log, db)


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
    parser.add_argument('-t', '--threads', type=int)
    args = parser.parse_args()
    startup(args)

if __name__ == '__main__':
    parse_arguments()