import database

def QUERY_GET_TABLE_CRAWLED():
    """ Dumps table 'crawled' """
    return """ SELECT * FROM crawled"""
def QUERY_GET_TABLE_CRAWL_HISTORY():
    """ Dumps table 'crawl_history' """
    return """ SELECT * FROM crawl_history"""
def QUERY_GET_TABLE_CRAWL_QUEUE():
    """ Dumps table 'crawl_queue' """
    return """ SELECT * FROM crawl_queue"""
def QUERY_GET_TABLE_CRAWL_INFORMATION():
    """ Dumps table 'crawl_information' """
    return """ SELECT * FROM crawl_information"""


def QUERY_TABLE_EXISTS():
    """ Query that checks if a table exists in the database """
    return "SELECT name FROM sqlite_master WHERE type='table' AND name=?"

def QUERY_CREATE_TABLE_CRAWLED():
    """ Create query for table 'crawled' """
    return """ CREATE TABLE crawled (
                Id int PRIMARY KEY,
                domain text,
                urls int,
                amount_crawled int,
                last_crawled date
            )"""

def QUERY_CREATE_TABLE_CRAWL_HISTORY():
    """ Create query for table 'crawl_history' """
    return """ CREATE TABLE crawl_history (
                Id int,
                url text PRIMARY KEY,
                status_code int,
                amount_crawled int,
                last_crawled date,
                FOREIGN KEY (Id) REFERENCES crawled(Id)
        )"""

def QUERY_CREATE_TABLE_CRAWL_QUEUE():
    """ Create query for table 'crawl_queue' """
    return """ CREATE TABLE crawl_queue (
                domain text PRIMARY KEY,
                priority int,
                added date
        )"""
        
def QUERY_CREATE_TABLE_CRAWL_INFORMATION():
    """ Create query for table 'crawl_information' """
    return """ CREATE TABLE crawl_information (
                email text PRIMARY KEY,
                url text,
                extracted_date date,
                FOREIGN KEY (url) REFERENCES crawl_history(url)
        )"""