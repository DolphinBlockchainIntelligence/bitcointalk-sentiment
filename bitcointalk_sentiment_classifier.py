import json
import getopt
import sys
import requests
import warnings
import os
from datetime import datetime
from datetime import timedelta
import pandas as pd
import tensorflow as tf
import numpy as np

def main(argv):
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    input_file = ''
    model_file_objectivity = ''
    model_file_polarity = ''
    output_folder = ''
    output_posts = ''
    host = '127.0.0.1'
    port = '1111'

    options = ['help',
               'inputfile=',
               'obj_model=',
               'pol_model=',
               'output_folder=',
               'posts_number=',
               'embeddings_host=',
               'embeddings_port=']

    help_string = 'bitcointalk_sentiment_classifier.py ' + ' '.join(options)

    try:
        opts, args = getopt.getopt(argv, "h", options)
    except getopt.GetoptError:
        print(help_string)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ['h', '--help']:
            print(help_string)
            sys.exit()
        elif opt == '--inputfile':
            input_file = arg
        elif opt == '--obj_model':
            model_file_objectivity = arg
        elif opt == '--pol_model':
            model_file_polarity = arg
        elif opt == '--output_folder':
            output_folder = arg
        elif opt == '--posts_number':
            output_posts = arg
        elif opt == '--embeddings_host':
            host = arg
        elif opt == '--embeddings_port':
            port = arg

    classify(input_file, model_file_objectivity, model_file_polarity, output_folder, output_posts, host, port)


def get_word_vectors(host, port, texts):
    texts.index = texts.index.astype(str)
    request = json.dumps(texts.to_dict())
    url = 'http://{}:{}/transform'.format(host, port)
    r = requests.post(url, json=request)

    if r.status_code != 200:
        print("Embedding Server Error:")
        print(r.text)
        sys.exit()

    response = json.loads(r.text)

    idx = np.array(list(response.keys()))
    sequences = np.array(list(response.values()))

    return idx, sequences


def load_model(filename):
    print(filename)
    graph = tf.Graph()
    with graph.as_default():

        saver = tf.train.import_meta_graph(filename, clear_devices=True)
        sess = tf.Session()
        saver.restore(sess, tf.train.latest_checkpoint(os.path.split(filename)[0]))

        data = graph.get_tensor_by_name('data:0')
        labels = graph.get_tensor_by_name('labels:0')

        prediction = graph.get_tensor_by_name('prediction:0')

    return graph, sess, data, labels, prediction


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


def classify(input_file, model_file_objectivity, model_file_polarity, output_folder, output_posts, host, port):

    topic_df = pd.read_json(input_file, orient='index', convert_dates=False)

    indexes, sequences = get_word_vectors(host, port, topic_df['text'])

    graph_objectivity, sess_objectivity, data_objectivity, labels_objectivity, prediction_objectivity = load_model(model_file_objectivity)

    with graph_objectivity.as_default():
        objectivity_predictions = np.argmax(sess_objectivity.run(prediction_objectivity,
                                                                {data_objectivity: sequences}), 1)
    idx_subjective = np.where(objectivity_predictions == 0)[0]

    sess_objectivity.close()

    graph_polarity, sess_polarity, data_polarity, labels_polarity, prediction_polarity = load_model(model_file_polarity)

    with graph_polarity.as_default():
        polarity_predictions = 2*np.argmax(sess_polarity.run(prediction_polarity,
                                                          {data_polarity: sequences[idx_subjective]}), 1)

    objectivity_predictions[idx_subjective] = polarity_predictions

    topic_df['Sentiment'] = objectivity_predictions

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

    _, topic_name = os.path.split(input_file)
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


    file_name = os.path.join(output_folder, 'S{}.json'.format(topic_name))
    with open(file_name, 'w') as f:
        json.dump(transform_sentiment_dict(json_sentiment), f, ensure_ascii=False)
    print('Saved sentiment counts to {}'.format(file_name))
    f.close()
    
    file_name = os.path.join(output_folder, 'D{}.json'.format(topic_name))
    with open(file_name, 'w') as f:
        topic_df_slice.to_json(f, orient='index')
    print('Saved posts with sentiments to {}'.format(file_name))
    f.close()

if __name__ == "__main__":
   main(sys.argv[1:])