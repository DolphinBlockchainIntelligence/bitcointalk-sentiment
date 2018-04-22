#reload(sys) sys.setdefaultencoding('utf-8')
import sys, requests, json, re, time, csv, math, exceptions, gc, getopt, furl, random
from lxml import html, etree
from HTMLParser import HTMLParser
from time import gmtime, strftime, localtime
from datetime import datetime
from pyvirtualdisplay import Display
from selenium import webdriver

TOPICS_PER_PAGE          = 20
PARSING_SLEEP            = 20    # 20
PARSING_SLEEP_RAND_RANGE = 8     # 8    should be no greater than PARSING_SLEEP
TIMEOUT_SLEEP            = 20    # 20
TIMEOUT_NUM              = 5     #
TIMEOUT_RETRY            = 600   # 600
TIMEOUT_RAND_RANGE       = 20    # 20   should be no greater than TIMEOUT_RETRY
FIRST_LAST_ONLY          = True
FULL_TOPIC_POSTS         = False
DATA_FILES_DIR           = "../data/"
PARSED_PAGES_SAVE_POSTS  = 20
TOP_CMC_ITEMS            = 400   # top coinmarketcap items to parse
PROXY_TIMEOUT            = 7

# globals:
verboseMode = False
browserMode = False
display = Display(visible=0, size=(1024, 768))
display.start()
browser = webdriver.Firefox()

# headers = { 'User-Agent': 'Mozilla/6.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144' }
headers = { 'User-Agent': 'Yandex/1.01.001 (compatible; Win16; I)' }
urlStart = 'https://bitcointalk.org/index.php?board=159.0'
urlTemplate = 'https://bitcointalk.org/index.php?board=159.'
urlTopicTemplate = 'https://bitcointalk.org/index.php?topic='

# globals for rotateProxy()
proxies = []
proxy_cur = 0
proxy_rotations = 1
proxy = {}

def rotateProxy(failed=True):
    global proxy_cur, proxy, proxy_rotations
    
    if not proxies:
        return
        
    if failed:
        proxies[proxy_cur]["failed"] += 1
    
    proxy_rotations_old = proxy_rotations
    while True:
        proxy_cur += 1
        if proxy_cur == len(proxies):
            proxy_cur = 0
            proxy_rotations += 1
            if proxy_rotations >= proxy_rotations_old + 2:
                print "No working proxies anymore, reread file with proxies and reset status"
                proxy_cur = 0                
                proxy_rotations = 1
                readProxyList()
                rotateProxy(failed=False)                
                
        if proxies[proxy_cur]["failed"] > 1:
            print "Proxy ", proxies[proxy_cur]["proxy"], " failed - no more use it"
            continue
        else:
            proxy = { 'https': proxies[proxy_cur]["proxy"] }
            break

    print "proxy rotated: ", proxies[proxy_cur]["proxy"]
    
    #if proxy_rotations % 5 == 0:
    #    readProxyList()

def readProxyList():
    global proxies
    
    pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,4})'
    regexpr = re.compile(pattern)
    
    proxies = []
    
    try:
        f = open("proxies.txt", "r")
        for line in f:
            try:
                ip, port = regexpr.match(line.strip("\n")).groups()
            except AttributeError:
                continue
            
            proxies.append({ "proxy": ip+':'+port, "failed": 0 })
            f.close()
            
    except exceptions.BaseException as e:
        pass
        
    print "# of proxies read: ", len(proxies)

def resetBrowser():
    global browser, browserMode
    print "Browser reset requested"
    if browserMode:
        del browser
        gc.collect()
        browser = webdriver.Firefox()
        print "Browser reset done"
    else:
        print "Operating mode doesn't mean using headless browser. Requst cancelled"
     
