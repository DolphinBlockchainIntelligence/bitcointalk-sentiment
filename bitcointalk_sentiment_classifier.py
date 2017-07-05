import pandas as pd
from datetime import datetime
from datetime import timedelta
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
    output_posts = ''
    try:
        opts, args = getopt.getopt(argv, "hi:m:f:n:")
    except getopt.GetoptError:
        print('bitcointalk_sentiment_classifier.py -i <inputfile> -m <model> -f <output folder> -n <number of output posts [number|fraction|all]>')
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
        elif opt == '-n':
            output_posts = arg

    classify(input_file, model_file, output_folder, output_posts)


def transform_sentiment_dict(sentiment_dict):
    negative = []
    neutral = []
    positive = []

    sorted_dates = sorted(list(sentiment_dict.keys()))
    point_start = datetime.strptime(sorted_dates[0], '%Y-%m-%d').timestamp()
    dates_parsed = [datetime.strptime(date, '%Y-%m-%d') for date in sorted_dates]

    date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
    while date <= dates_parsed[-1]:
        if date in dates_parsed:
            negative.append(sentiment_dict[str(date.date())]['negative'])
            neutral.append(sentiment_dict[str(date.date())]['neutral'])
            positive.append(sentiment_dict[str(date.date())]['positive'])
        else:
            negative.append(0)
            neutral.append(0)
            positive.append(0)
        date += timedelta(days=1)

    new_dict = {'heading': '',
                'chart':
                    {'negative': negative,
                     'neutral': neutral,
                     'positive': positive},
                'pointStart': int(point_start*100)
                }

    return(new_dict)


def classify(input_file, model_file, output_folder, output_posts):

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

    topic_df['date'].apply(str)
    topic_df.sort_values(by='date', ascending=False, inplace=True)

    try:
        posts_count = int(output_posts)
        if posts_count > len(topic_df):
            print('The number in the argument is bigger than actual number of posts. Outputting all posts.')
            topic_df_slice = topic_df
        else:
            topic_df_slice = topic_df[0:posts_count]
    except:
        try:
            posts_count = float(output_posts)
            if posts_count > 1:
                print('The fraction in the argument is bigger than 1. Outputting all posts.')
                topic_df_slice = topic_df
            else:
                topic_df_slice = topic_df[0:int(posts_count*len(topic_df))]
        except:
            topic_df_slice = topic_df
            if output_posts != 'all':
                print('Invalid number of posts value. Outputting all posts.')



    with open('{}\S{}.json'.format(output_folder, topic_name), 'w') as f:
        json.dump(transform_sentiment_dict(json_sentiment), f, ensure_ascii=False)
    print('Saved sentiment counts to {}\S{}.json'.format(output_folder, topic_name))

    with open('{}\D{}.json'.format(output_folder, topic_name), 'w') as f:
        topic_df_slice.to_json(f, orient='index')
    print('Saved posts with sentiments to {}\D{}.json'.format(output_folder, topic_name))

if __name__ == "__main__":
   main(sys.argv[1:])