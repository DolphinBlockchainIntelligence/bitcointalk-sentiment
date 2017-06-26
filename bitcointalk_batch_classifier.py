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
    announce_json = ''
    sentiment_json = ''
    try:
<<<<<<< HEAD
        opts, args = getopt.getopt(argv, "hi:m:f:a:s:")
    except getopt.GetoptError:
        print('bitcointalk_batch_classifier.py -i <input folder> -m <model> -f <output folder> -a <announce JSON> -s <sentiment JSON>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('bitcointalk_batch_classifier.py -i <input folder> -m <model> -f <output folder> -a <announce JSON> -s <sentiment JSON>')
=======
        opts, args = getopt.getopt(argv, "hi:m:f:")
    except getopt.GetoptError:
        print('bitcointalk_batch_classifier.py -i <input folder> -m <model> -f <output folder>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('bitcointalk_batch_classifier.py -i <input folder> -m <model> -f <output folder>')
>>>>>>> 709e6fa35abd6dc8dc2ea8d5d29844febbbd04ef
            sys.exit()
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

<<<<<<< HEAD
    batch_classify(input_folder, model_file, output_folder, announce_json, sentiment_json)


def batch_classify(input_folder, model_file, output_folder, announce_json, sentiment_json):
=======
    batch_classify(input_folder,model_file,output_folder)


def batch_classify(input_folder,model_file,output_folder):
>>>>>>> 709e6fa35abd6dc8dc2ea8d5d29844febbbd04ef

    try:
        f = open('lockSentiment.txt','w')
    except:
        print "Another process is working. Exiting."
        sys.exit(1)

    with open(announce_json,'r') as f:
        parsedList = json.load(f)
    with open(sentiment_json,'r') as f:
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

    f.close()

if __name__ == '__main__':
    main(sys.argv[1:])