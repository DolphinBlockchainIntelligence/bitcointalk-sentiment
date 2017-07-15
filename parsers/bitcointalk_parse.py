#reload(sys) sys.setdefaultencoding('utf-8')
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

headers = { 'User-Agent': 'Mozilla/6.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.1144' }
urlStart = 'https://bitcointalk.org/index.php?board=159.0'
urlTemplate = 'https://bitcointalk.org/index.php?board=159.'
urlTopicTemplate = 'https://bitcointalk.org/index.php?topic='

#####################################################
def parseIcoList(url,headers,skipLines,treeIn,icoList):

    if treeIn == "":
        time.sleep(PARSING_SLEEP)
        while True:
            try:
                r = requests.get(url, headers = headers)
                if r.text.find('Busy, try again (504)') != -1:
                    print 'Error: "Busy, try again (504)" retrying connection in ', TIMEOUT_RETRY , ' sec.'
                    time.sleep(TIMEOUT_RETRY)
                    continue
                else:
                    break   
            except exceptions.BaseException as e:
                # print 'Error:', exception.__class__.__name__, ' retrying connection in ', TIMEOUT_RETRY , ' sec.'
                print 'Error:', e.message, ' retrying connection in ', TIMEOUT_RETRY , ' sec.'
                time.sleep(TIMEOUT_RETRY)            
        
        tree = html.fromstring(r.text)
    else:
        tree = treeIn

    parserHtml = HTMLParser()

    table = tree.xpath('//table[@class = "bordercolor"]')[1]
    rows = table.xpath(".//tr")
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
    tr = requests.get(topicURL, headers = headers)
    ttree = html.fromstring(tr.text)

    tPages = ttree.xpath('//a[@class = "navPages"]')
    tTotalPages = 0
    for tPage in tPages:
        try:
            tPageNum = int( tPage.xpath('text()')[0].encode('utf-8') )
        except:
            pass

        if tTotalPages < tPageNum:
            tTotalPages = tPageNum

    # get first page of topic posts
    userNameAndUrl = {}
    parseTopicPagePosts(topicID, topicURL, headers, 1, ttree, topicPosts, userNameAndUrl)
    firstPageTopicPostsNum = len(topicPosts)
    starterUserNameAndUrl["topicStarterUrl"] = userNameAndUrl["topicStarterUrl"]
    starterUserNameAndUrl["topicStarter"]    = userNameAndUrl["topicStarter"]
    starterUserNameAndUrl["NumReplies"]      = 0
    
    if firstLastOnly == True:
        tCurrentPage = tTotalPages - 1
        if tCurrentPage != 0:
            tUrlTail = tCurrentPage*TOPICS_PER_PAGE
            tUrl = urlTopicTemplate + str(topicID) + '.' + str(tUrlTail)
            parseTopicPagePosts(topicID, tUrl, headers, 1, '', topicPosts, userNameAndUrl)
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

            parseTopicPagePosts(topicID,tUrl,headers,1,'',topicPosts, userNameAndUrl)

            percent = 100.0 * tCurrentPage / tTotalPages
            print "Completed %3.1f%%" % percent

    return

# end of parseTopicPages

#####################################################

def parseTopicPagePosts(topicID, url, headers, skipLines, treeIn, topicPosts, firstPostUserNameAndUrl):

    if treeIn == "":
        time.sleep(PARSING_SLEEP)
        #r = requests.get(url, headers = headers)
        while True:
            try:
                dateTimeOfRequest = localtime()
                r = requests.get(url, headers = headers)
                if r.text.find('Busy, try again (504)') != -1:
                    print 'Error: "Busy, try again (504)" retrying connection in ', TIMEOUT_RETRY , ' sec.'
                    time.sleep(TIMEOUT_RETRY)
                    continue
                else:
                    break
            except exceptions.BaseException as e:
                # print 'Error:', exception.__class__.__name__, ' retrying connection in ', TIMEOUT_RETRY , ' sec.'
                print 'Error:', e.message, ' retrying connection in ', TIMEOUT_RETRY , ' sec.'
                time.sleep(TIMEOUT_RETRY)

        tree = html.fromstring(r.text)
    else:
        tree = treeIn

    parserHtml = HTMLParser()

    try:
        table = tree.xpath('//table[@class = "bordercolor"]')[1]
    except Exception, e:
        print >> sys.stderr, "Exception parsing topic page posts, url: ", url
        print >> sys.stderr, "Exception: %s" % str(e)
        f = open("error_page.dmp", "w")
        f.write(r.text)
        f.close()
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

