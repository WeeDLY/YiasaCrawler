import time
import sys
sys.path.append('..')

import util.logger as logger
import yiasa.handler as handler

class HandlerSettings():
    queue = list()
    spiderThreadList = list()
    spiderList = list()
    robots = True

    def __init__(self):
        self._threads = 3

    def get_threads(self):
        return self._threads
        
    def set_threads(self, value):
        self._threads = value
    
    def del_threads(self):
        del self._threads
    threads = property(get_threads, set_threads, del_threads, 3)

def start(log, db):
    log.log(logger.LogLevel.INFO, 'Starting YiasaBot', forcePrint=True)
    settings = HandlerSettings()

    settings.queue.append('http://lichess.org')
    settings.queue.append('https://www.reddit.com/')
    settings.queue.append('http://pokemmo.eu')

    spider_handler = handler.Handler(log, db, settings)
    spider_handler.start_threads()

    while True:
        time.sleep(5*2)
        print('main_thread')