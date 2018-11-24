import logger
from spider import Spider
import time
import threading

def main():
    log = logger.Logger('yiasa_log', 'logs')

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


if __name__ == '__main__':
    main()