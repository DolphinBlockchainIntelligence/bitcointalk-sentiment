import json
import getopt
import sys
from matplotlib import pyplot as plt
import numpy as np


def main(argv):
    input_file = ''
    save_to = ''
    try:
        opts, args = getopt.getopt(argv, "hi:o:")
    except getopt.GetoptError:
        print('graph_builder.py -i <JSON inputfile> -o <output image>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('graph_builder.py -i <JSON inputfile> -o <output image>')
            sys.exit()
        elif opt == '-i':
            input_file = arg
        elif opt == '-o':
            save_to = arg

    build_graph(input_file,save_to)



def build_graph(input_file, save_to):

    with open(str(input_file),'r') as file:
        sentiment_dict = json.load(file)

    dates = []
    positives = []
    neutral = []
    negatives = []

    for date in sentiment_dict.keys():
        dates.append(date)
        positives.append(sentiment_dict[date]['positive'])
        neutral.append(sentiment_dict[date]['neutral'])
        negatives.append(sentiment_dict[date]['negative'])

    ind = np.arange(len(dates))
    plt.figure(figsize=(len(dates)/4, 5))
    p1 = plt.bar(ind, negatives, color='red')
    p2 = plt.bar(ind, neutral, bottom=negatives, color='yellow')
    p3 = plt.bar(ind, positives, bottom=[a + b for a, b in zip(neutral, negatives)], color='green')

    plt.ylabel('Number of posts')
    plt.xlabel('Day')
    plt.title('Sentiment')
    plt.xticks(ind, dates, rotation='vertical',fontsize='x-small')
    plt.legend((p1[0], p2[0], p3[0]), ('Negative', 'Neutral', 'Positive'))
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    if save_to != '':
        plt.savefig(save_to, bbox_inches='tight')

    plt.show()



if __name__ == "__main__":
   main(sys.argv[1:])