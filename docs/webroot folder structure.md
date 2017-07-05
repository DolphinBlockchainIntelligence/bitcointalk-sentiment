# Web server root folder structure (beta.dolphin.bi)
* `webserver root`
    * `static`
        * `data`
            * announceList.json
            * sentimentList.json
            * `btt-sentiments`
                * S\{topic ID\}.json
                * D\{topic ID\}.json


# Files structure
## announceList.json
`Sample:`
```javascript
{
    "1571738": {
        "topicUrl": "https://bitcointalk.org/index.php?topic=1571738.0", 
        "topicId": "1571738", 
        "topicStarterUrl": "https://bitcointalk.org/index.php?action=profile;u=145226", 
        "sourceJson": "1571738.json", 
        "dateTimeParsing": "2017-06-25 22:48", 
        "announce": "[ANN][rICO]Antshares Blockchain Mainnet is ONLINE!", 
        "NumReplies": "6543", 
        "NumViews": "1023714", 
        "topicStarter": "dahongfei"
    }, 
    "1937519": {
        "topicUrl": "https://bitcointalk.org/index.php?topic=1937519.0", 
        "topicId": "1937519", 
        "NumReplies": "88", 
        "topicStarterUrl": "https://bitcointalk.org/index.php?action=profile;u=1014170", 
        "sourceJson": "1937519.json", 
        "announce": "[PRE-ANN] - Crypto Island - Let's buy a private island together", 
        "dateTimeParsing": "2017-06-20 02:04", 
        "NumViews": "2394", 
        "topicStarter": "CryptoIsland"
    }
}
```

## S\{topicId\}.json
> contains number of sentiments for each category (negative/neutral/positive) starting from date specified as a unix timestamp in attribute `pointStart`
`Sample:`
```javascript
{
 "heading": "The Project",
 "chart": {
  "negative": [6, 15, 12],
  "neutral": [7, 4, 9],
  "positive": [3, 1, 8]
 },
 "pointStart": 1456790400000
}
```

## D\{topicId\}.json
> "Sentiment" gets values: 0 - negative, 1 - neutral, 2 - positive
`Sample`
```javascript
{
   "10870994":{
      "date":"March 24, 2015, 02:00:02 PM",
      "text":"<deleted>",
      "topicId":1001407,
      "user":"ACP",
      "Sentiment":1
   },
   "10871073":{
      "date":"March 24, 2015, 02:09:13 PM",
      "text":"Really\u00a0 Looks like coingen shit...",
      "topicId":1001407,
      "user":"I_Like_Dogs",
      "Sentiment":0
   },
   "10871077":{
      "date":"March 24, 2015, 02:09:18 PM",
      "text":"Probably the next bitcoin",
      "topicId":1001407,
      "user":"ocminer",
      "Sentiment":2
   }
}
```