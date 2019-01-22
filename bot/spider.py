from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests
import re, time
import sys
from datetime import datetime, timedelta
from validate_email_address import validate_email
sys.path.append('..')

import util.logger as logger
import database.query as query
import bot.handler

class Email():
    """ Class that holds on information about extracted emails """
    def __init__(self, email, url, extract_date):
        self.email = email
        self.url = url
        self.extract_date = extract_date

    def __str__(self):
        return '"%s", "%s", "%s"' % (self.email, self.url, self.extract_date)

class CrawlHistory():
    """ Class containing information about a crawl """
    def __init__(self, domain, url, status_code, date):
        self.domain = domain
        self.url = url
        self.status_code = status_code
        self.date = date

class Spider:
    queue = set()
    re_url = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    re_email = re.compile(
        """([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)"""
    )

    @staticmethod
    def print_queue():
        print(len(Spider.queue))
        print(Spider.queue)

    def __init__(self, log, db, name, domain, max_urls):
        self.log = log
        self.db = db
        self.name = name
        # Removes '/' suffix if it's there
        self.domain = domain[:len(domain)-1] if domain[len(domain) - 1] == '/' else domain
        self.queue = set()
        self.completed_queue = set()
        self.new_domains = set()
        self.emails = set()
        self.crawled_urls = 0
        self.robots = {"disallow":[], "allow":[]}
        self.crawl_delay = 0
        self.max_urls = max_urls
        self.start_time = datetime.now()
        self.run = True
        self.crawl_history = []
        self.crawl_history_limit = 100

    def __str__(self):
        return 'Name:%s @domain: %s' % (self.name, self.domain)
    
    def start_crawl(self):
        """ Getting ready to crawl a domain.
            This means, parsing robots.txt and crawling top-url for new urls """
        self.parse_robots()

        req = self.request(self.domain)
        if req is None:
            self.log.log(logger.LogLevel.WARNING, 'Request failed')
            self.finish_crawl()
            return
        soup = BeautifulSoup(req.text, 'html.parser')
        valid_urls = self.extract_url(soup)
        self.add_to_queue(valid_urls)
        self.crawl()
    
    def request(self, url):
        """ sends a http request to url.
            Adds crawled url to self.crawl_history """
        self.crawled_urls += 1
        
        try:
            req = requests.get(url, timeout=3)
        except requests.exceptions.Timeout as timeout:
            self.log.log(logger.LogLevel.DEBUG, 'Request timed out: %s' % url)
            return None
        except Exception as e:
            self.log.log(logger.LogLevel.WARNING, 'Request exception: (%s) %s' % (url, e))
            return None

        self.crawl_history.append(CrawlHistory(self.domain, url, req.status_code, datetime.now()))
        if len(self.crawl_history) >= self.crawl_history_limit:
            self.add_crawl_history_db()
        return req

    def crawl(self):
        """ Iterate through the entire queue stack """
        if self.queue == None:
            self.finish_crawl()
            return

        while self.queue and self.crawled_urls < self.max_urls and self.run:
            url = self.queue.pop()
            self.completed_queue.add(url)
            req = self.request(url)
            if req is None:
                self.log.log(logger.LogLevel.WARNING, 'Request is None, skipping')
                continue
            
            if req.text is None:
                self.log.log(logger.LogLevel.WARNING, 'Request.text is None, skipping')
                continue

            soup = BeautifulSoup(req.text, 'html.parser')
            valid_urls = self.extract_url(soup)

            self.extract_email(req.text, req.url)

            self.add_to_queue(valid_urls)
            time.sleep(self.crawl_delay)
        
        if self.run:
            self.log.log(logger.LogLevel.DEBUG, 'Spiderthread: %s(%s) was stopped' % (self.name, self.domain))

        # Finished crawling, insert stats to DB
        self.finish_crawl()
    
    def finish_crawl(self):
        """ Finished crawling, inserts result to DB """
        domainExists = self.db.query_exists(query.QUERY_GET_DOMAIN_IN_DB(), (self.domain, ))
        if domainExists:
            dbCrawled = self.db.query_execute(query.QUERY_UPDATE_TABLE_CRAWLED(), (len(self.new_domains), self.crawled_urls, 1, datetime.now(), self.domain, ))
            if dbCrawled:
                self.log.log(logger.LogLevel.INFO, 'Added crawl stats to DB from: %s' % self.name)
            else:
                self.log.log(logger.LogLevel.WARNING, 'Unable to insert crawl stats to DB from: %s' % self.name)
        else:
            self.log.log(logger.LogLevel.ERROR, 'Domain: %s was finshed crawling, but does not exist in DB!' % self.domain)
        
        # Push remaining self.crawl_history to database
        self.add_crawl_history_db()

        # Remove the domain from the 'crawl_queue' table
        domainRemoveQueue = self.db.query_execute(query.QUERY_DELETE_CRAWL_QUEUE(), (self.domain, ))
        if domainRemoveQueue:
            self.log.log(logger.LogLevel.INFO, "Removed %s from 'crawl_queue'" % self.domain)
        else:
            self.log.log(logger.LogLevel.ERROR, "Unable to remove %s from 'crawl_queue'" % self.domain)
        
        for domain in self.new_domains:
            domainDB = self.db.query_execute(query.QUERY_INSERT_TABLE_CRAWL_QUEUE(), (domain, 0, 0, datetime.now()))
            if domainDB:
                self.log.log(logger.LogLevel.DEBUG, "Inserted to add 'crawl_queue': %s" % domain)
            else:
                self.log.log(logger.LogLevel.WARNING, "Failed to add 'crawl_queue': %s" % domain)
        
        # Add emails to db
        self.insert_emails_to_db()

        # Push everything to database
        self.db.commit()
    
    def add_to_queue(self, urls):
        """ Adds a list of urls to the queue """
        for url in urls:
            urlParsed = urlparse(url)
            domain = '%s://%s' % (urlParsed.scheme, urlParsed.netloc)
            if self.domain != domain:
                self.new_domains.add(domain)
            elif url not in self.queue and url not in self.completed_queue:
                if self.url_follow_robots(url):
                    self.queue.add(url)

    def add_crawl_history_db(self):
        """ Adds all objects in self.crawl_history to database """
        history_success = 0
        history_error = 0
        for history in self.crawl_history:
            success = self.db.query_execute(query.QUERY_INSERT_TABLE_CRAWL_HISTORY(), (history.domain, history.url, history.status_code, history.url, history.date, ))
            if success:
                history_success += 1
            else:
                history_error += 1
            self.crawl_history.remove(history)
        self.log.log(logger.LogLevel.DEBUG, 'Pushed spider.crawl_history to database. Success: %d, Failed: %d' % (history_success, history_error))

    def extract_email(self, text, url):
        """ Extracts emails from website """
        emails = set(re.findall(Spider.re_email, text))
        valid_emails = []
        for email in emails:
            if self.valid_email(email):
                valid_emails.append(Email(email, url, datetime.now()))

        self.emails = self.emails.union(valid_emails)

    def extract_url(self, soup):
        """ Extract all urls from a soup """
        valid_urls = set()
        urls = [link.get('href') for link in soup.find_all('a', href=True)]
        for url in urls:
            if self.valid_url(url):
                valid_urls.add(url)
                continue
            if url.startswith('mailto'):
                continue
            if url == '':
                continue
            url = url[1:len(url)] if url[0] == '.' else url # Remove '.' prefix in url, if websites use it
            url = url if url[0] == '/' else '/%s' % url # Adds '/' to url, if it's a relative path url
            url = '%s%s' % (self.domain, url)
            if self.valid_url(url):
                valid_urls.add(url)
        return valid_urls

    def url_follow_robots(self, url):
        """ Checks if a url breaks the robots.txt rules """
        for disallow in self.robots["disallow"]:
            invalid = re.search(disallow, url, re.IGNORECASE)
            if invalid:
                return False
        return True

    def parse_robots(self):
        """ Parses robots.txt. disallow/allow is placed in self.robots """
        try:
            r = requests.get('%s/robots.txt' % self.domain)
        except Exception as e:
            self.log.log(logger.LogLevel.WARNING, 'Error while parsing robots.txt: %s' % e)
            return

        user_agent = True
        for line in r.text.lower().split('\n'):
            if line.startswith('user-agent'):
                if '*' in line:
                    user_agent = True
                else:
                    user_agent = False
            if user_agent:
                if line.startswith('disallow:'):
                    disallow = line.split(':')[1].replace(' ', '')
                    disallow = disallow.replace('*', '.+')
                    self.robots["disallow"].append(disallow)
                elif line.startswith('allow:'):
                    self.robots["allow"].append(line.split(':')[1].replace(' ', ''))
                elif line.startswith('crawl-delay'):
                    delay = int(re.search('\d+', line).group())
                    self.crawl_delay = delay

    def valid_url(self, url):
        """ Checks if a url is valid """
        return re.match(Spider.re_url, url) is not None
    
    def valid_email(self, email, check_mx=True):
        """ Checks if the email is valid """
        return validate_email(email, check_mx=check_mx)
    
    def insert_emails_to_db(self):
        """ Inserts found emails to database """
        if len(self.emails) <= 0:
            self.log.log(logger.LogLevel.INFO, "No emails found from: %s" % self.domain)
            return False

        q = query.QUERY_INSERT_MULTIPLE_CRAWL_INFORMATION()
        param = ()
        for email in self.emails:
            q += "\n(?, ?, ?),"
            param += (email.email, email.url, email.extract_date)
        q = q[:-1]
        q += ";"
        
        addedEmails = self.db.query_execute(q, param)
        if addedEmails:
            self.log.log(logger.LogLevel.INFO, "Inserted: %d emails from %s" % (len(self.emails), self.domain))
        else:
            self.log.log(logger.LogLevel.WARNING, "Failed to insert %d emails from: %s"% (len(self.emails), self.domain))
        return True