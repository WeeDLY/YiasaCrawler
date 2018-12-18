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
        elif cmd == 'dump':
            db.database_dump()

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