import threading
import time
from datetime import datetime
import sys
sys.path.append('..')

import database.query as query
import util.logger as logger
import yiasa.handler as handler
import server.server as server

def start(log, db, args):
    log.log(logger.LogLevel.INFO, 'Starting YiasaBot', forcePrint=True)
    settings = handler.HandlerSettings()
    settings.set_threads(args.threads)

    defaultFill = fill_database(log, db)
    if defaultFill is False:
        log.log(logger.LogLevel.ERROR, 'Was unable to fill database with default urls. Exiting..')
        sys.exit()

    spider_handler = handler.Handler(log, db, settings)
    #spider_handler.start_threads()
    
    handler_thread = threading.Thread(target=spider_handler.run)
    handler_thread.daemon = True
    if args.bot:
        handler_thread.start()

    if args.server:
        server.start_server()
    while True:
        time.sleep(5*2)

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
        insertedDefault = db.query_execute(query.QUERY_INSERT_TABLE_CRAWL_QUEUE(), (url, 0, 0, datetime.now()))
        if insertedDefault:
            log.log(logger.LogLevel.DEBUG, "Inserted default_url to \'crawl_queue\': %s" % url)
        else:
            log.log(logger.LogLevel.ERROR, "Failed to insert default_url to \'crawl_queue\': %s" % url)
            return False
    db.commit
    return True