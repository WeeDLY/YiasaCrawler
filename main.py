import logger
from spider import Spider

def main():
    log = logger.Logger('yiasa_log', 'logs')

    Spider.queue.add('http://bash.org')
    Spider.print_queue()    
    a = Spider(log, 1, Spider.queue.pop())
    a.to_string()
    a.crawl()

if __name__ == '__main__':
    main()