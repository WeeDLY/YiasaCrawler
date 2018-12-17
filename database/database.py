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

    def check_table(self, table, createTableQuery, maxAttempts=3):
        """ Checks and/or creates an individual table """
        tableSetUp = False
        i = 0
        while tableSetUp is False or i > maxAttempts:
            self.log.log(logger.LogLevel.INFO, 'Checking table(%d): %s' % (i, table))
            tableExists = self.query_exists(query.QUERY_TABLE_EXISTS(), (table, ))
            if tableExists is False:
                self.log.log(logger.LogLevel.INFO, 'Creating table(%d): %s' % (i, table))
                self.query_commit(createTableQuery)
            else:
                return True
            i += 1
        if tableSetUp is False:
            self.log.log(logger.LogLevel.CRITICAL, 'Could not create table: %s' % table)
        return tableSetUp    

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

    def query_commit(self, q, param=None):
        """ Executes a query, returns True if executed, otherwise False """
        try:
            c = self.connection.cursor()
            if param is None:
                c.execute(q)
            else:
                c.execute(q, param)
            self.log.log(logger.LogLevel.DEBUG, 'database.query_commit: %s | %s' % (q, param), True)
            self.connection.commit()
            return True
        except Exception as e:
            self.log.log(logger.LogLevel.ERROR, 'database.query_commit: %s' % e)
            return False