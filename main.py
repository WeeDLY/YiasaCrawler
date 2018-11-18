import logger
from spider import Spider

def main():
    log = logger.Logger('yiasa_log', 'logs')

    Spider.queue.add('http://e24.no/')
    #Spider.queue.add('https://www.buzzfeed.com/')
    Spider.print_queue()    
    a = Spider(log, 1, Spider.queue.pop())
    a.parse_robots()
    a.to_string()
    #a.start_crawl()

if __name__ == '__main__':
    main()