import time
import sys
sys.path.append('..')

import util.logger as logger
import yiasa.handler as handler

def start(log, db):
    log.log(logger.LogLevel.INFO, 'Starting YiasaBot', forcePrint=True)
    handler.Handler.queue.append('http://lichess.org')
    handler.Handler.queue.append('https://www.reddit.com/')
    handler.Handler.queue.append('http://pokemmo.eu')

    spider_handler = handler.Handler(log, db)
    spider_handler.start_threads()

    while True:
        time.sleep(5*2)
        print('main_thread')