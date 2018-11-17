import requests
import logger
from bs4 import BeautifulSoup
import re

class Spider:
    queue = set()

    @staticmethod
    def print_queue():
        print(len(Spider.queue))
        print(Spider.queue)

    def __init__(self, log, id, domain):
        self.log = log
        self.id = id
        self.domain = domain
        self.queue = set()
        self.completed_queue = set()

    def to_string(self):
        print('id: %s, domain: %s' % (self.id, self.domain))
    
    def crawl(self):
        r = requests.get(self.domain)
        print(r.status_code)
        soup = BeautifulSoup(r.text, 'html.parser')
        for link in soup.findAll('a', attrs={'href': re.compile("^http://")}):
            print(link.get('href'))