import re
import urllib
import urllib2
import xml.etree.cElementTree as ElementTree

# See additional endpoints and parameters at: https://www.nasdaqdod.com/ 
url = 'http://ws.nasdaqdod.com/v1/NASDAQAnalytics.asmx/GetSummarizedTrades'

# Change symbols and date range as needed (not more that 30 days at a time)
values = {'_Token' : 'BC2B181CF93B441D8C6342120EB0C971',
          'Symbols' : 'AAPL,MSFT',
          'StartDateTime' : '2/1/2015 00:00:00.000',
          'EndDateTime' : '2/18/2015 23:59:59.999',
          'MarketCenters' : '' ,
          'TradePrecision': 'Hour',
          'TradePeriod':'1'}

# Build HTTP request
request_parameters = urllib.urlencode(values)
req = urllib2.Request(url, request_parameters)

# Submit request
try:
    response = urllib2.urlopen(req)
except urllib2.HTTPError as e:
    print(e.code)
    print(e.read())

# Read response
the_page = response.read()

# Parse page XML from string
root = ElementTree.XML(the_page)

# DO SOMETHING....