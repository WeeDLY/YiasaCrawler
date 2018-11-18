import requests
import logger
from bs4 import BeautifulSoup
import re, time

class Spider:
    queue = set()
    re_url = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    @staticmethod
    def print_queue():
        print(len(Spider.queue))
        print(Spider.queue)

    def __init__(self, log, id, domain):
        self.log = log
        self.id = id
        # Removes '/' suffix if it's there
        self.domain = domain[:len(domain)-1] if domain[len(domain) - 1] == '/' else domain
        self.queue = set()
        self.completed_queue = set()
        self.new_domains = set()
        self.crawled_urls = 0
        self.robots = {"disallow":[], "allow":[]}
        self.crawl_delay = 0

    def to_string(self):
        print('id: %s, domain: %s, crawl-delay: %d' % (self.id, self.domain, self.crawl_delay))
    
    def start_crawl(self):
        """ Getting ready to crawl a domain.
            This means, parsing robots.txt and crawling top-url for new urls """
        self.parse_robots()

        req = self.request(self.domain)
        soup = BeautifulSoup(req.text, 'html.parser')
        valid_urls = self.extract_url(soup)
        self.add_to_queue(valid_urls)
        self.crawl()
        self.crawled_urls += 1
    
    def request(self, url):
        self.crawled_urls += 1
        r = requests.get(url)
        return r

    def crawl(self):
        """ Iterate through the entire queue stack """
        while self.queue:
            url = self.queue.pop()
            self.completed_queue.add(url)
            req = self.request(url)
            soup = BeautifulSoup(req.text, 'html.parser')
            valid_urls = self.extract_url(soup)
            self.add_to_queue(valid_urls)
            print('Crawled: %d, queue: %d, completed_queue: %d, new_domains: %d' % (self.crawled_urls, len(self.queue), len(self.completed_queue), len(self.new_domains)))
            time.sleep(self.crawl_delay)
    
    def add_to_queue(self, urls):
        for url in urls:
            if self.domain not in url:
                self.new_domains.add(url)
            elif url not in self.queue and url not in self.completed_queue:
                self.queue.add(url)

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

            url = url[1:len(url)] if url[0] == '.' else url # Remove '.' prefix in url, if websites use it
            url = url if url[0] == '/' else '/%s' % url # Adds '/' to url, if it's a relative path url
            url = '%s%s' % (self.domain, url)
            if self.valid_url(url):
                valid_urls.add(url)
        return valid_urls

    def parse_robots(self):
        r = requests.get('%s/robots.txt' % self.domain)
        if r.status_code == 404:
            print('No robots.txt')
        
        user_agent = True
        for line in r.text.lower().split('\n'):
            if line.startswith('user-agent'):
                if '*' in line:
                    user_agent = True
                else:
                    user_agent = False
            if user_agent:
                if line.startswith('disallow:'):
                    self.robots["disallow"].append(line.split(':')[1].replace(' ', ''))
                elif line.startswith('allow:'):
                    self.robots["allow"].append(line.split(':')[1].replace(' ', ''))
                elif line.startswith('crawl-delay'):
                    delay = int(re.search('\d+', line).group())
                    self.crawl_delay = delay
        
        print('disallow')
        print(self.robots["disallow"])
        print('allow')
        print(self.robots["allow"])

    def valid_url(self, url):
        """ Checks if a url is valid """
        return re.match(Spider.re_url, url) is not None