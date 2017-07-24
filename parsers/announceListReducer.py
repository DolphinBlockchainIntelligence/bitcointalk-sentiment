import getopt
import sys

# const
DATA_FILES_DIR = "../data/"

# vars
announceListInputPath = 'announceList.json'
announceListOutputPath = 'announceListNew.json'
dataDirPath = DATA_FILES_DIR

try:
    opts, args = getopt.getopt(sys.argv[1:], "d:o:")
    for optName, optValue in opts:
        if optName == '-r':
            announceListOutputPath = optValue
        elif optName == '-d':
            dataDirPath = optValue        

except getopt.GetoptError as e:
    print sys.argv[0], ' -o <announce list json output path> [-d <data dir/>]'
    sys.exit(1)


# read input announceList.json
try:
    with open(dataDirPath + 'announceList', 'r') as fAnnList:
        announceListInput = json.load(fAnnList)
    fAnnList.close()
    print "  Number of assets from assetList.json items:", len(announceListInput)
except:
    announceListInput = {}

'''
# read assetList.json
try:
    with open(dataDirPath + 'assetList.json', 'r') as fAssetList:
        assetList = json.load(fAssetList)
    fAssetList.close()
    print "  Number of assets from assetList.json items:", len(assetList)
except:
    assetList = {}
'''

icoListOutput = {}
for topic in icoListInput: