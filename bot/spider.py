from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests
import re, time
import sys
from datetime import datetime, timedelta
from validate_email_address import validate_email
sys.path.append('..')

import util.logger as logger
import util.classes as classes
import database.query as query
import bot.handler

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
        self.parse_urls(valid_urls)
        self.crawl()

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

            self.parse_urls(valid_urls)
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
        self.insert_crawl_history()

        # Remove the domain from the 'crawl_queue' table
        domainRemoveQueue = self.db.query_execute(query.QUERY_DELETE_CRAWL_QUEUE(), (self.domain, ))
        if domainRemoveQueue:
            self.log.log(logger.LogLevel.INFO, "Removed %s from 'crawl_queue'" % self.domain)
        else:
            self.log.log(logger.LogLevel.ERROR, "Unable to remove %s from 'crawl_queue'" % self.domain)

        self.insert_new_domains()
        
        # Add emails to db
        self.insert_emails()
    
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

        self.crawl_history.append(classes.CrawlHistory(self.domain, url, req.status_code, datetime.now()))
        if len(self.crawl_history) >= self.crawl_history_limit:
            self.log.log(logger.LogLevel.DEBUG, '%d >= %d' % (len(self.crawl_history), self.crawl_history_limit))
            self.insert_crawl_history()
        return req

    def url_follow_robots(self, url):
        """ Checks if a url breaks the robots.txt rules """
        for disallow in self.robots["disallow"]:
            invalid = re.search(disallow, url, re.IGNORECASE)
            if invalid:
                return False
        return True

    def parse_urls(self, urls):
        """ Parse all urls and takes care of them """
        for url in urls:
            urlParsed = urlparse(url)
            domain = '%s://%s' % (urlParsed.scheme, urlParsed.netloc)
            if self.domain != domain:
                self.new_domains.add(classes.Domain(domain, 0, 0, datetime.now()))
            elif url not in self.queue and url not in self.completed_queue:
                if self.url_follow_robots(url):
                    self.queue.add(url)

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

    def extract_email(self, text, url):
        """ Extracts emails from website """
        emails = set(re.findall(Spider.re_email, text))
        valid_emails = []
        for email in emails:
            if self.valid_email(email):
                valid_emails.append(classes.Email(email, url, datetime.now()))

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

    def valid_url(self, url):
        """ Checks if a url is valid """
        return re.match(Spider.re_url, url) is not None
    
    def valid_email(self, email, check_mx=True):
        """ Checks if the email is valid """
        return validate_email(email, check_mx=check_mx)
    
    def insert_new_domains(self):
        """ Insert new found domains to db to be crawled later """
        if len(self.new_domains) <= 0:
            return None
            
        q = "INSERT OR IGNORE INTO crawl_queue(domain, priority, started, added) VALUES"
        param = ()
        for domain in self.new_domains:
            q += "(?, ?, ?, ?),"
            param += (domain.domain, domain.priority, domain.started, domain.date_added)
        q = q[:-1]
        q += ";"
        
        insertedDomains = self.db.query_execute(q, param)
        if insertedDomains:
            self.log.log(logger.LogLevel.DEBUG, "Inserted: %d domains from %s" % (len(self.new_domains), self.domain))
        else:
            self.log.log(logger.LogLevel.ERROR, "Failed to insert: %d domains from %s" % (len(self.new_domains), self.domain))
        return True

    def insert_crawl_history(self):
        """ Adds all objects in self.crawl_history to database """
        q = "INSERT OR REPLACE INTO crawl_history(id, url, status_code, amount_crawled, last_crawled) VALUES"
        param = ()
        if len(self.crawl_history) <= 0:
            return None

        for history in self.crawl_history:
            q += "\n((SELECT rowid FROM crawled WHERE domain = ?), ?, ?, (SELECT CASE WHEN COUNT(1) > 0 THEN amount_crawled+1 ELSE 1 END AS [Value] FROM crawl_history WHERE url = ?), ?),"
            param += (history.domain, history.url, history.status_code, history.url, history.date)
        q = q[:-1]
        q += ";"
        insertHistory = self.db.query_execute(q, param)
        if insertHistory:
            self.log.log(logger.LogLevel.DEBUG, 'Pushed(%s): %d entries into crawl_history' % (self.domain, len(self.crawl_history)))
        else:
            self.log.log(logger.LogLevel.ERROR, 'Failed to push(%s): %d entries into crawl_history' % (self.domain, len(self.crawl_history)))
        self.crawl_history = []

    def insert_emails(self):
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
        
        insertedEmails = self.db.query_execute(q, param)
        if insertedEmails:
            self.log.log(logger.LogLevel.DEBUG, "Inserted: %d emails from %s" % (len(self.emails), self.domain))
        else:
            self.log.log(logger.LogLevel.ERROR, "Failed to insert %d emails from: %s"% (len(self.emails), self.domain))
        return True