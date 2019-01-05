from flask import Flask, Markup, render_template, request
from datetime import datetime
import sys
import logging
import sqlite3
sys.path.append('..')
import bot.handler as handler

class SpiderTable():
    def __init__(self, index, spider, runtime):
        self.index = index
        self.spider = spider
        self.runtime = runtime

def start_server(db):
    global database, connection
    database = db
    connection = sqlite3.connect(database.database_file, check_same_thread=False)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=5300)

app = Flask(__name__)
database = None
connection = None

@app.route('/')
def root():
    runtime = get_runtime()
    threads = get_threads()
    max_urls = handler.HandlerSettings.max_urls
    refresh_rate = handler.HandlerSettings.refresh_rate

    return render_template('main_page.html', runtime=runtime, threads=threads, max_urls=max_urls, refresh=refresh_rate)

@app.route('/threads', methods=["GET", "POST"])
def threads():
    runtime = get_runtime()
    spiders = get_threads()
    max_urls = handler.HandlerSettings.max_urls
    refresh_rate = handler.HandlerSettings.refresh_rate

    new_threads = handler.Handler.new_thread_amount
    threads = ""
    if new_threads is None or new_threads == spiders:
        threads = str(spiders)
    else:
        threads = "%d (%d)" % (spiders, new_threads - spiders)
    
    threadStats = []
    for index in range(get_threads()):
        spider = handler.HandlerSettings.spiderList[index]
        runtime = datetime.now() - spider.start_time
        sTable = SpiderTable(index, spider, runtime)
        threadStats.append(sTable)
    if request.method == "POST":
        threadIndex = get_integer(request.form["thread"])
        spider =  handler.HandlerSettings.spiderList[threadIndex]
        print('Stopping thread: %s' % spider.domain)
        spider.run = False

    return render_template('threads.html', runtime=runtime, threads=threads, max_urls=max_urls, refresh=refresh_rate, result=threadStats)

@app.route('/settings', methods=["GET", "POST"])
def settings():
    runtime = get_runtime()
    threads = get_threads()
    max_urls = handler.HandlerSettings.max_urls
    refresh_rate = handler.HandlerSettings.refresh_rate

    # TODO: Check for invalid input
    if request.method == "POST":
        threadRequest = get_integer(request.form["threads"])
        handler.Handler.new_thread_amount = threadRequest

        maxUrlRequest = get_integer(request.form["max_urls"])
        handler.HandlerSettings.max_urls = maxUrlRequest

        refreshRateRequest = get_float(request.form["refresh"])
        handler.HandlerSettings.refresh_rate = refreshRateRequest

        message = []
        if same_value(threads, threadRequest) is False:
            message.append("Changed threads: %d -> %d\n" % (threads, threadRequest))
        if same_value(max_urls, maxUrlRequest) is False:
            message.append("Changed max urls: %d -> %d\n" % (max_urls, maxUrlRequest))
        if same_value(refresh_rate, refreshRateRequest) is False:
            message.append("Changed refresh rate: %f -> %f\n" % (refresh_rate, refreshRateRequest))

        threads = threadRequest
        max_urls = maxUrlRequest
        refresh_rate = refreshRateRequest
        return render_template('settings.html', runtime=runtime, threads=threads, max_urls=max_urls, refresh=refresh_rate, message=message)
    else:
        return render_template('settings.html', runtime=runtime, threads=threads, max_urls=max_urls, refresh=refresh_rate)

@app.route('/database', methods=["GET", "POST"])
def database():
    tableHeader = []
    result = []
    if request.method == "POST":
        query = request.form["query"]
        try:
            cur = connection.cursor()
            cur.execute(query)
            queryResult = cur.fetchall()
            if queryResult is None:
                result = "No result matched: %s" % query
                tableHeader = ""
            else:
                for desc in cur.description:
                    tableHeader.append(desc[0])
                    result = queryResult
        except Exception as e:
            result = "Could not execute query: %s" % query
    return render_template('database.html', tableHeader=tableHeader, result=result)

def get_runtime():
    """ returns current runtime """
    return datetime.now() - handler.HandlerSettings.startTime

def get_threads():
    """ returns amount of threads """
    return len(handler.HandlerSettings.spiderList)

def same_value(value1, value2):
    """ Checks if values are the same """
    return value1 == value2

def get_float(value):
    """ Converts a variable to float """
    try:
        return float(value)
    except:
        return 0.0

def get_integer(value):
    """ Converts a variable to int """
    try:
        return int(value)
    except:
        return 0