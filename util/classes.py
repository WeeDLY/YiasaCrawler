class SpiderTable():
    """ Class that contains every spider stats that are displayed to the web server """
    def __init__(self, index, spider, runtime):
        self.index = index
        self.spider = spider
        self.runtime = runtime

class Domain():
    """ Class that holds information about newly found domains """
    def __init__(self, domain, priority, started, date_added):
        self.domain = domain
        self.priority = priority
        self.started = started
        self.date_added = date_added
    
    def __hash__(self):
        return hash(self.domain)
    
    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.domain == other.domain

class Email():
    """ Class that holds information about extracted emails """
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