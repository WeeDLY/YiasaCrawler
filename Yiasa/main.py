import sys
sys.path.append('..')
import util.logger as logger

def start(log, db):
    log.log(logger.LogLevel.INFO, 'Starting YiasaBot', forcePrint=True)
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