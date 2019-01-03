from flask import Flask, Markup, render_template, request
from datetime import datetime
import sys
sys.path.append('..')
import bot.handler as handler


def start_server():
    app.run(host='0.0.0.0', port=5300)

app = Flask(__name__)
settings = None

@app.route('/')
def root():
    runtime = datetime.now() - handler.HandlerSettings.startTime
    threads = len(handler.HandlerSettings.spiderList)
    max_urls = handler.HandlerSettings.max_urls
    refresh_rate = handler.HandlerSettings.refresh_rate

    return render_template('main_page.html', runtime=runtime, threads=threads, max_urls=max_urls, refresh=refresh_rate)

@app.route('/threads')
def threads():
    runtime = datetime.now() - handler.HandlerSettings.startTime
    spiders = len(handler.HandlerSettings.spiderList)
    max_urls = handler.HandlerSettings.max_urls
    refresh_rate = handler.HandlerSettings.refresh_rate

    new_threads = handler.Handler.new_thread_amount
    threads = ""
    if new_threads is None or new_threads == spiders:
        threads = str(spiders)
    else:
        threads = "%d (%d)" % (spiders, new_threads - spiders)
    
    threadStats = []
    for index in range(len(handler.HandlerSettings.spiderList)):
        spider = handler.HandlerSettings.spiderList[index]
        runtime = datetime.now() - spider.start_time
        completedMax = '%d/%d' % (spider.crawled_urls, spider.max_urls)
        values = (index, spider.name, runtime, spider.domain, completedMax,
        len(spider.new_domains), len(spider.queue))
        threadStats.append(values)
    return render_template('threads.html', runtime=runtime, threads=threads, max_urls=max_urls, refresh=refresh_rate, result=threadStats)

@app.route('/settings', methods=["GET", "POST"])
def settings():
    runtime = datetime.now() - handler.HandlerSettings.startTime
    threads = len(handler.HandlerSettings.spiderList)
    max_urls = handler.HandlerSettings.max_urls
    refresh_rate = handler.HandlerSettings.refresh_rate

    # TODO: Check for wrong input
    if request.method == "POST":
        threadRequest = get_integer(request.form["threads"])
        handler.Handler.new_thread_amount = threadRequest

        maxUrlRequest = get_integer(request.form["max_urls"])
        handler.HandlerSettings.max_urls = maxUrlRequest

        refreshRateRequest = get_float(request.form["refresh"])
        handler.HandlerSettings.refresh_rate = refreshRateRequest

        message = "Changed: threads: %d -> %d\n" % (threads, threadRequest)
        message += "Max urls: %d -> %d\n" % (max_urls, maxUrlRequest)
        message += "Refresh rate: %f -> %f\n" % (refresh_rate, refreshRateRequest)
        
        return render_template('settings.html', runtime=runtime, threads=threads, max_urls=max_urls, refresh=refresh_rate, message=message)
    else:
        return render_template('settings.html', runtime=runtime, threads=threads, max_urls=max_urls, refresh=refresh_rate)

@app.route('/database')
def database():
    return render_template('database.html')

def get_float(value):
    try:
        return float(value)
    except:
        return 0.0

def get_integer(value):
    try:
        return int(value)
    except:
        return 0