# globals for requestURL(...)
def requestURL(callPoint, url):
    global verboseMode, browserMode
    
    time.sleep(PARSING_SLEEP + random.randrange(-PARSING_SLEEP_RAND_RANGE,PARSING_SLEEP_RAND_RANGE,1))
    while True:
        try:
            if browserMode:
                if verboseMode:
                    print "Requesting html with headless browser"
                browser.get(url)
                rtext = browser.page_source
                rstatus_code = 200
                
            else:
                if verboseMode:
                    print "Requesting html with 'requests'"                
                r = requests.get(url, headers = headers, proxies = proxy, timeout = PROXY_TIMEOUT)
                rtext = r.text
                rstatus_code = r.status_code
                
            if rtext.find('Busy, try again (504)') != -1:
                if proxy:
                    print "proxy failed:  ", proxy['https']
                if verboseMode:
                    print callPoint, ': response: ', rstatus_code, ', "Busy, try again (504)" retrying connection in ', TIMEOUT_RETRY , ' sec.'
                time.sleep(TIMEOUT_RETRY + random.randrange(-TIMEOUT_RAND_RANGE,TIMEOUT_RAND_RANGE,1))
                resetBrowser()
                rotateProxy()
                continue
            elif rtext.find('<h1>Busy, try again (502)</h1>') != -1:
                if proxy:
                    print "proxy failed:  ", proxy['https']
                if verboseMode:
                    print callPoint, ': response: ', rstatus_code, ', "Busy, try again (502)" retrying connection in ', TIMEOUT_RETRY , ' sec.'
                time.sleep(TIMEOUT_RETRY + random.randrange(-TIMEOUT_RAND_RANGE,TIMEOUT_RAND_RANGE,1))
                resetBrowser()
                rotateProxy()
                continue
            elif rtext.find('<head><title>500 Internal Server Error</title></head>') != -1:
                print "Forum failed, need to take a timeout"
                if verboseMode:
                    print callPoint, ': response: ', rstatus_code, ', "500 Internal Server Error" retrying connection in ', TIMEOUT_RETRY , ' sec. dumped to error_page_500.dmp'
                f = open("error_page_500.dmp", "w")
                f.write(rtext.encode('utf-8'))
                f.close()
                time.sleep(TIMEOUT_RETRY + random.randrange(-TIMEOUT_RAND_RANGE,TIMEOUT_RAND_RANGE,1))
                resetBrowser()
                rotateProxy(failed=False)
                continue
            elif rtext.find('Sorry, SMF was unable to connect to the database') != -1:
                print "Forum failed, need to take a timeout"
                if verboseMode:
                    print callPoint, ': response: ', rstatus_code, ', "SMF was unable to connect to the database" retrying connection in ', TIMEOUT_RETRY , ' sec.'
                time.sleep(TIMEOUT_RETRY + random.randrange(-TIMEOUT_RAND_RANGE,TIMEOUT_RAND_RANGE,1))
                resetBrowser()
                rotateProxy(failed=False)
                continue
            elif rtext.find('<span class="cf-error-code">520</span>') != -1:
                print "Forum failed, need to take a timeout"
                if verboseMode:
                    print callPoint, ': response: ', rstatus_code, ', "520: Web server is returning an unknown error" retrying connection in ', TIMEOUT_RETRY , ' sec.'
                time.sleep(TIMEOUT_RETRY + random.randrange(-TIMEOUT_RAND_RANGE,TIMEOUT_RAND_RANGE,1))
                resetBrowser()
                rotateProxy(failed=False)
                continue            
            elif rtext.find('<span class="cf-error-code">522</span>') != -1:
                print "Forum failed, need to take a timeout"
                if verboseMode:
                    print callPoint, ': response: ', rstatus_code, ', "522: Connection timed out" retrying connection in ', TIMEOUT_RETRY , ' sec.'
                time.sleep(TIMEOUT_RETRY + random.randrange(-TIMEOUT_RAND_RANGE,TIMEOUT_RAND_RANGE,1))
                resetBrowser()
                rotateProxy(failed=False)
                continue 
            elif rstatus_code != 200:
                if proxy:
                    print "proxy failed:  ", proxy['https']
                if verboseMode:
                    print callPoint, ': response: ', rstatus_code, ', retrying connection in ', TIMEOUT_RETRY , ' sec.'
                time.sleep(TIMEOUT_RETRY + random.randrange(-TIMEOUT_RAND_RANGE,TIMEOUT_RAND_RANGE,1))
                resetBrowser()
                rotateProxy()
                continue
            else:
                break
        except exceptions.BaseException as e:
            if proxy:
                print "proxy failed:  ", proxy['https']
            if verboseMode:
                print 'Error:', e.__class__.__name__, ' retrying connection in ', TIMEOUT_RETRY , ' sec.'
                print callPoint, ': Exception:', e.message, ' retrying connection in ', TIMEOUT_RETRY , ' sec.'
            time.sleep(TIMEOUT_RETRY + random.randrange(-TIMEOUT_RAND_RANGE,TIMEOUT_RAND_RANGE,1))
            resetBrowser()
            rotateProxy()
    
    rotateProxy(failed=False)
    print "URL request success" 
    return rtext


