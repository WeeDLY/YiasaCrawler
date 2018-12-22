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
    run = True
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
        self.lock = threading.Lock()

    def run(self):
        self.start_threads()
        while self.run:
            time.sleep(5)
            print('handler_thread')
            
            # Gets status of all active threads
            threadStatus = self.get_thread_status()
            print('Alive: %s' % threadStatus["alive"])
            print('Dead: %s' % threadStatus["dead"])
            
            # Restart dead threads with new assignment
            for index in threadStatus["dead"]:
                self.restart_spider(index)

    def get_thread_status(self):
        """ returns associate list with dead/alive threads, based on index """
        threadStatus = {"dead":[], "alive":[]}
        for index in range(len(self.settings.spiderThreadList)):
            alive = self.settings.spiderThreadList[index].isAlive()
            if alive:
                threadStatus["alive"].append(index)
            else:
                threadStatus["dead"].append(index)
        return threadStatus

    def start_threads(self):
        """ Start all threads """
        started = 0
        while len(self.settings.spiderThreadList) < self.settings.get_threads() and len(self.settings.queue) > 0:
            self.start_spider()

    def restart_spider(self, index):
        """ remakes a spider thread """
        oldSpider = self.settings.spiderList[index]
        oldThread = self.settings.spiderThreadList[index]
        oldThread.join()
        self.log.log(logger.LogLevel.INFO, 'Restarting thread: %d -> %d' % (oldSpider.name, self.threadId))
        
        # Remove old spider+thread from list
        del self.settings.spiderList[index]
        del self.settings.spiderThreadList[index]

        # Start new spider
        self.start_spider()

    def start_spider(self):
        """ Starts a spider thread """
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