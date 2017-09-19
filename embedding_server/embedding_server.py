from flask import Flask
from flask import request, abort, jsonify
import numpy as np
import gensim
import re
import string

app = Flask(__name__)

model = None
maxSeqLength = 70
numFeatures = 300


def get_tokens(s):
    return re.sub('[{}]'.format(string.punctuation), '', s).lower().split()

def get_sequence_matrix(tokens, maxSeqLength, numFeatures, model):
    matrix = []
    for i in range(maxSeqLength):
        if i < len(tokens) and tokens[i] in model:
            matrix.append(model[tokens[i]])
        else:
            pass
    matrix = np.array(matrix)
    if matrix.shape[0] == 0:
        matrix = np.zeros((maxSeqLength, numFeatures))
    elif matrix.shape[0] < maxSeqLength:
        matrix = np.concatenate((matrix, np.zeros((maxSeqLength - matrix.shape[0], numFeatures))))
    return matrix

@app.route("/init", methods=['POST'])
def init():
    global model
    try:
        model_path = request.form['filepath']
        is_binary = bool(request.form['is_binary'])
        model = gensim.models.KeyedVectors.load_word2vec_format(model_path, binary=is_binary)
    except PermissionError:
        abort(400, 'Could not load vectors - invalid path (%s)' % model_path)
    except Exception as e:
        abort(500, 'Internal server error: %s' % str(e))
    return 'OK'

@app.route("/check/<string:word>", methods=['GET'])
def check(word):
    if model is None:
        abort(500, 'Model is not initialized.')
    if word not in model:
        abort(500, 'Word was not found.')
    return jsonify({word: model[word].tolist()})

@app.route("/transform", methods=['POST'])
def transform():
    if model is None:
        abort(500, 'Model is not initialized.')
    global maxSeqLength
    global numFeatures
    global model
    response = {}
    for item in request.data['texts']:
        try:
            id = item
            vector_sequence = get_sequence_matrix(get_tokens(request.data['texts'][id]), maxSeqLength, numFeatures, model).tolist()
            response[id] = vector_sequence
        except KeyError as e:
            abort(400, 'Wrong JSON format, key %s' % e)
        except Exception as e:
            abort(500, 'Internal server error: %s' % str(e))
        return jsonify(response)
