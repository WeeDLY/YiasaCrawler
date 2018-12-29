from flask import Flask, Markup, render_template, request
from datetime import datetime
import sys
sys.path.append('..')
import yiasa.handler as handler


def start_server():
    app.run(host='0.0.0.0', port=5300)

app = Flask(__name__)
settings = None

@app.route('/')
def root():
    runtime = datetime.now() - handler.HandlerSettings.startTime
    threads = len(handler.HandlerSettings.spiderList)
    
    threadStats = []
    for index in range(len(handler.HandlerSettings.spiderList)):
        spider = handler.HandlerSettings.spiderList[index]
        values = (index, spider.name, spider.domain, len(spider.new_domains), 
        spider.crawled_urls, len(spider.queue))
        threadStats.append(values)
    return render_template('main_page.html', runtime=runtime, threads=threads, result=threadStats)

@app.route('/settings')
def settings():
    runtime = datetime.now() - handler.HandlerSettings.startTime
    threads = len(handler.HandlerSettings.spiderList)
    return render_template('settings.html', runtime=runtime, threads=threads)

@app.route('/changes', methods=["POST"])
def threads():
    if request.method == "POST":
        threads = get_number(request.form["threads"])
        handler.Handler.new_thread_amount = threads
    return 'Threads: %s' % str(threads)


def get_number(value):
    try:
        return int(value)
    except:
        return 0