import numpy as np
import scipy.stats as st

def confidence_interval(confidence, mses_list):
    # define the interval tuple
    interval = None
    interval = st.t.interval(confidence, len(mses_list)-1, loc=np.mean(mses_list), scale=st.sem(mses_list))

    return interval

def anomaly_report(mses_list,file_number):
    # here we use the max value as the threshold
    confidence_interval_fp1 = confidence_interval(0.98, mses_list)
    # it is for the false positive detection
    threshold1 = confidence_interval_fp1[1]
    confidence_interval_fp2 = confidence_interval(0.99, mses_list)
    # it is for the false positive detection
    threshold2 = confidence_interval_fp2[1]
    confidence_interval_an = confidence_interval(0.999, mses_list)
    # it is for the anomaly detection
    threshold3 = confidence_interval_an[1]
    # record the potential anomaly logs
    suspicious_logs = []
    # record the false positive logs
    fp_logs = []
    for i in range(len(mses_list)):
        if mses_list[i] > threshold3:
            print('The {}th log in matrix {} is suspiciously anomaly'.format(i, file_number[0]))
            suspicious_logs.append(i)
        elif mses_list[i] > threshold1:
            print('The {}th log in matrix {} is false positive'.format(i, file_number[0]))
            fp_logs.append(i)
        else:
            continue
    return threshold1, threshold2, threshold3, suspicious_logs, fp_logs

if __name__ == '__main__':
    mses_list = [1,2,3]
    file_number = [23,0]
    threshold1, threshold2, threshold3, suspicious_logs, fp_logs = anomaly_report(mses_list, file_number)
    print(threshold1,threshold3,threshold2)
