import database

""" GET TABLE queries """
def QUERY_GET_TABLE_CRAWLED():
    """ Dumps table 'crawled' """
    return """ SELECT rowid, * FROM crawled"""
def QUERY_GET_TABLE_CRAWL_HISTORY():
    """ Dumps table 'crawl_history' """
    return """ SELECT rowid, * FROM crawl_history"""
def QUERY_GET_TABLE_CRAWL_QUEUE():
    """ Dumps table 'crawl_queue' """
    return """ SELECT rowid, * FROM crawl_queue"""
def QUERY_GET_TABLE_CRAWL_INFORMATION():
    """ Dumps table 'crawl_information' """
    return """ SELECT rowid, * FROM crawl_information"""

""" GET queries """
def QUERY_GET_DOMAIN_IN_DB():
    """ Checks if a domain is in 'crawled' or 'crawl_queue' """
    return """ SELECT 1 FROM (
                SELECT domain FROM crawled
                UNION ALL
                SELECT domain FROM crawl_queue)
                WHERE domain = ? """

def QUERY_GET_CRAWL_QUEUE():
    """ returns urls that should be queued """
    return """ SELECT domain FROM crawl_queue WHERE started = 0 ORDER BY priority DESC, added ASC LIMIT ? """

def QUERY_GET_DOMAIN_IN_CRAWLED():
    """ Checks if a domain has entry in table 'crawled' """
    return """ SELECT * FROM crawled
                WHERE domain = ?"""

def QUERY_GET_EMAILS_WITHIN_TIMESPAN():
    """ returns amount of emails gotten with a set timespan """
    return """ SELECT COUNT(email) FROM crawl_information
                WHERE extracted_date >= ? """

def QUERY_GET_CRAWLED_WITHIN_TIMESPAN():
    """ returns amount of crawled websites within a set timespan """
    return """ SELECT COUNT(*) FROM crawled
                WHERE last_crawled >= ? """

""" INSERT queries """
def QUERY_INSERT_TABLE_CRAWL_QUEUE():
    """ Insert or ignore into table 'crawl_queue' """
    return """ INSERT OR IGNORE INTO crawl_queue(domain, priority, started, added)
                VALUES(?, ?, ?, ?)
    """

def QUERY_INSERT_CRAWL_QUEUE_STARTED():
    """ marks domain as 'started' in DB """
    return """ UPDATE crawl_queue SET
                started = 1
                WHERE domain = ? """

def QUERY_INSERT_CRAWL_INFORMATION():
    return """ INSERT or ignore into crawl_information(email, url, extracted_date)
                VALUES (?, ?, ?)"""

def QUERY_INSERT_MULTIPLE_CRAWL_INFORMATION():
    return """ INSERT or ignore into crawl_information(email, url, extracted_date) VALUES"""

def QUERY_UPDATE_TABLE_CRAWLED():
    """ Updates table 'crawled' based on domain """
    return """ UPDATE crawled SET
                urls = ?,
                amount_crawled = ?,
                finished_crawling = ?,
                last_crawled = ?
                WHERE domain = ? """

def QUERY_INSERT_TABLE_CRAWLED():
    """ inserts into 'crawled'"""
    return """INSERT INTO crawled(domain, urls, amount_crawled, finished_crawling, last_crawled)
                VALUES(?, ?, ?, ?, ?)
    """

def QUERY_INSERT_TABLE_CRAWL_HISTORY():
    """ inserts OR REPLACES into 'crawl_history' 
        args: domain, url, status_code, url, last_crawled
    """
    return """INSERT OR REPLACE INTO crawl_history(id, url, status_code, amount_crawled, last_crawled)
    VALUES((SELECT rowid FROM crawled WHERE domain = ?),
    ?,
    ?,
    (SELECT CASE WHEN COUNT(1) > 0 THEN amount_crawled+1 ELSE 1 END AS [Value] FROM crawl_history WHERE url = ?),
    ?)"""

""" DELETE queries """
def QUERY_DELETE_CRAWL_QUEUE():
    """ Deletes a domain from 'crawl_queue' """
    return """ DELETE FROM crawl_queue
                WHERE domain = ? and started = 1 """

def QUERY_TABLE_EXISTS():
    """ Query that checks if a table exists in the database """
    return "SELECT name FROM sqlite_master WHERE type='table' AND name=?"

""" CREATE TABLES queries """
def QUERY_CREATE_TABLE_CRAWLED():
    """ Create query for table 'crawled'
        Id used is the rowid
        domain: domain that was crawled
        urls: amount of new urls found from this crawl
        amount_crawled: amount of urls crawled
        last_crawled: date last crawled
    """
    return """ CREATE TABLE crawled (
                domain text,
                urls int,
                amount_crawled int,
                finished_crawling boolean,
                last_crawled date
            )"""

def QUERY_CREATE_TABLE_CRAWL_HISTORY():
    """ Create query for table 'crawl_history'
        Id: 'crawled'.rowid
        url: url that was crawled
        status_code: status code returned when crawled
        amount_crawled: How many times this specific url have been crawled
        last_crawled: Date this was crawled last
    """
    return """ CREATE TABLE crawl_history (
                id int,
                url text PRIMARY KEY,
                status_code int,
                amount_crawled int,
                last_crawled date
        )"""

def QUERY_CREATE_TABLE_CRAWL_QUEUE():
    """ Create query for table 'crawl_queue'
        domain: domain to be crawled
        priority: priority of when to be crawled (higher number = higher priority)
        added: When it was added to the queue
    """
    return """ CREATE TABLE crawl_queue (
                domain text PRIMARY KEY,
                priority int,
                started boolean,
                added date
        )"""
        
def QUERY_CREATE_TABLE_CRAWL_INFORMATION():
    """ Create query for table 'crawl_information'
        email: email address that was found
        url: url email was found on
        extracted_date: When this email was found
    """
    return """ CREATE TABLE crawl_information (
                email text PRIMARY KEY,
                url text,
                extracted_date date,
                FOREIGN KEY (url) REFERENCES crawl_history(url)
        )"""