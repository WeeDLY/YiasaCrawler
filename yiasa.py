import time
import threading
import argparse

import database.database as database
import util.logger as logger
import debug.debug as debug
import bot.main as main
import bot.handler as handler

def startup(args):
    log = logger.Logger('yiasa_log', 'logs')
    log.log(logger.LogLevel.INFO, 'Yiasabot is starting. DebugMode: %s' % args.debug, force_print=True)

    db = check_database(log)
    if db is None:
        return

    if args.debug:
        debug.debug(log, db)
    else:
        main.start(log, db, args)

def check_database(log):
    """ Checks that database is up and running correctly """
    db = database.Database(log, 'crawl.db')
    status = db.check_database()
    if status is False:
        log.log(logger.LogLevel.CRITICAL, 'Database is not set up correctly')
        return None
    
    log.log(logger.LogLevel.INFO, 'Database is correctly set up')
    return db


def parse_arguments():
    """ Parse args from user """
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', action='store_true', default=False)
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    parser.add_argument('-t', '--threads', type=int, default=0)
    parser.add_argument('-u', '--urls', type=int, default=100)
    parser.add_argument('-r', '--refresh', type=float, default=2.0)
    args = parser.parse_args()
    startup(args)

if __name__ == '__main__':
    parse_arguments()