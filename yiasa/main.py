import time
import sys
sys.path.append('..')

import util.logger as logger
import yiasa.handler as handler

def start(log, db, args):
    log.log(logger.LogLevel.INFO, 'Starting YiasaBot', forcePrint=True)
    settings = handler.HandlerSettings()
    settings.set_threads(args.threads)

    settings.queue.append('http://lichess.org')
    settings.queue.append('https://www.reddit.com')
    settings.queue.append('http://pokemmo.eu')

    spider_handler = handler.Handler(log, db, settings)
    spider_handler.start_threads()

    while True:
        time.sleep(5*2)
        print('main_thread')

def fill_database():
    """ Function that fills database with 'starting' urls """
