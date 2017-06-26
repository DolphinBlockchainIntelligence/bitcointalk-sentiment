import pandas as pd
from datetime import datetime
import json
import getopt
import sys
import pickle
import warnings

def main(argv):
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    input_file = ''
    model_file = ''
    output_folder = ''
    try:
        opts, args = getopt.getopt(argv, "hi:m:f:")
    except getopt.GetoptError:
        print('bitcointalk_sentiment_classifier.py -i <inputfile> -m <model> -f <output folder>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('bitcointalk_sentiment_classifier.py -i <inputfile> -m <model> -f <output folder>')
            sys.exit()
        elif opt == '-i':
            input_file = arg
        elif opt == '-m':
            model_file = arg
        elif opt == '-f':
            output_folder = arg

    classify(input_file,model_file,output_folder)

def classify(input_file,model_file,output_folder):

    topic_df = pd.read_json(input_file, orient='index', convert_dates=False)

    with open(model_file, 'rb') as file:
        model = pickle.load(file)

    topic_df['smoothed_text'] = topic_df['text'].apply(lambda x: x + ' <smoothingplaceholder>')

    topic_df['Sentiment'] = model.predict(topic_df['smoothed_text'])

    topic_df.drop(labels=['smoothed_text'], axis=1, inplace=True)

    def checkTimeFormat(time_string):
        try:
            datetime.strptime(time_string,'%B %d, %Y, %I:%M:%S %p')
            return True
        except ValueError:
            return False

    topic_df['date'] = topic_df['date'].apply(str)
    topic_df = topic_df[topic_df['date'].apply(lambda x: checkTimeFormat(x))]
    topic_df['date'] = topic_df['date'].apply(lambda x: datetime.strptime(x,'%B %d, %Y, %I:%M:%S %p').date())
    day_groups = topic_df.groupby(['date'])

    dates = []
    positives = []
    neutral = []
    negatives = []

    for key, group in day_groups:
        dates.append(key)
        if 0 in group['Sentiment'].value_counts().index:
            negatives.append(group['Sentiment'].value_counts()[0])
        else:
            negatives.append(0)
        if 1 in group['Sentiment'].value_counts().index:
            neutral.append(group['Sentiment'].value_counts()[1])
        else:
            neutral.append(0)
        if 2 in group['Sentiment'].value_counts().index:
            positives.append(group['Sentiment'].value_counts()[2])
        else:
            positives.append(0)

    json_sentiment = {}

    for i in range(len(dates)):
        string_date = str(dates[i])
        json_sentiment[string_date] = {}
        json_sentiment[string_date]['positive'] = int(positives[i])
        json_sentiment[string_date]['neutral'] = int(neutral[i])
        json_sentiment[string_date]['negative'] = int(negatives[i])

    topic_name = input_file.split('\\')[1]
    topic_name = topic_name.split('.')[0]

    with open('{}\S{}.json'.format(output_folder, topic_name), 'w') as f:
        json.dump(json_sentiment, f, sort_keys=True, ensure_ascii=False)
    print('Saved sentiment counts to {}\S{}.json'.format(output_folder, topic_name))

    with open('{}\D{}.json'.format(output_folder, topic_name), 'w') as f:
        topic_df.to_json(f, orient='index')
    print('Saved posts with sentiments to {}\S{}.json'.format(output_folder, topic_name))

if __name__ == "__main__":
   main(sys.argv[1:])