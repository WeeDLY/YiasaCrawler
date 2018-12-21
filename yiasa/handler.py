import threading
from datetime import timedelta, datetime
import sys
sys.path.append('..')

import database.query as query
import util.logger as logger
import yiasa.spider as spider
from yiasa.spider import Spider

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

class Handler:
    def __init__(self, log, db, settings):
        self.log = log
        self.db = db
        self.settings = settings
        self.threadId = 0

    def start_threads(self):
        started = 0
        while len(self.settings.spiderThreadList) < self.settings.get_threads() and len(self.settings.queue) > 0:
            domain = self.settings.queue.pop()
            self.setup_row_crawled(domain)

            s = Spider(self.log, self.db, self.threadId, domain)
            t = threading.Thread(target=s.start_crawl, name=self.threadId)
            t.daemon = True
            self.settings.spiderThreadList.append(t)
            t.start()
            self.threadId += 1
            self.log.log(logger.LogLevel.INFO, 'Started new spider: %s' % s.to_string())
    
    def setup_row_crawled(self, domain):
        """ This should make sure that the domain in question already exists in table 'crawled' """
        domainExists = self.db.query_exists(query.QUERY_GET_DOMAIN_IN_CRAWLED(), (domain, ))
        if domainExists is False:
            self.log.log(logger.LogLevel.DEBUG, "Domain %s is not in 'crawled. Creating...'" % domain)
            insertTableCrawled = self.db.query_commit(query.QUERY_INSERT_TABLE_CRAWLED(), (domain, 0, 0, 0, datetime.now(), ))
            if insertTableCrawled:
                self.log.log(logger.LogLevel.DEBUG, "Inserted %s to 'crawled'" % domain)
            else:
                self.log.log(logger.LogLevel.ERROR, "Error insert into 'crawled': %s" % domain)