# count num of pages
r = requests.get(urlStart, headers = headers)
tree = html.fromstring(r.text)

pages = tree.xpath('//a[@class = "navPages"]')
totalPages = 0
for page in pages:
    try:
        pageNum  = int( page.xpath('text()')[0].encode('utf-8') )
    except:
        pass

    if totalPages < pageNum:
        totalPages = pageNum

print "Total pages: ", totalPages

# parsing ICO list:
print "Parsing ICO announcements topics list"

# default values:
# read from page 1 to totalPages
currentPage  = 1
# temporary limit number of pages
totalPages   = 1

onlyOneTopicId = "0"

# read command line params if specified
try:
    opts, args = getopt.getopt(sys.argv[1:], "s:n:t:")
    for optName, optValue in opts:
        if optName == '-s':
            currentPage  = int( optValue )
        elif optName == '-n':
            totalPages   = int( optValue )
        elif optName == '-t':
            onlyOneTopicId  = optValue

except getopt.GetoptError as e:
    print sys.argv[0], ' -s <start page> -n <num pages> [-t <topic id>]'
    sys.exit(1)

print "Parsing topics from page ", currentPage, " to page ", totalPages
icoList = {}

while True:
    if currentPage > totalPages:
        break

    if currentPage % 10 == TIMEOUT_NUM:
        time.sleep(TIMEOUT_SLEEP)

    urlTail = (currentPage-1)*40
    url = urlTemplate + str(urlTail)

    if currentPage == 1:
        # get first page ICO list
        # reuse html tree from step "count num of pages"
        parseIcoList('',headers,6,tree,icoList)
    else:
        parseIcoList(url,headers,1,'',icoList)
        #icoList.update(newIcoList)

    percent = 100.0 * currentPage / totalPages
    print "Completed %3.1f%%" % percent  

    currentPage += 1

print "Parsing ICO posts"

# http://www.developersite.org/102-103188-python
# http://jsonviewer.stack.hu/

# read old announceList
icoListOld = {}

try:
    with open(DATA_FILES_DIR + 'announceList.json', 'r') as oldAnnList:
        icoListOld = json.load(oldAnnList)
except:
    icoListOld = {}   

#del icoList
#icoList = {}

# read assetList.json to append ico announcement topics of BTT
try:
    with open(DATA_FILES_DIR + 'assetList.json', 'r') as fAssetList:
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
           assetList[asset]["rank"] < 100:
           
            print "  adding", asset 
            try:
                bttTopicIdUni = re.search('topic=(.+?)\.0', link["linkUrl"]).group(1)
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
        with open(DATA_FILES_DIR + ico + '.json', 'r') as fTopicPosts:
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
        parseTopicPagePosts(ico, tUrl, headers, 1, '', topicPosts, userNameAndUrl)
        icoChangedPagesCurr += 1

        # save posts each PARSED_PAGES_SAVE_POSTS pages
        postsSavedFlag = ""
        if icoChangedPagesCurr % PARSED_PAGES_SAVE_POSTS == 0:
            with open(DATA_FILES_DIR + ico + '.json', 'w') as fTopicPosts:
                json.dump(topicPosts, fTopicPosts, sort_keys=True, indent=4)
            fTopicPosts.close
            postsSavedFlag = " (dumped to disk)"

        # print progress info  
        percent = 100.0 * icoChangedPagesCurr / icoChangedPagesNum
        print "  topic ", ico, " parsing completion %3.1f%%" % percent, postsSavedFlag

    with open(DATA_FILES_DIR + ico + '.json', 'w') as fTopicPosts:
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

    with open(DATA_FILES_DIR + 'announceList.json', 'w') as fAnnounceList: 
        json.dump(icoListOld, fAnnounceList, indent=4)
    fAnnounceList.close

    icoListCurr += 1
    percent = 100.0 * icoListCurr / icoListNum
    print "ICO list parsing completion %3.1f%%" % percent, "(", icoListCurr, " of ", icoListNum, ")"


#with open('announceListCurrent.json', 'w') as fp:
    #json.dump(icoList, fp)
    #json.dump(icoList, fp, sort_keys=True, indent=4)
    #json.dump(icoList, fp, indent=4)

#with open('announceList.json', 'r') as fp:
#  dataNew = json.load(fp)

