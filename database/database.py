import sqlite3
import sys
sys.path.append('..')
import 

class Database():
    def __init__(self, log, database_file):
        self.database_file = database_file
        self.connection = sqlite3.connection(self.database_file, check_same_thread=False)
        self.log = log
    
    def check_database(self):
        self.log.log(logger.LogLevel.INFO, 'Checking database tables')