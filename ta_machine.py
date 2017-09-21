# -*- coding: utf-8 -*-
"""
Created on Sun Aug 27 18:53:46 2017

@author: lenovo
"""
import urllib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
import numpy as np
import os
import talib
from sklearn.naive_bayes import GaussianNB
from sklearn import svm
from matplotlib import pyplot as plt
from candleplot import *
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets


def prediksi(ticker):
    print(ticker)
    try:
        url="https://www.google.com/finance/historical?output=csv&q="+ticker
        stock=ticker+".csv"
        urllib.request.urlretrieve(url,stock)
    except:
        try:
            print("Retrying..")
            url="https://www.google.com/finance/historical?output=csv&q="+ticker
            stock=ticker+".csv"
            urllib.request.urlretrieve(url,stock)
        except:
            print("Connection Error..")
            exit(0)

        
    df = pd.read_csv(stock).dropna(how='any') 
    for i in df:
        df = df[~df[i].isin(["-"])]
        
    df.iloc[:] = df.iloc[::-1].values
        
    try:
        rsi = pd.DataFrame(talib.RSI(df['Close'].values,timeperiod=14),columns=['RSI_14'])
        atr = pd.DataFrame(talib.ATR(df['High'].values.astype(float),df['Low'].values.astype(float),df['Close'].values.astype(float),timeperiod=14),columns=["ATR_14"])
        roc = pd.DataFrame(talib.ROC(df['Close'].values,timeperiod=14),columns=["ROC_14"])
        wilr = pd.DataFrame(talib.WILLR(df['High'].values.astype(float),df['Low'].values.astype(float),df['Close'].values,timeperiod=14),columns=["WILLR"])
        mom = pd.DataFrame(talib.MOM(df['Close'].values,timeperiod=14),columns=["MOM_14"])
        aaron = pd.DataFrame(talib.AROONOSC(df['High'].values.astype(float),df['Low'].values.astype(float),timeperiod=14),columns=["ARN_14"])
       
    except Exception as e:
        print(e)   
        
    frames = [df,rsi,atr,roc,wilr,mom,aaron]
    data = pd.concat(frames,axis=1)
    data = data.loc[14:,~data.columns.duplicated()].reset_index()
    data = data.dropna(how='any')
    close = data['Close'].values
    
    threshold = float(input("threshold (%): "))
    
    up_t = 1+threshold/100
    down_t = 1-threshold/100
    Target = []
    for i in range(len(close)):
        try:
            if (close[i]*up_t)<close[i+1]:
                Target.append("UP")
            elif (close[i]*down_t<=close[i+1]) and (close[i]*up_t)>=close[i+1]:
                Target.append("STABLE")
            elif (close[i]*down_t)>close[i+1]:
                Target.append("DOWN")
                
        except:
            Target.append("-")         
    
    forest = RandomForestClassifier(n_estimators=5, random_state=2)  
    X=data[['RSI_14','ATR_14','ROC_14','WILLR',"MOM_14","ARN_14"]].copy()
    train_X = X[:len(X)-1]
    train_Y = Target[:len(Target)-1] 
    forest.fit(train_X,train_Y)
    
    RandomForestClassifier(bootstrap=True, class_weight=None, criterion='gint', max_depth=None, max_features='auto', max_leaf_nodes=None,min_samples_leaf=1,min_samples_split=2,min_weight_fraction_leaf=0.0, n_estimators=100,n_jobs=1,oob_score=False, random_state=2, verbose= 2, warm_start=False)
    
    clf = MLPClassifier(solver='lbfgs', alpha=1e-5,hidden_layer_sizes=(100,100,100,100,100,100,100, ), random_state=1)
    clf.fit(train_X,train_Y)
    
    gnb = GaussianNB()
    gnb.fit(train_X,train_Y)
    
    vm = svm.SVC()
    vm.fit(train_X,train_Y)
    y_eval_vm = vm.predict(train_X)
    y_pred_vm = vm.predict(X)
    
    
    y_eval_gnb = gnb.predict(train_X)
    y_pred_gnb = gnb.predict(X)
    
    y_pred_nn = clf.predict(X)
    y_eval_nn = clf.predict(train_X)
    y_eval_frt = forest.predict(train_X)
    print("Training accuracy: \r")
    print("Random Forest: %.3f "%(np.mean(y_eval_frt == train_Y)))
    print("Neural Network: %.3f "%(np.mean(y_eval_nn == train_Y)))
    print("Naive Bayes: %.3f " %(np.mean(y_eval_gnb == train_Y)))
    print("Suppor Vector Machine: %.3f " %(np.mean(y_eval_vm == train_Y)))
    y_pred_frt = forest.predict(X)
    print ("using " + data['Date'].values[-1] +" data")
    
    print("Random Forest: %s" %(y_pred_frt[-1]))
    print("Neural Network: %s" %(y_pred_nn[-1]))
    print("Naive Bayes: %s" %(y_pred_gnb[-1]))
    print("Support Vector Machine: %s \n" %(y_pred_gnb[-1]))

    hasil = y_pred_nn[-1][0]+y_pred_gnb[-1][0]+y_pred_frt[-1][0]+y_pred_vm[-1][0]
            
    os.system("del /f %s" %stock)
    return close,Target,train_X,hasil,data

if __name__ == '__main__':
    ticker = input("predict what stock?: ")
    y = prediksi(ticker)
    df = y[2]
    #df['ROC_14'].plot(figsize=(10,10))
    
    fig, axes = plt.subplots(nrows=len(df.columns)+1,sharex=True)
    index = 0
    fig.tight_layout()
    for i in df:
        df[i].plot(ax=axes[index],title=i,figsize=(9,9))
        index+=1
                
    ticks = []
    for i in y[1]:
        if i=="STABLE":
            ticks.append(0.0)
        elif i == "UP":    
            ticks.append(10)
        else:    
            ticks.append(-10)
            
    axes[index].plot(ticks)
    axes[index].set_title("Price Movement")
    plt.show()
    
    data = []
    data_plot = y[4]
    for i in range(len(data_plot)):
        temp=(i, data_plot['Open'][i], data_plot['Close'][i], data_plot['Low'][i], data_plot['High'][i])
        temp=tuple(temp)
        data.append(temp)
        
    item = CandlestickItem(data)
    plt_qt = pg.plot(title='price candleplot')
    plt_qt.addItem(item)
    
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
    
    

