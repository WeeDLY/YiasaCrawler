import time
import threading
import argparse

import database.database as database
from spider import Spider
import util.logger as logger
import debug.debug as debug

def startup(debugMode):
    log = logger.Logger('yiasa_log', 'logs')
    log.log(logger.LogLevel.INFO, 'Yiasabot is starting. DebugMode: %s' % debugMode, forcePrint=True)

    db_status = check_database(log)
    if db_status is None:
        return

    debug.debug(log)

    """
    threads = 1
    crawlerThreads = []
    #Spider.queue.add('http://e24.no/')
    Spider.queue.add('http://sa.no')
    #Spider.queue.add('http://dagbladet.no/')
    #a.parse_robots()
    #Spider.print_queue()

    for i in range(threads):
        spider = Spider(log, i, Spider.queue.pop())
        spiderThread = threading.Thread(target=spider.start_crawl)
        spiderThread.daemon = True
        crawlerThreads.append(spiderThread)
        spiderThread.start()
    
    while True:
        time.sleep(5)
    """


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