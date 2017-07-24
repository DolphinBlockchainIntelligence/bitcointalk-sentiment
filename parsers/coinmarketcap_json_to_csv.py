import csv
import json
import datetime

eos_contract_address = '0xd0a6E6C54DbC68Db5db3A091B171A77407Ff7ccf'
eos_contract_file_name = 'txs_'+eos_contract_address+'.json'

cmcAssetsListFile = 'assetsList.json'

try:
    with open(cmcAssetsListFile, 'r') as fAssets:
        assets = json.load(fAssets)
        fAssets.close
except:
    assets = {}

# https://stackoverflow.com/questions/26944274/valueerror-dict-contains-fields-not-in-fieldnames
csvfile = open(cmcAssetsListFile+'.csv','wb')
writer = csv.writer(csvfile, delimiter = ';')

writer.writerow(["asset","rank", "cmcUrl", "linkType", "linkUrl"])

bttThreads = {}
for asset in assets:
    bttThreads[asset] = []
    for link in assets[asset]["links"]:
        if link["linkType"] not in ['Rank','Tags']:
            writer.writerow([ asset,
                              assets[asset]["rank"],
                              assets[asset]["cmcUrl"],
                              link["linkType"],
                              link["linkUrl"] ])
        if assets[asset]["rank"] < 1000 and link["linkType"] == 'Announcement' and link["linkUrl"].find('bitcointalk.org') != -1:
            # bttThreads.append( { asset : link["linkUrl"] } )
            bttThreads[asset].append({"btt":link["linkUrl"]})
            
csvfile.close()

with open('assetsListBtt.json', 'w') as fAssetsListBtt:
    json.dump(bttThreads, fAssetsListBtt, sort_keys=True, indent=4)
fAssetsListBtt.close