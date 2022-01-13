import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
import utils 
import matplotlib.pyplot as plt

def getdf(newthr):
    df=utils.load_df(newthr)
    return df

def run(df,settype,owner,name):
    X_train, X_test, y_train, y_test = utils.load_train_test_data(df,settype,owner,name)
    model = XGBClassifier()               
    model.fit(X_train,y_train)            
    y_pred = model.predict(X_test)
    y_score=model.predict_proba(X_test)[:,1]
        
    auc,precision, recall, f1, average_precision=utils.get_all_metrics(y_test,y_pred,y_score)
    acc=accuracy_score(y_test,y_pred)
    y_test=y_test.values.tolist()
    #print(auc,precision, recall, f1, average_precision,acc)
    list0=[]#for plot bar
    list1=[]
    for i in range(len(y_test)):
        if y_test[i]==0:
            list0.append(y_score[i])
        else:
            list1.append(y_score[i])
    return np.array([auc,precision, recall, f1, average_precision,acc]),list0,list1

def showperformance(settype='overall',newthr=1,owner=None,name=None):#settype: 'overall','all4one','one4one'
    df=getdf(newthr)
    metric,list0,list1=run(df,settype,owner,name)
    return metric,list0,list1

if __name__ == '__main__':
    metric,list0,list1=showperformance('one4one',1,'Revolutionary-Games','Thrive')
    print(metric)#,list0,list1)





    