def parseIcoList(url,headers,skipLines,treeIn,textIn,icoList):

    if treeIn == "":
        text = requestURL('parseIcoList', url)
        tree = html.fromstring(text)
    else:
        tree = treeIn
        text = textIn

    parserHtml = HTMLParser()

    try:
        table = tree.xpath('//table[@class = "bordercolor"]')[1]
        rows = table.xpath(".//tr")
    except Exception, e:
        print >> sys.stderr, "Exception parsing ICO list, url: ", url
        print >> sys.stderr, "Exception: %s (dumped to error_page.dmp" % str(e)
        f = open("error_page.dmp", "w")
        f.write(text.encode('utf-8'))
        f.close()
        raise

    tabLine = 0
    for row in rows:
        tabLine += 1
        if tabLine < skipLines:
            continue

        cols = row.xpath(".//td")

        # topic theme
        topic = cols[2].xpath('.//a')[0]
        theme = parserHtml.unescape(topic.xpath('descendant-or-self::text()')[0]).encode('utf-8')
        # topic URL
        topicUrl = cols[2].xpath('.//a/@href')[0]
        # topicID : https://bitcointalk.org/index.php?topic=654845.0 => 654845
        result = re.search(r'=\d+', topicUrl)
        topicID = result.group(0)[1:]

        # topic starter
        topicStarter = cols[3].xpath('.//a')[0]
        topicStarterName = parserHtml.unescape(topicStarter.xpath('descendant-or-self::text()')[0]).encode('utf-8')
        #topic starter URL
        topicStarterURL = cols[3].xpath('.//a/@href')[0]
        # replies
        replies = "".join(cols[4].xpath('text()')).strip()
        # views:
        views = "".join(cols[5].xpath('text()')).strip()

        icoList[topicID] = {"topicId"          : topicID,
                            "announce"         : theme,
                            "topicUrl"         : topicUrl,
                            "topicStarter"     : topicStarterName,
                            "topicStarterUrl"  : topicStarterURL,
                            "NumReplies"       : replies,
                            "NumViews"         : views,
                            "sourceJson"       : topicID+'.json',
                            "dateTimeParsing"  : "",
                            "DateTimeLastPost" : "" }


    return

# end of def parseIcoList

#####################################################

