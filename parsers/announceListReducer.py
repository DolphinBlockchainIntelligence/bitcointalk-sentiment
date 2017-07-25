import getopt
import sys
import os
import re
import json
import furl

# const
DATA_FILES_DIR = "../data/"
TOP_CMC_ITEMS  = 1000
REPLIES_THRESHOLD = 40 # at least one page of btt

# vars
announceListOutputFilename = 'announceListNew.json'
dataDirPath = DATA_FILES_DIR
sentimDataDirPath = DATA_FILES_DIR

try:
    opts, args = getopt.getopt(sys.argv[1:], "o:d:")
    for optName, optValue in opts:
        if optName == '-o':
            announceListOutputFilename = optValue
        elif optName == '-d':
            dataDirPath = optValue
            
except getopt.GetoptError as e:
    print sys.argv[0], ' -o <announce list json output filename> [-d <data/dir/>]'
    print "default data dir is ", DATA_FILES_DIR
    sys.exit(1)

print dataDirPath

# read input announceList.json
try:
    with open(dataDirPath + 'announceList.json', 'r') as fAnnList:
        announceListInput = json.load(fAnnList)
    fAnnList.close()
    print "  Number of assets from announceList.json items:", len(announceListInput)
except:
    announceListInput = {}

# filter out items in announceListInput with a few replies
announcesBeforeProcessingNum = len(announceListInput)
for announce in announceListInput.keys():
    numReplies = int(announceListInput[announce]["NumReplies"])
    if numReplies < REPLIES_THRESHOLD:
        del announceListInput[announce]
print "Announce list reduced from", announcesBeforeProcessingNum, \
      "to", len(announceListInput), "items according to 'min replies' rule"

# and no data files
announcesBeforeProcessingNum = len(announceListInput)
jsonFiles = [f for f in os.listdir(dataDirPath) if re.match('[0-9]*\.json', f)]
for announce in announceListInput.keys():
    fileName = announceListInput[announce]["topicId"] + '.json'
    if fileName not in jsonFiles:
        # print ' announce deleted (no data file): ', announceListInput[announce]["topicId"] #, announceListInput[announce]["announce"]
        del announceListInput[announce]

print "Announce list reduced from", announcesBeforeProcessingNum, "to", len(announceListInput), "items according to 'no posts file' rule"

# compare announceListInput with assetList
# and replace "announce" with asset name
# read assetList.json
try:
    with open(dataDirPath + 'assetsList.json', 'r') as fAssetList:
        assetList = json.load(fAssetList)
    fAssetList.close()
    print "  Number of assets from assetsList.json items:", len(assetList)
except:
    assetList = {}

print "assets in mind:", len(assetList)
announcesRenamed = 0
for asset in assetList:
    for link in assetList[asset]["links"]:
        if link["linkType"] == "Announcement" and \
           link["linkUrl"].find('bitcointalk.org') != -1 and \
           assetList[asset]["rank"] < TOP_CMC_ITEMS:

            if link["linkUrl"][-2:] == '.0':
                try:
                    bttTopicId = re.search('topic=(.+?)\.0', link["linkUrl"]).group(1).encode('ascii','ignore')
                except:
                    print "Asset (", asset, ") : cannot retrieve topic id from URL:", link["linkUrl"]
                    continue
            else:
                f = furl.furl(link["linkUrl"])
                try:
                    bttTopicId = f.args["topic"].encode('ascii','ignore')
                except:
                    print "Asset (", asset, ") : cannot retrieve topic id from URL:", link["linkUrl"]
                    continue

            if bttTopicId in announceListInput.keys():                
                announceListInput[bttTopicId]["announce"] = asset
                announceListInput[bttTopicId]["rank"] = assetList[asset]["rank"]
                announceListInput[bttTopicId]["cmcUrl"] = assetList[asset]["cmcUrl"]
                announcesRenamed += 1
            else:
                print "Asset (", asset, ") : not found in announce list"

print announcesRenamed, "announces renamed as in CMC"

if len(announceListInput) != 0:
    with open(announceListOutputFilename, 'w') as fAnnounceListOutput:
        json.dump(announceListInput, fAnnounceListOutput, sort_keys=True, indent=4)
    fAnnounceListOutput.close
else:
    print "no topics remains"
