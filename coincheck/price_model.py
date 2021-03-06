from datetime import datetime
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras.layers import LSTM
from keras.optimizers import Adam
from keras.utils.data_utils import get_file
import numpy as np
import random, sys

from sklearn import model_selection

from base.foots import Foots
from base.price_model import BasePriceModel
import pytz


class CoincheckPriceModel(BasePriceModel):

    def __init__(self):
        self.sentence_length = 288

    def fit(self, path):
        data = np.load(path)
        data_length = len(data)
        sentences_count = data_length - self.sentence_length
        print('data length:', data_length)
        print('sentences count:', sentences_count)
        X = []
        y = []
        for sentence_index in range(0, sentences_count):
            x = data[sentence_index:sentence_index + self.sentence_length]
            max_x = np.max(x)
            X.append(x / max_x)
            y_ = data[sentence_index + self.sentence_length]
            y.append(y_ / max_x)
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        X_train, X_test, y_train, y_test = model_selection.train_test_split(X, y)
        batch_size = 512
        self.model.fit(X_train, y_train, batch_size=batch_size)
        score = self.model.evaluate(X_test, y_test, batch_size=batch_size)
        print('score:', score)

    def make_data(self, path, limit=None):
        foots = Foots()
        file = open(path)
        count = 0
        while True:
            line = file.readline()
            if not line:
                break
            line = line.strip()
            csv = line.split(',')
            time = int(csv[0])
            last_price = float(csv[1])
            foots.add(time, last_price)
            if limit and count > limit:
                break
            count += 1
        file.close()
        foot_hashes = list(foots.foots.keys())
        first_foot_hash = foot_hashes[0]
        last_foot_hash = foot_hashes[-1]
        foot = None
        data = []
        for foot_hash in range(first_foot_hash, last_foot_hash + 1):
            if foot_hash in foots.foots:
                foot = foots.foots[foot_hash]
            data.append(foot.array)
        np.save(path, np.asarray(data))

    def make_model(self):
        model = Sequential()
        lstm = LSTM(128, input_shape=(self.sentence_length, 4), return_sequences=False)
        model.add(lstm)
        model.add(Dense(4))
        model.add(Activation("linear"))
        optimizer = Adam(lr=0.001)
        model.compile(loss='mean_squared_error', optimizer=optimizer)
        self.model = model
        return self.model

    def predict(self, x):
        max_x = np.max(x)
        predicted = self.model.predict(x / max_x)
        return predicted * max_x