def parseTopicPages(topicID, firstLastOnly, topicPosts, starterUserNameAndUrl):

    # 'https://bitcointalk.org/index.php?topic=1541329.0'
    topicURL = urlTopicTemplate + str(topicID) + '.0'

    # count num of pages of topic
    time.sleep(PARSING_SLEEP)
    # tr = requests.get(topicURL, headers = headers, proxies = proxy)
    text = requestURL('parseTopicPages', topicURL)
    ttree = html.fromstring(text)

    tPages = ttree.xpath('//a[@class = "navPages"]')
    tTotalPages = tPageNum = 0
    for tPage in tPages:
        try:
            tPageNum = int( tPage.xpath('text()')[0].encode('utf-8') )
        except:
            pass

        if tTotalPages < tPageNum:
            tTotalPages = tPageNum

    # get first page of topic posts
    userNameAndUrl = {}
    parseTopicPagePosts(topicID, topicURL, headers, 1, ttree, text, topicPosts, userNameAndUrl)
    firstPageTopicPostsNum = len(topicPosts)
    starterUserNameAndUrl["topicStarterUrl"] = userNameAndUrl["topicStarterUrl"]
    starterUserNameAndUrl["topicStarter"]    = userNameAndUrl["topicStarter"]
    starterUserNameAndUrl["NumReplies"]      = 0

    if firstLastOnly == True:
        tCurrentPage = tTotalPages - 1
        if tCurrentPage != 0:
            tUrlTail = tCurrentPage*TOPICS_PER_PAGE
            tUrl = urlTopicTemplate + str(topicID) + '.' + str(tUrlTail)
            parseTopicPagePosts(topicID, tUrl, headers, 1, '', '', topicPosts, userNameAndUrl)
            starterUserNameAndUrl["NumReplies"] = ( tTotalPages - 2) * TOPICS_PER_PAGE + len(topicPosts)
        else:
            starterUserNameAndUrl["NumReplies"] = len(topicPosts)
    else:
        tCurrentPage = 1
        while True:

            if tCurrentPage >= tTotalPages:
                break

            tUrlTail = tCurrentPage*TOPICS_PER_PAGE
            tUrl = urlTopicTemplate + str(topicID) + '.' + str(tUrlTail)
            tCurrentPage += 1

            parseTopicPagePosts(topicID,tUrl,headers,1,'','',topicPosts, userNameAndUrl)

            percent = 100.0 * tCurrentPage / tTotalPages
            print "Completed %3.1f%%" % percent

    return

# end of parseTopicPages

#####################################################

def parseTopicPagePosts(topicID, url, headers, skipLines, treeIn, textIn, topicPosts, firstPostUserNameAndUrl):

    if treeIn == "":
        dateTimeOfRequest = localtime()
        text = requestURL('parseTopicPagePosts', url)
        tree = html.fromstring(text)
    else:
        tree = treeIn
        text = textIn

    parserHtml = HTMLParser()

    try:
        table = tree.xpath('//table[@class = "bordercolor"]')[1]
    except Exception, e:
        print >> sys.stderr, "Exception parsing topic page posts, url: ", url
        print >> sys.stderr, "Exception: %s" % str(e)
        f = open("error_page.dmp", "w")
        f.write(text.encode('utf-8'))
        f.close()
        # "The topic or board you are looking for appears to be either missing or off limits to you."        
        raise

    # number of posts
    flagFirstPostUser = True
    rows = table.xpath('//td[@class = "windowbg" or @class = "windowbg2"]')

    for row in rows:
        anchors = row.xpath('.//td[@class = "poster_info"]/b/a')
        if len(anchors) == 0:
            # skipping
            continue
        else:
            anchor = anchors[0]
            postUserName = parserHtml.unescape(anchor.xpath('descendant-or-self::text()')[0]).encode('utf-8')
            postUserUrl  = anchor.xpath('@href')[0]
            if flagFirstPostUser:
                flagFirstPostUser = False
                firstPostUserNameAndUrl["topicStarter"] = postUserName
                firstPostUserNameAndUrl["topicStarterUrl"]  = postUserUrl

            #f = furl(postUserUrl)
            #postUserId = f.args["u"]

            postHeadA = row.xpath('.//td[@class = "td_headerandpost"]//div[@class = "subject"]/a')[0]
            postHead = parserHtml.unescape(postHeadA.xpath('descendant-or-self::text()')[0]).encode('utf-8')
            postHeadUrl = postHeadA.xpath('@href')[0]
            # https://tproger.ru/translations/regular-expression-python/
            result  = re.search(r'#msg\d+', postHeadUrl)
            postID = result.group(0)[4:]

            postDateList  = row.xpath('.//td[@class = "td_headerandpost"]//div[@class = "smalltext"]/text()')
            if len(postDateList) == 0:
                # use 'span' search if 'div' search is unsuccessful (cases of editing the posts)
                postDateList  = row.xpath('.//td[@class = "td_headerandpost"]//span[@class = "edited"]/text()')
                postDate = postDateList[0]
            else:
                postDate = postDateList[0]

            postText = " ".join(row.xpath('.//td[@class = "td_headerandpost"]//div[@class = "post"]/text()')).strip()
            postText = parserHtml.unescape(postText).encode('utf-8')

            if postUserName == postDate == postText:
                #skipping
                continue
            else:
                # topicPosts[postID] = [topicID, postUserName, postDate, postText]
                # remove spaces and check if post text is deleted by author
                postText = ' '.join(x for x in postText.split() if x)
                # if yes then insert '<deleted>' for correct work of classifier
                if len(postText) == 0:
                    postText = '<deleted>'

                if postDate[0:4] == ' at ':
                    postDate = strftime("%B %d, %Y, ", dateTimeOfRequest) + postDate[4:]

                topicPosts[postID] = { "topicId" : topicID,
                                       "user"    : postUserName,
                                       "date"    : postDate,
                                       "text"    : postText }

    return

