import pandas as pd
from datetime import datetime
import json
import getopt
import sys
import pickle

def main(argv):
    input_file = ''
    model_file = ''
    vectorizer_file = ''
    output_folder = ''
    try:
        opts, args = getopt.getopt(argv, "hi:m:v:f:")
    except getopt.GetoptError:
        print('bitcointalk_sentiment_classifier.py -i <inputfile> -m <model> -v <vectorizer> -f <output folder>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('bitcointalk_sentiment_classifier.py -i <inputfile> -m <model> -v <vectorizer> -f <output folder>')
            sys.exit()
        elif opt == '-i':
            input_file = arg
        elif opt == '-m':
            model_file = arg
        elif opt == '-v':
            vectorizer_file = arg
        elif opt == '-f':
            output_folder = arg

    classify(input_file,model_file,vectorizer_file,output_folder)

def classify(input_file,model_file,vectorizer_file,output_folder):

    topic_df = pd.read_json(input_file,orient='index')
    with open(model_file,'rb') as file:
        model = pickle.load(file)
    with open(vectorizer_file,'rb') as file:
        tfidf = pickle.load(file)


    topic_matrix = tfidf.transform(topic_df[3])
    topic_df['Sentiment'] = model.predict_proba(topic_matrix)[:,1]
    topic_df['Sentiment'] = topic_df['Sentiment'].apply(lambda x: 0 if x<0.33 else (1 if x<0.66 else 2))

    def checkTimeFormat(time_string):
        try:
            datetime.strptime(time_string,'%B %d, %Y, %I:%M:%S %p')
            return True
        except ValueError:
            return False

    topic_df = topic_df[topic_df[2].apply(lambda x: checkTimeFormat(x))]
    topic_df[2] = topic_df[2].apply(lambda x: datetime.strptime(x,'%B %d, %Y, %I:%M:%S %p').date())
    topic_df.rename(columns={2: 'Date'},inplace=True)
    day_groups = topic_df.groupby(['Date'])

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

    with open('{}\{}_sentiment_{}.json'.format(output_folder,topic_name,str(datetime.now().date())),'w') as f:
        json.dump(json_sentiment,f,sort_keys=True,ensure_ascii=False)
    print('Saved to {}\{}_sentiment_{}.json'.format(output_folder,topic_name,str(datetime.now().date())))

if __name__ == "__main__":
   main(sys.argv[1:])