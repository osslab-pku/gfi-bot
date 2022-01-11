import numpy as np

from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
import utils 


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
    #print(auc,precision, recall, f1, average_precision,acc)
    return(np.array([auc,precision, recall, f1, average_precision,acc]))

def showperformance(settype='overall',newthr=1,owner=None,name=None):#settype: 'overall','all4one','one4one'
    metric=[0,0,0,0,0,0]
    df=getdf(newthr)
    metric=run(df,settype,owner,name)
    return metric

if __name__ == '__main__':
    metric=showperformance('all4one',1,'Mihara','RasterPropMonitor')
    print(metric)





    
