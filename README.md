# YiasaCrawler
Web crawler

## Requirements:
    requests
    BeautifulSoup
    validate-email-address
    py3dns
    sqlite3
    flask (for webserver)

### LogLevels:
    Debug: Technical details
    Info: General information what the bot is doing
    Warning: Something very minor occured. i.e No response from web server
    Error: Something bad occured. Unable to query database, etc.
    Critical: Something that could crash the application or is detrimental to the program. i.e: Not able to commit changes to db.