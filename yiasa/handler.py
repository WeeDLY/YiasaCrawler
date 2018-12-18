import threading
import sys
sys.path.append('..')

import util.logger as logger
import yiasa.spider as spider
from yiasa.spider import Spider

class Handler:
    queue = list()
    spiderThreadList = list()
    spiderList = list()
    threads = 3
    robots = True
    def __init__(self, log, db):
        self.log = log
        self.db = db
        self.threadId = 0
    
    def start_threads(self):
        started = 0
        while len(self.spiderThreadList) < self.threads and len(self.queue) > 0:
            s = Spider(self.log, self.db, self.threadId, self.queue.pop())
            t = threading.Thread(target=s.start_crawl, name=self.threadId)
            t.daemon = True
            self.spiderThreadList.append(t)
            t.start()
            self.log.log(logger.LogLevel.INFO, 'Started new spider: %s' % s.to_string())