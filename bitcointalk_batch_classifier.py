import getopt
import sys
import bitcointalk_sentiment_classifier
import json
import datetime
import os

def main(argv):
    input_folder = ''
    model_file = ''
    output_folder = ''
    announce_json = ''
    sentiment_json = ''
    output_posts = ''

    try:
        opts, args = getopt.getopt(argv, "hi:m:f:a:s:n:")
    except getopt.GetoptError:
        print('bitcointalk_batch_classifier.py -i <input folder> -m <model> -f <output folder> -a <announce JSON> -s <sentiment JSON> -n <number of output posts [number|fraction|all]>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('bitcointalk_batch_classifier.py -i <input folder> -m <model> -f <output folder> -a <announce JSON> -s <sentiment JSON> -n <number of output posts [number|fraction|all]>')
        elif opt == '-i':
            input_folder = arg
        elif opt == '-m':
            model_file = arg
        elif opt == '-f':
            output_folder = arg
        elif opt == '-a':
            announce_json = arg
        elif opt == '-s':
            sentiment_json = arg
        elif opt == '-n':
            output_posts = arg

    batch_classify(input_folder, model_file, output_folder, announce_json, sentiment_json, output_posts)


def batch_classify(input_folder, model_file, output_folder, announce_json, sentiment_json, output_posts):

    try:
        fLockSentiment = open('lockSentiment.txt', 'w')
    except:
        print('Another process is working. Exiting.')
        sys.exit(1)

    with open(announce_json, 'r') as f:
        parsedList = json.load(f)
    f.close()
    with open(sentiment_json, 'r') as f:
        sentimentList = json.load(f)
    f.close()

    toClassify = []

    for topicId in parsedList.keys():
        if topicId not in sentimentList.keys():
            toClassify.append(topicId)
        elif datetime.datetime.strptime(parsedList[topicId]['dateTimeParsing'], '%Y-%m-%d %H:%M') >=\
                datetime.datetime.strptime(sentimentList[topicId]['dateTimeSentiment'], '%Y.%m.%d %H:%M'):
            toClassify.append(topicId)

    currentTime = datetime.datetime.now()
    
    numTopics = len(toClassify)
    print("Topics to (re)process:{}".format(numTopics))
    currTopic = 0
    for topicId in toClassify:
        filename = os.path.join(input_folder, '{}.json'.format(topicId))
        bitcointalk_sentiment_classifier.classify(filename, model_file, output_folder, output_posts)
        sentimentList[topicId] = {'dateTimeSentiment': currentTime.strftime('%Y.%m.%d %H:%M')}
        
        currTopic += 1
        if currTopic % 10 == 0:
            with open(sentiment_json, 'w') as f:
                json.dump(sentimentList, f)
            f.close()
        print("Processed {} topics of {}".format(currTopic, numTopics))
    
    fLockSentiment.close()

if __name__ == '__main__':
    main(sys.argv[1:])