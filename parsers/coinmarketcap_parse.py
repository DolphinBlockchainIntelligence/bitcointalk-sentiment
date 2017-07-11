import sys, requests, pandas, json, re, time, csv, math, exceptions, gc, getopt
from lxml import html, etree
from HTMLParser import HTMLParser
from time import gmtime, strftime, localtime
from datetime import datetime

TOPICS_PER_PAGE         = 20
PARSING_SLEEP           = 2
TIMEOUT_SLEEP           = 10
TIMEOUT_NUM             = 5
TIMEOUT_RETRY           = 60
FIRST_LAST_ONLY         = True
FULL_TOPIC_POSTS        = False
DATA_FILES_DIR          = "..\\data\\"
PARSED_PAGES_SAVE_POSTS = 20
TIMEOUT_RETRY           = 60

headers = { 'User-Agent': 'Mozilla/6.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144' }
URL_CMC_ROOT = 'http://coinmarketcap.com/'
URL_CMC_ASSET_LIST = URL_CMC_ROOT + 'all/views/all/'
PARSING_SLEEP = 2

r = requests.get(URL_CMC_ASSET_LIST, headers = headers)
tree = html.fromstring(r.text)
parserHtml = HTMLParser()

assetsList = {}
table = tree.xpath('//table[@id="currencies-all"]')[0]
rows = table.xpath('.//tr/td[@class="no-wrap currency-name"]/a')
assetNum = len(rows)
print "Number of assets: ", assetNum
assetCount = 0
for row in rows:
    assetUrl  = row.xpath('@href')[0]
    assetName = parserHtml.unescape(row.xpath('descendant-or-self::text()')[0]).encode('utf-8')
    assetFullUrl = URL_CMC_ROOT + assetUrl
    # print assetName, ":" #,  assetFullUrl
    
    assetsList[assetName] = { "CmcUrl"   : assetUrl,
                              "links"    : [] }
    
    time.sleep(PARSING_SLEEP)
    while True:
        try:
            rA = requests.get(assetFullUrl, headers = headers)
            break
        except exceptions.BaseException as e:
            print 'Error:', e.message, ' retrying connection in ', TIMEOUT_RETRY , ' sec.'
            time.sleep(TIMEOUT_RETRY)

    treeA = html.fromstring(rA.text)
    assetNamesFull = treeA.xpath('//div/div/h1[@class="text-large"]')
    if len(assetNamesFull) > 0:
        assetName = assetNamesFull[0].xpath('descendant-or-self::text()')[0].strip().encode('utf-8')
        #assetName = parserHtml.unescape(assetNamesFull[0].xpath('descendant-or-self::text()')[0]).encode('utf-8')

    listItems = treeA.xpath('//ul[@class="list-unstyled"]/li')
    
    for listItem in listItems:
        #messageBoardUrl  = listItem.xpath('//span')[0]
        
        linkType = listItem.xpath('.//span/@title')[0]
        #if linkType in ['Website', 'Explorer', 'Message Board', 'Announcement']:
        try:
            url = listItem.xpath('.//a/@href')[0]
        except:
            url = ''
        if linkType not in ['Rank', 'Tags']:
            assetsList[assetName]["links"].append( { "linkType" : linkType, 
                                                     "linkUrl"  : url  } )
    assetCount += 1
    print assetCount, " / ", assetNum, '( ', assetName, ' )'
    
    if assetCount == 2:
        break

print assetsList
'''
with open('assetsList2.json', 'w') as fAssetsList:
    json.dump(assetsList, fAssetsList, sort_keys=True, indent=4)
fAssetsList.close
''' 
    
