import time
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
        self._killList = list()

    def get_threads(self):
        return self._threads
        
    def set_threads(self, value):
        self._threads = value
    
    def del_threads(self):
        del self._threads
    
    def get_killList(self):
        return self._killList
        
    def set_killList(self, value):
        print(self._killList)
        self._killList.append(value)
    
    def del_killList(self):
        del self._killList
    
    killList = property(get_killList, set_killList, del_killList, 3)
    threads = property(get_threads, set_threads, del_threads, 3)

class Handler:
    def __init__(self, log, db, settings):
        self.log = log
        self.db = db
        self.settings = settings
        self.threadId = 0
        self.lock = threading.Lock()

    def run(self):
        self.start_threads()
        while True:
            time.sleep(5)
            print('handler_thread')
            print(len(self.settings.spiderThreadList))
            for thread in self.settings.spiderThreadList:
                alive = thread.isAlive()
                if alive is False:
                    threadId = int(thread.name.replace('Thread-', ''))
                    print('Thread: %d is finished' % threadId)
                    self.get_spider_thread_status(threadId)

    def start_threads(self):
        started = 0
        while len(self.settings.spiderThreadList) < self.settings.get_threads() and len(self.settings.queue) > 0:
            domain = self.settings.queue.pop()
            with self.lock:
                self.setup_row_crawled(domain)

            # Create spider object
            s = Spider(self.log, self.db, self.threadId, domain)
            self.settings.spiderList.append(s)

            # Create thread for spider object
            t = threading.Thread(target=s.start_crawl, name=self.threadId)
            t.daemon = True
            self.settings.spiderThreadList.append(t)

            t.start()
            self.threadId += 1
            self.log.log(logger.LogLevel.INFO, 'Started new spider: %s' % s.to_string())
        #self.get_spider_thread_status(0)

    def get_spider_thread_status(self, threadId):
        """ Gets information about a spider thread, based on threadId """
        name = self.settings.spiderList[threadId].name
        start_time = self.settings.spiderList[threadId].start_time
        crawled_urls = self.settings.spiderList[threadId].crawled_urls
        queue = self.settings.spiderList[threadId].queue
        new_domains = self.settings.spiderList[threadId].new_domains
        crawl_delay = self.settings.spiderList[threadId].crawl_delay
        print(name)
        print(start_time)
        print(crawled_urls)
        print(queue)
        print(new_domains)
        print(crawl_delay)
    
    def kill_thread(self, threadId):
        """ kills a thread, this is called from spider.py """
        thread = spiderThreadList[threadId]
        thread.join()
        print(thread.is_alive())

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