import getopt
import sys
import os
import bitcointalk_sentiment_classifier
import json
import datetime

def main(argv):
    input_folder = ''
    model_file = ''
    output_folder = ''
    try:
        opts, args = getopt.getopt(argv, "hi:m:f:")
    except getopt.GetoptError:
        print('bitcointalk_batch_classifier.py -i <input folder> -m <model> -f <output folder>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('bitcointalk_batch_classifier.py -i <input folder> -m <model> -f <output folder>')
            sys.exit()
        elif opt == '-i':
            input_folder = arg
        elif opt == '-m':
            model_file = arg
        elif opt == '-f':
            output_folder = arg

    batch_classify(input_folder,model_file,output_folder)


def batch_classify(input_folder,model_file,output_folder):

    try:
        f = open('lockSentiment.txt','w')
    except:
        print "Another process is working. Exiting."
        sys.exit(1)

    with open('announceList.json','r') as f:
        parsedList = json.load(f)
    with open('sentimentList.json','r') as f:
        sentimentList = json.load(f)

    toClassify = []

    for topicId in parsedList.keys():
        if topicId not in sentimentList.keys():
            toClassify.append(topicId)
        elif datetime.datetime.strptime(parsedList['topicId']['dateTimeParsing'],'%Y.%m.%d %H:%M') >= datetime.datetime.strptime(sentimentList['topicId']['dateTimeSentiment'],'%Y.%m.%d %H:%M'):
            toClassify.append(topicId)

    currentTime = datetime.datetime.now()

    for topicId in toClassify:
        filename = '{}\\{}.json'.format(input_folder, topicId)
        bitcointalk_sentiment_classifier.classify(filename, model_file, output_folder)
        sentimentList[topicId] = {'dateTimeSentiment': currentTime.strftime('%Y.%m.%d %H:%M')}

    with open('sentimentList.json','w') as f:
        json.dump(sentimentList,f)

if __name__ == '__main__':
    main(sys.argv[1:])