import threading
import sys
sys.path.append('..')

import database.query as query
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
            domain = self.queue.pop()
            self.setup_db_row(domain)

            s = Spider(self.log, self.db, self.threadId, domain)
            t = threading.Thread(target=s.start_crawl, name=self.threadId)
            t.daemon = True
            self.spiderThreadList.append(t)
            t.start()
            self.threadId += 1
            self.log.log(logger.LogLevel.INFO, 'Started new spider: %s' % s.to_string())
    
    def setup_db_row(self, domain):
        domainExists = self.db.query_exists(query.QUERY_GET_CRAWLED_DOMAIN(), (domain, ))
        if domainExists is False:
            self.db.query_commit(query.QUERY_INSERT_TABLE_CRAWLED(), (domain, 0, 0, 'NULL'))
