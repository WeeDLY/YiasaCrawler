import sys
sys.path.append('..')

import util.logger as logger
import database.database as database
import database.query as query

def database(log, db):
    databaseMode = True
    while databaseMode:
        cmd = input('database-debug$ ')
        if cmd == 'q' or cmd == 'e':
            debug(log, db)
        elif cmd == 'commit':
            q = input('database-debug: commit$ ')
            db.query_commit(q)
        elif cmd == 'dump':
            q = input('database-debug: dump$ ')
            db.table_dump(q)
        elif cmd == 'dump database' or cmd == 'dump db':
            db.database_dump()
        elif cmd == 'dump crawled':
            print('=====CRAWLED=====')
            db.table_dump(query.QUERY_GET_TABLE_CRAWLED())
        elif cmd == 'dump crawl history':
            print('=====CRAWL_HISTORY=====')
            db.table_dump(query.QUERY_GET_TABLE_CRAWL_HISTORY())
        elif cmd == 'dump crawl info':
            print('=====CRAWL_INFORMATION=====')
            db.table_dump(query.QUERY_GET_TABLE_CRAWL_INFORMATION())
        elif cmd == 'dump crawl queue':
            print('=====CRAWL_QUEUE=====')
            db.table_dump(query.QUERY_GET_TABLE_CRAWL_QUEUE())


def debug(log, db):
    print('Debug Mode. q or e to quit!')
    debugMode = True
    while debugMode:
        cmd = input('debug$ ')
        if cmd == 'q' or cmd == 'e':
            debugMode = False
        elif cmd == 'db':
                database(log, db)

    print('Exiting debug mode')
    sys.exit()