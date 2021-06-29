# the principles behind Execution path anomaly
# 1. first, we generate the set of distinct log keys from our program
# 2. parse the entries into log keys, the log key sequence ---- an execution path
# 3. the model DeepLog is a multi-class classifier over recent context
## 1. input the recent log keys
## 2. a probability distribution over the n log keys from K ----
## the probability that the next log key in the sequence is a key ki belongs to K

# LSTM
# it learns a probability distribution Pr(mt=ki | M(t-h),...M(t-1)) that maximizes the
# prob of the training log key sequence
#
# every single block remembers a state for its input as a vector of a fixed dimension
#
# the output of previous block+data input -----> fed into this one block
#
# one layer(h unrolled LSTM blocks) ---> a series of LSTM blocks ---- each
# cell includes a
# hidden vector H(t-i) and cell state vector C(t-i）

#
# Description about the model:
# each block remembers a state for its input as a vector of a fixed dimension
#
# input: a window w of h log keys --- (w = {mt−h, . . . ,mt−1})
# output: the log key value comes right after w
#
# the loss function will be categorical cross-entropy loss
#
# omits the input layer and and output layer ---- encoding-decoding schemes
# the input layer encodes the n possible log keys from K(log keys set) as one-hot vectors
#
# output layer:  a standard multinomial logistic function to represent Pr[mt = ki|w]


'''
This version is a version without normalization
'''

import pandas as pd
from keras.models import Sequential
import keras
from keras.layers import Dense, Embedding, Dropout
from keras.layers import LSTM
from keras.utils import *
import numpy as np
import joblib
import os
from sklearn.metrics import mean_squared_error
import re

# =================== build the LSTM part for the first model DeepLog ============================

def load_value_vector(filename):
    # get the normal system execution path
    df = None
    df = pd.read_csv(filename, encoding = "ISO-8859-15")
    return df


# function to transfer log key into EventId
def key_to_EventId(df, dict_filename):
    df_log_trans = df.copy()
    log_key_sequence = df_log_trans['log key']
    # log_key_sequence = list(log_key_sequence)
    # get the unique list
    items = set(log_key_sequence)
    # define the total number of log keys
    K = None
    K = len(items)
    print("the length of unique log_key_sequence is:", K)
    key_name_dict = {}

    for i, item in enumerate(items):
        # items is a set
        # columns are the lines of log key sequence
        for j in range(len(log_key_sequence)):
            if log_key_sequence[j] == item:
                name = 'E' + str(i)
                # we do not replace the string using Exx in the function
                key_name_dict[name] = item.strip('\n')

    joblib.dump(key_name_dict, dict_filename)

    return log_key_sequence, key_name_dict, K


# function to replace the log key event to eventID (in a log key sequence)
def transform_key_k(log_key_sequence, dict):
    print("the length of sequence is {} and the length of dict is {}".format\
              (len(set(log_key_sequence)), len(set(dict.values()))))
    # while set(log_key_sequence) == set(dict.values()):
    for key, value in dict.items():
        for x in log_key_sequence:
            # transform the set type to list type
            log_key_sequence = list(log_key_sequence)
            if value == x:
                log_key_sequence[log_key_sequence.index(x)] = str(key)
            else:
                continue
    return log_key_sequence


# function to filter E in a str and get the sequence with (history length): 1
def get_train(log_key_sequence_str, n_steps, path_filename):
    '''
    :param log_key_sequence_str: E23,E24,E11,E23....
    '''
    X,Y = list(), list()
    seq = None
    # replace the 'E' in eventID to ''
    log_key_sequence_str = re.sub('E','',log_key_sequence_str)
    log_key_sequence_str_list = log_key_sequence_str.split(' ')
    seq = log_key_sequence_str_list
    for i in range(len(log_key_sequence_str_list)):
        # find the end of this pattern
        end_ix = i + n_steps
        # check whether it is beyond the sequence
        if end_ix > len(seq)-1:
            break
        # get the input and output parts for model
        X_seq, Y_seq = seq[i:end_ix], seq[end_ix]
        X.append(X_seq)
        Y.append(Y_seq)
        # define the index with sequence list
        start_end_pair_list = []
        start_end_pair = None
        for x, y in zip(X, Y):
            start_end_pair = tuple((x, y))
            start_end_pair_list.append(start_end_pair)
        np.savetxt(path_filename, start_end_pair_list, delimiter=',', fmt='%s')

    return X, Y