# end of parseTopicPagePosts

#####################################################

try:
    f = open('lockBttParsing.txt', 'w')
except:
    print('Another process is working. Exiting.')
    sys.exit(1)


# default values:
# read from page 1
currentPage = 1
lastPage = 0
# default data dir path
dataDirPath = DATA_FILES_DIR

onlyOneTopicId = "0"

# read command line params if specified
try:
    opts, args = getopt.getopt(sys.argv[1:], "s:n:t:d:vb")
    for optName, optValue in opts:
        if optName == '-s':
            currentPage = int(optValue)
        elif optName == '-n':
            lastPage = int(optValue)
        elif optName == '-t':
            onlyOneTopicId  = optValue
        elif optName == '-d':
            dataDirPath = optValue
        elif optName == '-v':
            verboseMode = True
        elif optName == '-b':
            print "Using headless browser mode"
            browserMode = True      

except getopt.GetoptError as e:
    print sys.argv[0], ' [-s <start page>] [-n <num pages>] [-t <topic id>] [-d <datadir>] [-v (switch verbose mode on)] [-b (use headless firefox)]'
    sys.exit(1)


readProxyList()
rotateProxy(failed=False)

# count num of pages
# r = requests.get(urlStart, headers = headers, proxies = proxy)
text = requestURL('countNumOfPages', urlStart)
tree = html.fromstring(text)

pages = tree.xpath('//a[@class = "navPages"]')
maxPages = 0
for page in pages:
    try:
        pageNum  = int( page.xpath('text()')[0].encode('utf-8') )
    except:
        pass

    if maxPages < pageNum:
        maxPages = pageNum

if lastPage > maxPages:
    lastPage = maxPages
elif lastPage == 0:
    lastPage = maxPages

# parsing ICO list:
print "Parsing ICO announcements topics list"

print "Parsing topics from page ", currentPage, " to page ", lastPage
icoList = {}

while True:
    if currentPage > lastPage:
        break

    if currentPage % 10 == TIMEOUT_NUM:
        time.sleep(TIMEOUT_SLEEP)

    urlTail = (currentPage-1)*40
    url = urlTemplate + str(urlTail)

    if currentPage == 1:
        # get first page ICO list
        # reuse html tree from step "count num of pages"
        parseIcoList('',headers,6,tree,text,icoList)
    else:
        parseIcoList(url,headers,1,'','',icoList)
        #icoList.update(newIcoList)

    percent = 100.0 * currentPage / lastPage
    print "Completed %3.1f%%" % percent

    currentPage += 1

