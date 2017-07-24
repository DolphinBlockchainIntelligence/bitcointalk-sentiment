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
URL_ROOT = 'https://bitcointalk.org/index.php?action=profile;u='
PARSING_SLEEP = 2

try:
    with open(DATA_FILES_DIR + 'bttUsers.json', 'r') as fUserList:
        userList = json.load(fUserList)
except:
    userList = {}

startItem = len(userList)

currItem = startItem + 1
#while True:
#    currItem += 1

r = requests.get(URL_ROOT + str(currItem), headers = headers)
tree = html.fromstring(r.text)
# parserHtml = HTMLParser()
tables = tree.xpath('//td[@class = "windowbg"]')
print len(tables)

#rows = tables[1].xpath('.//td/table/tbody/tr')
rows = tables[1].xpath('.//table')
print len(rows)

sys.exit(0)

# assetsList = {}
# table = tree.xpath('//table[@id="currencies-all"]')[0]

'''
tableLines = table.xpath(".//tr")
print len(tableLines)
for line in tableLines:
    cols = line.xpath('.//td[@class="no-wrap currency-name"]/a')
    if len(cols) > 0:
        print cols[0].xpath('descendant-or-self::text()')[0]

    cols = line.xpath('.//td[@class="text-center"]/a')
    if len(cols) > 0:
        print cols[0].xpath('descendant-or-self::text()')[0]

sys.exit(0)
'''

rows = table.xpath('.//tr/td[@class="no-wrap currency-name"]/a')
assetNum = len(rows)
print "Number of assets: ", assetNum
assetCount = 0
assetRank  = 0
for row in rows:
    # assumption that listing is always ordered by capitalization
    assetRank += 1 
    assetUrl  = row.xpath('@href')[0]
    # assetName = parserHtml.unescape(row.xpath('descendant-or-self::text()')[0]).encode('utf-8')
    assetFullUrl = URL_CMC_ROOT + assetUrl
    # print assetName, ":" #,  assetFullUrl
    
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

    assetsList[assetName] = { "rank"     : assetRank,
                              "cmcUrl"   : assetUrl,
                              "links"    : [] }        


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
    
    #if assetCount == 10:
    #    break

# print assetsList

with open('assetsList.json', 'w') as fAssetsList:
    json.dump(assetsList, fAssetsList, sort_keys=True, indent=4)
fAssetsList.close
 
    
