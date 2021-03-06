from threading import Lock
import sqlite3
import sys
sys.path.append('..')
import database.query as query
import util.logger as logger

class Database():
    def __init__(self, log, database_file):
        self.database_file = database_file
        self.connection = sqlite3.connect(self.database_file, check_same_thread=False)
        self.log = log
        self.execute_lock = Lock()
        self.commit_lock = Lock()
    
    def check_database(self):
        """ Checks and/or creates the database tables for Yiasa to run """
        self.log.log(logger.LogLevel.INFO, 'Checking database tables')
        table_crawled = self.check_table('crawled', query.QUERY_CREATE_TABLE_CRAWLED())
        if table_crawled is False:
            return False

        table_crawl_history = self.check_table('crawl_history', query.QUERY_CREATE_TABLE_CRAWL_HISTORY())
        if table_crawl_history is False:
            return False

        table_crawl_information = self.check_table('crawl_information', query.QUERY_CREATE_TABLE_CRAWL_INFORMATION())
        if table_crawl_information is False:
            return False

        table_crawl_queue = self.check_table('crawl_queue', query.QUERY_CREATE_TABLE_CRAWL_QUEUE())
        if table_crawl_queue is False:
            return False

    def database_dump(self):
        """ Dumps all tables in database """
        print('=====Dumping database=====')
        print('=====CRAWLED=====')
        self.table_dump(query.QUERY_GET_TABLE_CRAWLED())
        print('=====CRAWL_INFORMATION=====')
        self.table_dump(query.QUERY_GET_TABLE_CRAWL_INFORMATION())
        print('=====CRAWL_QUEUE=====')
        self.table_dump(query.QUERY_GET_TABLE_CRAWL_QUEUE())
        print('=====CRAWL_HISTORY=====')
        self.table_dump(query.QUERY_GET_TABLE_CRAWL_HISTORY())

    def table_dump(self, query):
        try:
            c = self.connection.cursor()
            rows = c.execute(query)
            description = "("
            for desc in c.description:
                description += '%s, ' % desc[0]
            print('%s)' % description[:len(description) - 2])
            for row in rows:
                print(row)
        except Exception as e:
            self.log.log(logger.LogLevel.ERROR, "Exception when dumping database: %s" % e)


    def check_table(self, table, createTableQuery, maxAttempts=3):
        """ Checks and/or creates an individual table """
        tableSetUp = False
        i = 0
        while tableSetUp is False or i > maxAttempts:
            self.log.log(logger.LogLevel.INFO, 'Checking table(%d): %s' % (i, table))
            tableExists = self.query_exists(query.QUERY_TABLE_EXISTS(), (table, ))
            if tableExists is False:
                self.log.log(logger.LogLevel.INFO, 'Creating table(%d): %s' % (i, table))
                self.query_execute(createTableQuery)
            else:
                return True
            i += 1
        if tableSetUp is False:
            self.log.log(logger.LogLevel.CRITICAL, 'Could not create table: %s' % table)
        return tableSetUp

    def query_get(self, q, param=None):
        """ Query that fetches results """
        try:
            c = self.connection.cursor()
            c.execute(q, param)
            self.log.log(logger.LogLevel.DEBUG, 'database.query_get: %s | %s' % (q, param))            
            return c.fetchall()
        except Exception as e:
            self.log.log(logger.LogLevel.ERROR, 'database.query_get: %s. %s | %s' % (e, q, param))
            return None

    def query_exists(self, q, param=None):
        """ checks if the query yields a result """
        """ Queries database and return one row """
        try:
            c = self.connection.cursor()
            c.execute(q, param)
            self.log.log(logger.LogLevel.DEBUG, 'database.query_exists: %s | %s' % (q, param))            
            if c.fetchone() is None:
                return False
            else:
                return True
        except Exception as e:
            self.log.log(logger.LogLevel.ERROR, 'database.query_exists: %s. %s | %s' % (e, q, param))
            return False

    def query_execute(self, q, param=None, commit=True):
        """ Executes a query, returns True if executed, otherwise False """
        try:
            with self.execute_lock:
                c = self.connection.cursor()
                if param is None:
                    c.execute(q)
                else:
                    c.execute(q, param)
                self.log.log(logger.LogLevel.DEBUG, 'database.query_execute: %s | %s' % (q, param))
                if commit:
                    self.commit()
                return True
        except Exception as e:
            self.log.log(logger.LogLevel.ERROR, 'database.query_execute: %s | %s | %s' % (e, q, param))
            return False
    
    def commit(self):
        """ Commit changes to db """
        try:
            with self.commit_lock:
                self.connection.commit()
                self.log.log(logger.LogLevel.DEBUG, 'Database was commited')
        except Exception as e:
            self.log.log(logger.LogLevel.CRITICAL, 'Failed to commit database: %s' % e)