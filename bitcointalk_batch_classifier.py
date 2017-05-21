import getopt
import sys
import os
import bitcointalk_sentiment_classifier

def main(argv):
    input_folder = ''
    model_file = ''
    vectorizer_file = ''
    output_folder = ''
    try:
        opts, args = getopt.getopt(argv, "hi:m:v:f:")
    except getopt.GetoptError:
        print('bitcointalk_batch_classifier.py -i <input folder> -m <model> -v <vectorizer> -f <output folder>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('bitcointalk_batch_classifier.py -i <input folder> -m <model> -v <vectorizer> -f <output folder>')
            sys.exit()
        elif opt == '-i':
            input_folder = arg
        elif opt == '-m':
            model_file = arg
        elif opt == '-v':
            vectorizer_file = arg
        elif opt == '-f':
            output_folder = arg

    batch_classify(input_folder,model_file,vectorizer_file,output_folder)


def batch_classify(input_folder,model_file,vectorizer_file,output_folder):
    for root, dirs, files in os.walk(input_folder):
        for name in files:
            input_filename = input_folder + '\\' + name
            bitcointalk_sentiment_classifier.classify(input_filename,model_file,vectorizer_file,output_folder)


if __name__ == '__main__':
    main(sys.argv[1:])