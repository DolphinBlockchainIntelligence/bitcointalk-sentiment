import pandas as pd


with open('plot.tok.gt9.5000') as f:
    obj_sentences = f.readlines()

with open('quote.tok.gt9.5000') as f:
    subj_sentences = f.readlines()

df_obj = pd.DataFrame(obj_sentences, columns=['Text'])
df_obj['Objectivity'] = 1

df_subj = pd.DataFrame(subj_sentences, columns=['Text'])
df_subj['Objectivity'] = 0

df = pd.concat([df_obj, df_subj])

print(df)

df.to_csv('objectivity.csv')