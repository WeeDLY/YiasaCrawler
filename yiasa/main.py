import time
from datetime import datetime
import sys
sys.path.append('..')

import database.query as query
import util.logger as logger
import yiasa.handler as handler

def start(log, db, args):
    log.log(logger.LogLevel.INFO, 'Starting YiasaBot', forcePrint=True)
    settings = handler.HandlerSettings()
    settings.set_threads(args.threads)

    defaultFill = fill_database(log, db)
    if defaultFill is False:
        log.log(logger.LogLevel.ERROR, 'Was unable to fill database with default urls. Exiting..')
        sys.exit()

    queue_urls = db.query_get(query.QUERY_GET_CRAWL_QUEUE(), (args.threads * 2, ))
    queue = list()
    for url in queue_urls:
        queue.append(url[0])
    queue.reverse()
    settings.queue.append(queue)

    spider_handler = handler.Handler(log, db, settings)
    spider_handler.start_threads()

    while True:
        time.sleep(5*2)
        print('main_thread')

def fill_database(log, db):
    """ Function that fills database with 'starting' urls """
    default_urls = [
        'https://www.google.com',
        'https://www.youtube.com',
        'https://www.facebook.com',
        'http://lichess.org',
        'https://www.wikipedia.org',
        'https://imgur.com',
        'https://www.yahoo.com',
        'https://www.amazon.com',
        'https://twitter.com',
        'https://www.instagram.com',
        'https://outlook.live.com',
        'https://www.bing.com',
        'https://www.ebay.com',
        'https://www.spotify.com',
        'https://www.microsoft.com',
        'https://www.msn.com',
        'https://weather.com',
        'https://www.twitch.tv',
        'http://www.bbc.com',
        'https://www.reddit.com'
    ]
    for url in default_urls:
        insertedDefault = db.query_commit(query.QUERY_INSERT_TABLE_CRAWL_QUEUE(), (url, 0, datetime.now()))
        if insertedDefault:
            log.log(logger.LogLevel.DEBUG, "Inserted default_url to \'crawl_queue\': %s" % url)
        else:
            log.log(logger.LogLevel.ERROR, "Failed to insert default_url to \'crawl_queue\': %s" % url)
            return False
    return True