print "Parsing ICO posts"

# http://www.developersite.org/102-103188-python
# http://jsonviewer.stack.hu/

# read old announceList
icoListOld = {}

try:
    with open(dataDirPath + 'announceList.json', 'r') as oldAnnList:
        icoListOld = json.load(oldAnnList)
except:
    icoListOld = {}

#del icoList
#icoList = {}

# read assetList.json to append ico announcement topics of BTT
try:
    with open(dataDirPath + 'assetList.json', 'r') as fAssetList:
        assetList = json.load(fAssetList)
    fAssetList.close
    print "  adding assets from assetList.json items", len(assetList), "to topics list"
except:
    assetList = {}

itemsBeforeAdding = len(icoList)
# append topics from assetList to icoList:
for asset in assetList:
    for link in assetList[asset]["links"]:
        if link["linkType"] == "Announcement" and \
           link["linkUrl"].find('bitcointalk.org') != -1 and \
           assetList[asset]["rank"] < TOP_CMC_ITEMS:

            print "  adding", asset 
            if link["linkUrl"][-2:] == '.0':
                try:
                    bttTopicIdUni = re.search('topic=(.+?)\.0', link["linkUrl"]).group(1)
                    bttTopicId = bttTopicIdUni.encode('ascii','ignore')
                except:
                    print "Asset (", asset, ") : cannot retrieve topic id from URL:", link["linkUrl"]
                    continue
            else:
                f = furl.furl(link["linkUrl"])
                try:
                    bttTopicIdUni = f.args["topic"]
                    bttTopicId = bttTopicIdUni.encode('ascii','ignore')
                except:
                    print "Asset (", asset, ") : cannot retrieve topic id from URL:", link["linkUrl"]
                    continue

            if bttTopicId not in icoList.keys():

                if bttTopicId in icoListOld.keys():

                    icoList[bttTopicId] = icoListOld[bttTopicId].copy()

                else:
                    assetTopicPosts = {}
                    starterUserNameAndUrl = {}
                    parseTopicPages(bttTopicId, FIRST_LAST_ONLY, assetTopicPosts, starterUserNameAndUrl)

                    # set "DateTimeLastPost" equal to the last comment date and time
                    maxParsedDateTime = ''
                    for post in assetTopicPosts:
                        parsedDateTime = datetime.strptime(assetTopicPosts[post]["date"], '%B %d, %Y, %I:%M:%S %p').strftime("%Y-%m-%d %H:%M:%S")
                        if maxParsedDateTime < parsedDateTime:
                            maxParsedDateTime = parsedDateTime

                    icoList[bttTopicId] = { "DateTimeLastPost": maxParsedDateTime,
                                            "topicUrl"        : link["linkUrl"],
                                            "topicId"         : post,
                                            "sourceJson"      : post + '.json',
                                            "NumViews"        : "0",
                                            "announce"        : asset,
                                            "topicStarterUrl" : starterUserNameAndUrl["topicStarterUrl"],
                                            "topicStarter"    : starterUserNameAndUrl["topicStarter"],
                                            "NumReplies"      : starterUserNameAndUrl["NumReplies"] }

                    del assetTopicPosts

print "Number of items was added:", len(icoList) - itemsBeforeAdding

# print icoList
# sys.exit(1)

