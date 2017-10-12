import pandas as pd
from nltk.tokenize import TweetTokenizer
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import KFold
from nltk.corpus import stopwords
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import FunctionTransformer
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
from scipy.sparse import csr_matrix
import re


def tokenize(text):
    tt = TweetTokenizer(preserve_case=False)
    tokens = tt.tokenize(text)
    ps = PorterStemmer()
    tokens = [ps.stem(token) for token in tokens]
    return tokens


df = pd.read_csv(r'objectivity.csv', index_col=0, encoding='windows-1251')
df['Text'] = df['Text'].apply(lambda x: str(x) + ' <smoothingplaceholder>')
df = df[df['Objectivity'].apply(lambda x: bool(re.match('[012]', str(x))))]
df = df.sample(frac=1)
print(len(df))

xgbc = XGBClassifier(n_estimators=500, max_depth=3, learning_rate=0.1, seed=512)
tt = TweetTokenizer(preserve_case=False)

tfidf = TfidfVectorizer(encoding='latin-1',
                        tokenizer=tt.tokenize,
                        stop_words=stopwords.words('english'),
                        ngram_range=(1, 3),
                        decode_error='ignore')

csc_transformer = FunctionTransformer(csr_matrix.tocsc, accept_sparse=True)

model = Pipeline([('vectorizer', tfidf), ('tocsc', csc_transformer), ('boosting', xgbc)])
kf = KFold(n_splits=4, shuffle=True, random_state=512)

for train_idx, test_idx in kf.split(df['Text'], df['Objectivity']):
    train_X = df['Text'].iloc[train_idx]
    test_X = df['Text'].iloc[test_idx]
    train_y = df['Objectivity'].iloc[train_idx]
    test_y = df['Objectivity'].iloc[test_idx]
    eval_set = [(test_X, test_y)]
    print('Training')
    model.fit(train_X, train_y)
    print('Prediction')
    pred = model.predict(test_X)
    print(accuracy_score(test_y, pred))