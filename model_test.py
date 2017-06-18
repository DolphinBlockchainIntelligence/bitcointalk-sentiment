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
        print('model_test.py -i <inputfile> -m <model> -v <vectorizer> -f <output folder>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('model_test.py -i <inputfile> -m <model> -v <vectorizer> -f <output folder>')
            sys.exit()
        elif opt == '-i':
            input_file = arg
        elif opt == '-m':
            model_file = arg
        elif opt == '-v':
            vectorizer_file = arg
        elif opt == '-f':
            output_folder = arg


    classify(input_file,model_file,vectorizer_file, output_folder)

def classify(input_file,model_file,vectorizer_file, output_folder):

    topic_df = pd.read_json(input_file,orient='index')
    with open(model_file,'rb') as file:
        model = pickle.load(file)
    with open(vectorizer_file,'rb') as file:
        tfidf = pickle.load(file)

    topic_matrix = tfidf.transform(topic_df[3])
    topic_df['Sentiment'] = model.predict_proba(topic_matrix)[:, 1]
    topic_df['Sentiment'] = topic_df['Sentiment'].apply(lambda x: 0 if x<0.33 else (1 if x<0.66 else 2))

    topic_name = input_file.split('\\')[1]
    topic_name = topic_name.split('.')[0]

    with open('{}\{}_sentiment_posts_{}.json'.format(output_folder, topic_name, str(datetime.now().date())), 'w') as f:
        topic_df.to_json(f, orient='index')


if __name__ == "__main__":
   main(sys.argv[1:])