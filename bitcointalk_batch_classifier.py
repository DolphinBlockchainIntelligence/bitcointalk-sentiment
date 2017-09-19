import getopt
import sys
import bitcointalk_sentiment_classifier
import json
import datetime
import os
import warnings


def main(argv):
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    input_folder = ''
    model_file_objectivity = ''
    model_file_polarity = ''
    output_folder = ''
    output_posts = ''
    announce_json = ''
    sentiment_json = ''
    host = '127.0.0.1'
    port = '1111'

    options = ['help',
               'input_folder=',
               'obj_model=',
               'pol_model=',
               'output_folder=',
               'announce_list=',
               'sentiment_list=',
               'posts_number=',
               'embeddings_host=',
               'embeddings_port=']

    help_string = 'bitcointalk_batch_classifier.py ' + ' '.join(options)

    try:
        opts, args = getopt.getopt(argv, "h", options)
    except getopt.GetoptError:
        print(help_string)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ['-h', '--help']:
            print(help_string)
            sys.exit()
        elif opt == '--input_folder':
            input_folder = arg
        elif opt == '--obj_model':
            model_file_objectivity = arg
        elif opt == '--pol_model':
            model_file_polarity = arg
        elif opt == '--announce_json':
            announce_json = arg
        elif opt == '--sentiment_json':
            sentiment_json = arg
        elif opt == '--posts_number':
            output_posts = arg
        elif opt == '--embeddings_host':
            host = arg
        elif opt == '--embeddings_port':
            port = arg

    batch_classify(input_folder,
                   model_file_objectivity,
                   model_file_polarity,
                   output_folder,
                   announce_json,
                   sentiment_json,
                   output_posts,
                   host,
                   port)


def batch_classify(input_folder,
                   model_file_objectivity,
                   model_file_polarity,
                   output_folder,
                   announce_json,
                   sentiment_json,
                   output_posts,
                   host,
                   port):

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
        bitcointalk_sentiment_classifier.classify(filename,
                                                  model_file_objectivity,
                                                  model_file_polarity,
                                                  output_folder,
                                                  output_posts,
                                                  host,
                                                  port)
        sentimentList[topicId] = {'dateTimeSentiment': currentTime.strftime('%Y.%m.%d %H:%M')}
        
        currTopic += 1
        if currTopic % 10 == 0:
            with open(sentiment_json, 'w') as f:
                json.dump(sentimentList, f)
            f.close()
        print("Processed {} topics of {}".format(currTopic, numTopics))
    
    with open(sentiment_json, 'w') as f:
        json.dump(sentimentList, f)
    f.close()

    fLockSentiment.close()

if __name__ == '__main__':
    main(sys.argv[1:])