# ================= part to generate the training data ======================
# # ============  Implement the lstm model ==================


def lstm_model(x, y, callbacks, class_num):
    earlystopping = EarlyStopping(monitor='acc', patience=10)
    # according to the article, we will stack two layers of LSTM, the model about stacked LSTM for sequence classification
    model = Sequential()
    # input dim is the length of steps/history
    model.add(Dense(16, input_dim=5, activation='relu'))
    model.add(Dense(16, activation='relu'))
    # output unit is the number of classes
    model.add(Dense(class_num,activation='softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam',metrics=['accuracy'])
    batch_size = 16
    model.fit(x, y, epochs=500, batch_size =16,validation_split=0.2,  callbacks = [earlystopping], verbose=2)
  
    model.save(model, 'path_anomaly_model.h5')
    return model



# ============ part to prediction ==============
def model_predict(model, x_test, y_test):
    errors = None
    # predict the x_test
    Y_pred = model.predict(x_test, verbose=0)
    errors = mean_squared_error(y_test, Y_pred)
    print("the errors are:",errors)
    # for i in range(Y_pred.shape[1]):
        # print("the index of predicted one_hot_labels {} are: {}".format(Y_pred[i],np.argmax(Y_pred[i])))


def model_predict_trace(model, x_test, y_test, key_name_dict):
    # use the dict to define the order: anomaly log
    y_pred = model.predict(x_test, verbose = 0)

    # get the index (we use the one-hot encoder for y)
    yhat = []
    for i in range(y_pred.shape[0]):
        yhat.append(np.argmax(y_pred[i]))

    anomaly_index = []
    anomaly_x_sequence = []
    for n in range(len(yhat)):
        if yhat[n] == np.argmax(y_test[n]):
            pass
        else:
            eventId = 'E' + str(yhat[n])
            anomaly_log_key = key_name_dict[eventId]
            anomaly_index.append(n)
            # get the x_test
            anomaly_x_sequence.append(x_test[n][:])
            # print("log {} is possible anomaly".format(anomaly_log_key))
    print("There are {} possible anomaly logs, the anomaly rate is {}".format(len(anomaly_index), \
                                                        len(anomaly_index)/len(yhat)))
    print("the anomaly index is:", anomaly_index)
    joblib.dump(anomaly_index, 'anomaly_log_index.pkl')



if __name__ == "__main__":

    # ===== generate the training data with large clear logs =====
    log_value_vector_path = '../Dataset/Linux/Malicious_Separate_Structured_Logs/log_value_vector_mali.csv'
    df = load_value_vector(log_value_vector_path)
    df = df.copy()
    # check whether the key_name_dict has been generated
    key_name_dict_path = 'path_key_name_dict.pkl'

    if os.path.isfile(key_name_dict_path):
        print("key_name_dict file has been generated before")
        key_name_dict = joblib.load(key_name_dict_path)
        # get the original log key sequence
        log_key_sequence = df['log key']
        # get the unique log_key_sequence set
        items = list(set(log_key_sequence))
        # define the number of clusters
        K = len(items)
    else:
        dict_filename = 'path_key_name_dict.pkl'
        log_key_sequence, key_name_dict, K = key_to_EventId(df, dict_filename)


    # get the EventID sequence
    log_key_id_sequence = transform_key_k(log_key_sequence, key_name_dict)
    # the length of log_key_id_sequence is 335 here

    # transform the list of data to str data
    for i in range(len(log_key_id_sequence)):
        log_key_id_sequence_str = ' '.join(log_key_id_sequence)
    # get the raw training data
    # define the length of history for LSTM network
    n_steps = 5
    path_filename = '../Dataset/Linux/Malicious_Separate_Structured_Logs/Path_sequence.csv'
    X_normal, Y_normal = get_train(log_key_id_sequence_str, n_steps, path_filename)

    # reshape the X_normal to make it suitable for training ---- time_steps = 3
    # X_normal = np.reshape(X_normal, (-1, 3, 1))

    # reshape the X_normal to make it suitable for training ---- time_steps = 5
    X_normal = np.reshape(X_normal, (-1, 5, 1))

    # make the parameters understandable
    x_train = X_normal


    # ==== generate the testing data with coming logs ====

    log_value_vector_com_path = '../Dataset/Linux/Coming/log_value_vector.csv'
    df_com = load_value_vector(log_value_vector_com_path)
    df_com = df_com.copy()


    # === part to compare and update the key_name_dict_path ===
    # the format of key_name_dict_com is like ---- E95': 'shutting down'
    dict_filename_com = 'path_key_name_dict_com.pkl'

    if os.path.isfile(dict_filename_com):
        print("key_name_dict_com file has been generated before")
        key_name_dict_com = joblib.load(dict_filename_com)
        # get the original log key sequence
        log_key_sequence_com = df_com['log key']
        # get the unique log_key_sequence set
        items_com = list(set(log_key_sequence_com))
        # define the number of clusters
        K_com = len(items_com)
    else:
        log_key_sequence_com, key_name_dict_com, K_com = key_to_EventId(df_com, dict_filename_com)


    # i is the parameter set for new log cluster
    i = 1
    # in order to update the coming dict then
    update_dict = {}
    for key, value in key_name_dict_com.items():
        # check whether
        if value in key_name_dict.values():
            pass
        else:
            # K is the cluster number of normal system logs(training dataset)
            key = 'E'+ str(K + i)
            # update the total dict
            key_name_dict.update({key: value})
            update_dict.update({key: value})
            # increasing i if the coming log belongs to a new cluster
            i += 1
    # update the coming dict
    key_name_dict_com.update(update_dict)
    # return a new key_name_dict
    joblib.dump(key_name_dict, 'path_key_name_dict_updated.pkl')

    # get the EventID sequence using updated key_name_dict
    log_key_id_sequence_com = transform_key_k(log_key_sequence_com, key_name_dict)
    # the length of log_key_id_sequence_com is 118 here

    # transfrom the list of data to str data
    for i in range(len(log_key_id_sequence_com)):
        log_key_id_sequence_str_com = ' '.join(log_key_id_sequence_com)

    # get the raw testing data
    path_filename_com = '../Dataset/Linux/Malicious_Separate_Structured_Logs/Path_sequence_com.csv'
    X_com, Y_com = get_train(log_key_id_sequence_str_com, n_steps, path_filename_com)
    # reshape the X_normal to make it suitable for training ---- time_steps = 5
    X_com = np.reshape(X_com, (-1, 5, 1))
    Y_com = keras.utils.to_categorical(Y_com, num_classes = (K_com + K))
    # in order to update the model or rebuild the model with the new output
    Y_normal = keras.utils.to_categorical(Y_normal, num_classes=(K_com + K))
    # make the parameters understandable
    y_train = Y_normal
    x_test = X_com
    y_test = Y_com

    # ==== part to predict the anomaly logs (training --- normal, test --- coming logs) ===
    print("the lengths of training data and testing data is {} and {}".format(X_normal.shape[0], X_com.shape[0]))
    print("the shape of training data is {} and testing data is {}".format(X_normal.shape, X_com.shape))
    # check whether the model has existed
    filename = 'path_anomaly_model.pkl'
    # load the callback instance
    callbacks = Mycallback()
    if os.path.isfile(filename):
        print("model has been generated before")
        model = joblib.load(filename)
        model_predict(model, x_test, y_test)
        model_predict_trace(model, x_test, y_test, key_name_dict)
    else:
        model = lstm_model(x_train, y_train, callbacks)
        model_predict(model, x_test, y_test)
        model_predict_trace(model, x_test, y_test, key_name_dict)

