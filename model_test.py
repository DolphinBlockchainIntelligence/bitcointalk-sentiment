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
    try:
        opts, args = getopt.getopt(argv, "hi:m:v:")
    except getopt.GetoptError:
        print('bitcointalk_sentiment_classifier.py -i <inputfile> -m <model> -v <vectorizer>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('bitcointalk_sentiment_classifier.py -i <inputfile> -m <model> -v <vectorizer>')
            sys.exit()
        elif opt == '-i':
            input_file = arg
        elif opt == '-m':
            model_file = arg
        elif opt == '-v':
            vectorizer_file = arg


    classify(input_file,model_file,vectorizer_file)

def classify(input_file,model_file,vectorizer_file):

    topic_df = pd.read_json(input_file,orient='index')
    with open(model_file,'rb') as file:
        model = pickle.load(file)
    with open(vectorizer_file,'rb') as file:
        tfidf = pickle.load(file)


    topic_matrix = tfidf.transform(topic_df[3])
    topic_df['Sentiment'] = model.predict_proba(topic_matrix)[:,1]
    topic_df['Sentiment'] = topic_df['Sentiment'].apply(lambda x: 0 if x<0.33 else (1 if x<0.66 else 2))

    for index, row in topic_df[[3,'Sentiment']].sample(50).iterrows():
        print(row[3])
        print(row['Sentiment'])

if __name__ == "__main__":
   main(sys.argv[1:])