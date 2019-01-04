import time
import threading
from datetime import timedelta, datetime
import sys
sys.path.append('..')

import database.query as query
import util.logger as logger
import bot.spider as spider
from bot.spider import Spider

class HandlerSettings():
    startTime = datetime.now()
    queue = list()
    spiderThreadList = list()
    spiderList = list()
    robots = True
    run = True
    max_urls = 100
    refresh = 0.4

    def __init__(self):
        self._threads = 0

    def get_threads(self):
        return self._threads
        
    def set_threads(self, value):
        if Handler.new_thread_amount == value:
            Handler.new_thread_amount = None
        self._threads = value
    
    def del_threads(self):
        del self._threads
    threads = property(get_threads, set_threads, del_threads, 0)

class Handler:
    new_thread_amount = None
    def __init__(self, log, db, settings):
        self.log = log
        self.db = db
        self.settings = settings
        self.threadId = 0

    def run(self):
        self.fill_queue()
        self.start_threads()
        while self.run:
            print('handler_thread')
            if Handler.new_thread_amount is not None:
                self.settings.set_threads(Handler.new_thread_amount)
            
            print('Threads: %d' % self.settings.get_threads())

            # Gets status of all active threads
            threadStatus = self.get_thread_status()
            aliveThreads = len(threadStatus["alive"])
            deadThreads = len(threadStatus["dead"])
            totalThreads = aliveThreads + deadThreads
            print('Threads running: %d' % totalThreads)
            print('Alive: %s' % threadStatus["alive"])
            print('Dead: %s' % threadStatus["dead"])
            
            if totalThreads < self.settings.get_threads():
                self.start_threads()

            # Restart dead threads with new assignment
            for index in threadStatus["dead"]:
                self.restart_spider(index)
            
            self.fill_queue()

            time.sleep(5)

    def get_thread_status(self):
        """ returns associate list with dead/alive threads, based on index """
        threadStatus = {"dead":[], "alive":[]}
        for index in range(len(HandlerSettings.spiderThreadList)):
            alive = HandlerSettings.spiderThreadList[index].isAlive()
            if alive:
                threadStatus["alive"].append(index)
            else:
                threadStatus["dead"].append(index)
        return threadStatus

    def start_threads(self):
        """ Start all threads """
        while len(HandlerSettings.spiderThreadList) < self.settings.get_threads() and len(HandlerSettings.queue) > 0:
            self.start_spider()

    def restart_spider(self, index):
        """ remakes a spider thread """
        if index > len(HandlerSettings.spiderList) - 1:
            self.log.log(logger.LogLevel.ERROR, "Can't restart spider: index/len(spiderList): %d/%d" % (index, len(HandlerSettings.spiderList)))
            return

        oldSpider = HandlerSettings.spiderList[index]
        oldThread = HandlerSettings.spiderThreadList[index]
        oldThread.join()
        self.log.log(logger.LogLevel.INFO, 'Restarting thread: %d -> %d' % (oldSpider.name, self.threadId))
        
        # Remove old spider+thread from list
        del HandlerSettings.spiderList[index]
        del HandlerSettings.spiderThreadList[index]

        if len(HandlerSettings.spiderList) < self.settings.get_threads():
            self.start_spider()
        else:
            self.log.log(logger.LogLevel.INFO, 'Not restarting spider, due to thread limit')

    def start_spider(self):
        """ Starts a spider thread """
        domain = HandlerSettings.queue.pop()
        self.setup_row_crawled(domain)

        # Create spider object
        s = Spider(self.log, self.db, self.threadId, domain, HandlerSettings.max_urls)
        HandlerSettings.spiderList.append(s)

        # Create thread for spider object
        t = threading.Thread(target=s.start_crawl, name=self.threadId)
        t.daemon = True
        HandlerSettings.spiderThreadList.append(t)

        t.start()
        self.threadId += 1
        self.log.log(logger.LogLevel.INFO, 'Started new spider: %s' % s.to_string())

    def get_spider_thread_status(self, threadId):
        """ Gets information about a spider thread, based on threadId """
        name = HandlerSettings.spiderList[threadId].name
        start_time = HandlerSettings.spiderList[threadId].start_time
        crawled_urls = HandlerSettings.spiderList[threadId].crawled_urls
        queue = HandlerSettings.spiderList[threadId].queue
        new_domains = HandlerSettings.spiderList[threadId].new_domains
        crawl_delay = HandlerSettings.spiderList[threadId].crawl_delay
        print(name)
        print(start_time)
        print(crawled_urls)
        print(queue)
        print(new_domains)
        print(crawl_delay)
    
    def fill_queue(self):
        """ Fills queue with needed urls """
        amount = (self.settings.get_threads() * 2) - len(HandlerSettings.spiderList)

        urls = self.db.query_get(query.QUERY_GET_CRAWL_QUEUE(), (amount, ))
        tempQueue = list()
        for url in urls:
            tempQueue.append(url[0])
            
            # Marks url taken in DB. TODO: improve on this, by marking them all at the same time afterwards.
            urlStarted = self.db.query_execute(query.QUERY_INSERT_CRAWL_QUEUE_STARTED(), (url[0], ))
            if urlStarted is False:
                self.log.log(logger.LogLevel.ERROR, 'Unable to mark url: %s as started in DB - crawl_queue' % url[0])
        tempQueue.reverse()
        HandlerSettings.queue += tempQueue
        self.log.log(logger.LogLevel.DEBUG, 'Added %d urls to queue' % amount)

    def setup_row_crawled(self, domain):
        """ This should make sure that the domain in question already exists in table 'crawled' """
        domainExists = self.db.query_exists(query.QUERY_GET_DOMAIN_IN_CRAWLED(), (domain, ))
        if domainExists is False:
            self.log.log(logger.LogLevel.DEBUG, "Domain %s is not in 'crawled. Creating...'" % domain)
            insertTableCrawled = self.db.query_execute(query.QUERY_INSERT_TABLE_CRAWLED(), (domain, 0, 0, 0, datetime.now(), ))
            if insertTableCrawled:
                self.log.log(logger.LogLevel.DEBUG, "Inserted %s to 'crawled'" % domain)
            else:
                self.log.log(logger.LogLevel.ERROR, "Error insert into 'crawled': %s" % domain)