# reparse changed ICOs with saving all files on each iteration
# because of possible script crash or btt start blocking access
# we will update to announceList.json only what has been successfully parsed
# and saved to corresponding <topicId>.json
# but interim post data is dumped to <topicId>.json each PARSED_PAGES_SAVE_POSTS pages
icoListNum = len(icoList)
icoListCurr = 1
userNameAndUrl = {}
for ico in icoList:
    # process only one topic if specified in command line
    if onlyOneTopicId != "0" and onlyOneTopicId != ico:
        continue

    # icoList[ico]["NumReplies"]  vs  count rows in json
    # read all <topicId>.json if exits
    # so we proceed to parse topic pages staring from last <topicId>.json dump
    try:
        with open(dataDirPath + ico + '.json', 'r') as fTopicPosts:
            topicPosts = json.load(fTopicPosts)
        fTopicPosts.close
    except:
        topicPosts = {}

    numRepliesOld = len(topicPosts)

    try:
        numRepliesNew = int( icoList[ico]["NumReplies"] )
    except:
        numRepliesNew = 0

    if numRepliesNew == numRepliesOld:
        print "For topic ", ico ," no changes"
        percent = 100.0 * icoListCurr / icoListNum
        print "ICO list parsing completion %3.1f%%" % percent, "(", icoListCurr, " of ", icoListNum, ")"
        icoListCurr += 1
        continue

    numPagesOld = int(math.ceil( numRepliesOld / TOPICS_PER_PAGE ))
    numPagesNew = int(math.ceil( numRepliesNew / TOPICS_PER_PAGE ))

    if numPagesOld > numPagesNew: 
        numPagesOld = numPagesNew

    print "For", icoList[ico]["announce"], "(", ico, ")" ," need to parse pages from", numPagesOld+1, ' to ', numPagesNew+1

    topicParsingDT = strftime("%Y-%m-%d %H:%M", localtime())
    icoChangedPagesNum = numPagesNew - numPagesOld + 1
    icoChangedPagesCurr = 0
    for icoTopicPage in range(numPagesOld, numPagesNew+1):    
        tUrlTail = icoTopicPage*TOPICS_PER_PAGE
        tUrl = urlTopicTemplate + ico + '.' + str(tUrlTail)
        parseTopicPagePosts(ico, tUrl, headers, 1, '', '', topicPosts, userNameAndUrl)
        icoChangedPagesCurr += 1

        # save posts each PARSED_PAGES_SAVE_POSTS pages
        postsSavedFlag = ""
        if icoChangedPagesCurr % PARSED_PAGES_SAVE_POSTS == 0:
            with open(dataDirPath + ico + '.json', 'w') as fTopicPosts:
                json.dump(topicPosts, fTopicPosts, sort_keys=True, indent=4)
            fTopicPosts.close
            postsSavedFlag = " (dumped to disk)"

        # print progress info  
        percent = 100.0 * icoChangedPagesCurr / icoChangedPagesNum
        print "  topic ", ico, " parsing completion %3.1f%%" % percent, postsSavedFlag

    with open(dataDirPath + ico + '.json', 'w') as fTopicPosts:
        json.dump(topicPosts, fTopicPosts, sort_keys=True, indent=4)
    fTopicPosts.close

    # update old announce list
    icoListOld[ico] = icoList[ico]
    icoListOld[ico]["dateTimeParsing"] = topicParsingDT
    # set last comment date
    maxParsedDateTime = ''
    for post in topicPosts:
        parsedDateTime = datetime.strptime(topicPosts[post]["date"], '%B %d, %Y, %I:%M:%S %p').strftime("%Y-%m-%d %H:%M:%S")
        if maxParsedDateTime < parsedDateTime:
            maxParsedDateTime = parsedDateTime

    icoListOld[ico]["DateTimeLastPost"] = maxParsedDateTime

    with open(dataDirPath + 'announceList.json', 'w') as fAnnounceList: 
        json.dump(icoListOld, fAnnounceList, indent=4)
    fAnnounceList.close

    percent = 100.0 * icoListCurr / icoListNum
    print "ICO list parsing completion %3.1f%%" % percent, "(", icoListCurr, " of ", icoListNum, ")"
    icoListCurr += 1


#with open('announceListCurrent.json', 'w') as fp:
    #json.dump(icoList, fp)
    #json.dump(icoList, fp, sort_keys=True, indent=4)
    #json.dump(icoList, fp, indent=4)

#with open('announceList.json', 'r') as fp:
#  dataNew = json.load(fp)

