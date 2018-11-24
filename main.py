from spider import Spider
import time
import threading
import logger
import database.database as database

def main():
    log = logger.Logger('yiasa_log', 'logs')

    db_status = check_database(log)
    if db_status is None:
        return

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


def check_database(log):
    """ Checks that database is up and running correctly """
    db = database.Database(log, 'yiasa.db')
    status = db.check_database()
    if status is False:
        log.log(logger.LogLevel.CRITICAL, 'Database is not set up correctly')
        return None
    
    log.log(logger.LogLevel.INFO, 'Database is correctly set up')
    return db

if __name__ == '__main__':
    main()