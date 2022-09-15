# -*- coding: utf-8 -*-
"""nlp_submission_dicoding

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1DaLjRoqdEr9xL_TMC1M9QOU63mOC4AwK

# Download Dataset
"""

# install kaggle package
!pip install -q kaggle

# upload kaggle.json
from google.colab import files
files.upload()

# check dataset list
! mkdir ~/.kaggle
! cp kaggle.json ~/.kaggle/
! chmod 600 ~/.kaggle/kaggle.json
! kaggle datasets list

# download dataset
!kaggle datasets download -d hgultekin/bbcnewsarchive

# unzip dataset
!mkdir bbcnewsarchive
!unzip bbcnewsarchive.zip -d bbcnewsarchive
!ls bbcnewsarchive

"""# Load Dataset"""

# libraries
import pandas as pd
import nltk, os, re, string
import tensorflow as tf

from tensorflow.keras.layers import Input, LSTM, Bidirectional, SpatialDropout1D, Dropout, Flatten, Dense, Embedding, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.preprocessing.text import Tokenizer, text_to_word_sequence
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical

from sklearn.model_selection import train_test_split

from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet as wn

nltk.download('wordnet')
nltk.download('stopwords')

# load dataset
df = pd.read_csv('bbcnewsarchive/bbc-news-data.csv', sep='\t')
df.head(10)

print(df.columns)
print(df.shape)
print(df.info())

# categories
df.category.value_counts()

# delete unused columns
df = df.drop(columns = ['filename'])
df.head(5)

"""# Cleansing Data"""

# lowercasing
df.title = df.title.apply(lambda x: x.lower())
df.content = df.content.apply(lambda x: x.lower())

# removing functuation
def cleaner(data):
    return(data.translate(str.maketrans('','', string.punctuation)))
    df.title = df.title.apply(lambda x: cleaner(x))
    df.content = df.content.apply(lambda x: lem(x))

# lematization
lemmatizer = WordNetLemmatizer()

def lem(data):
    pos_dict = {'N': wn.NOUN, 'V': wn.VERB, 'J': wn.ADJ, 'R': wn.ADV}
    return(' '.join([lemmatizer.lemmatize(w,pos_dict.get(t, wn.NOUN)) for w,t in nltk.pos_tag(data.split())]))
    df.title = df.title.apply(lambda x: lem(x))
    df.content = df.content.apply(lambda x: lem(x))

# removing number
def rem_numbers(data):
    return re.sub('[0-9]+','',data)
    df['title'].apply(rem_numbers)
    df['content'].apply(rem_numbers)

# removing stopword
st_words = stopwords.words()
def stopword(data):
    return(' '.join([w for w in data.split() if w not in st_words ]))
    df.title = df.title.apply(lambda x: stopword(x))
    df.content = df.content.apply(lambda x: lem(x))

# view data
df.head(10)

# one-hot-encoding
category = pd.get_dummies(df.category)
df = pd.concat([df, category], axis = 1)
df = df.drop(columns = 'category')
df.head(10)

# change value to numpy array
news = df['title'].values + '' + df['content'].values
label = df[['business', 'entertainment', 'politics', 'sport', 'tech']].values

# view label
label

# Split data
news_train, news_test, label_train, label_test = train_test_split(news, label, test_size=0.2, shuffle=True)

# tokenizer
 
tokenizer = Tokenizer(num_words=2000, oov_token='x', filters='!"#$%&()*+,-./:;<=>@[\]^_`{|}~ ')
tokenizer.fit_on_texts(news_train) 
tokenizer.fit_on_texts(news_test)
 
sekuens_train = tokenizer.texts_to_sequences(news_train)
sekuens_test = tokenizer.texts_to_sequences(news_test)
 
padded_train = pad_sequences(sekuens_train) 
padded_test = pad_sequences(sekuens_test)

# model
model = tf.keras.Sequential([
    tf.keras.layers.Embedding(input_dim=5000, output_dim=64),
    tf.keras.layers.LSTM(128),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(5, activation='softmax')
])
model.compile(optimizer='adam', metrics=['accuracy'], loss='categorical_crossentropy',)
model.summary()

# callback
class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('accuracy')>0.90 and logs.get('val_accuracy')>0.85):
      self.model.stop_training = True
      print("\nThe accuracy of the training set has reached > 90% and the validation set has reached > 85%!")
callbacks = myCallback()

# model fit
history = model.fit(padded_train, label_train, epochs = 30, 
                    validation_data = (padded_test, label_test), 
                    verbose = 1, callbacks = [callbacks], validation_steps = 20)

# plot of accuracy
import matplotlib.pyplot as plt
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Model Accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

# plot of loss
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model Loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()
