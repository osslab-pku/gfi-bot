import pandas as pd
import numpy as np
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.metrics import f1_score
from sklearn.metrics import average_precision_score
from sklearn.metrics import roc_curve
from sklearn.metrics import auc
from typing import Pattern
import multiprocessing as mp
import re
import textstat
from sentistrength import PySentiStr
from tqdm import tqdm
import pymongo
from sklearn.feature_extraction.text import TfidfVectorizer
import json

def unfold(df,s):
    df=df[s].values
    lst=[]
    for i in df:
        dic={}
        for j in range(len(i)):
            dic[j]=i[j]
        lst.append(dic)
    return pd.DataFrame(lst)

def get_text_feature(X_train):
    train_data = TfidfVectorizer(analyzer='word', input='content', stop_words='english', max_features=50).fit_transform(X_train).toarray()
    return train_data

def get_label(clscmt,newthr):
    if clscmt<newthr:
        return 1
    return 0

def generateRate(lst,newthr):
    c1=0
    c2=0
    for i in lst:
        if i!= None:
            c1+=1
            if i<newthr:
                c2+=1
    if c1==0:
        return 0
    else:
        return c2/c1
       
def generateNum(lst,newthr):
    c1=0
    for i in lst:
        if i!= None:
            if i<newthr:
                c1+=1
    return c1

def eventcount(lst,newthr): 
    num_sum=0
    num_new=0
    len_lst=[]
    res=[0,0,0,0,0,0]
    for i in lst:
        f=[0,0,0,0,0,0]
        c=0
        d=0
        if len(i)!=0:
            for j in i:
                if j != [None]:
                    d+=1
                    for k in range(3):
                        f[k]+=j[k]
                    c+=1
                    f[3]+=generateNum(j[3],newthr)
                    f[4]+=generateRate(j[3],newthr)
                    if j[0]<newthr:
                        num_new+=1
                    num_sum+=1
            if c!=0:
                for k in range(5):
                        f[k]=f[k]/c
            f[5]+=d
        len_lst.append(c)        
        for p in range(6):
            res[p]+=f[p]
    for p in  range(5):
        res[p]/=len(lst)    
    res+=len_lst[:-1]
    res.append(num_new)
    if num_sum==0:
        res.append(0)
    else:
        res.append(num_new/num_sum)
    return res
    
def getcommentuser(i,newthr):
    num_sum=0
    num_new=0
    f=[0,0,0,0,0,0]
    if len(i)!=0:
        c=0
        d=0
        for j in i:
            d+=1
            if j != [None]:
                for k in range(3):
                    f[k]+=j[k]
                c+=1
                f[3]+=generateNum(j[3],newthr)
                f[4]+=generateRate(j[3],newthr)
                if j[0]<newthr:
                    num_new+=1
                num_sum+=1
        if c!=0:
            for k in range(5):
                    f[k]=f[k]/c       
        f[5]+=d        
    f.append(num_new)
    if num_sum==0:
        f.append(0)
    else:
        f.append(num_new/num_sum)
    return f
    
def labeleventcount(lst,newthr):
    i=lst[0]
    num_sum=0
    num_new=0
    f=[0,0,0,0,0]
    if len(i)!=0:
        c=0
        for j in i:
            if j != [None]:
                for k in range(3):
                    f[k]+=j[k]
                c+=1
                f[3]+=generateNum(j[3],newthr)
                f[4]+=generateRate(j[3],newthr)
                if j[0]<newthr:
                    num_new+=1
                num_sum+=1
        if c!=0:
            for k in range(5):
                    f[k]=f[k]/c        
    f.append(num_new)
    if num_sum==0:
        f.append(0)
    else:
        f.append(num_new/num_sum)
    return f

def ifrptnew(rptcmt,newthr):
    if rptcmt<newthr:
        return 1
    return 0

def getratio(lst,newthr):
    if lst is None:
        return 0
    else:
        lst=[d for d in lst if d is not None]
        if lst==[]:
            return 0
        pnum=sum(d<newthr for d in lst)
        nnum=len(lst)-pnum
        if pnum==0:
            pnum=0.1
        return nnum/pnum

def getdataset(owner,reponame,number,resolver_commit_num,clst,pro_star,isslist,propr, rptcmt, rptiss,rptpr, rptissues,ownercmt, owneriss,ownerpr, ownerissues,procmt, contributornum, crtclsissnum, openiss, openissratio, clsisst,
              labels, eventdatalist, commentlist, rpthasevent, rpthascomment,
              NumOfCode,NumOfUrls,NumOfPics,coleman_liau_index,flesch_reading_ease,flesch_kincaid_grade,
              automated_readability_index,LengthOfTitle,LengthOfDescription,commentnum,title,body,comment,newthr):
    #[owner,reponame,number,resolver_commit_num,pro_star,isslist,propr, rptcmt, rptiss,rptpr, rptissues,ownercmt, owneriss,ownerpr, ownerissues,procmt, contributornum, crtclsissnum, openiss, openissratio, clsisst,
    #          labels, eventdatalist, commentlist, rpthasevent, rpthascomment,
    #          NumOfCode,NumOfUrls,NumOfPics,coleman_liau_index,flesch_reading_ease,flesch_kincaid_grade,
    #          automated_readability_index,LengthOfTitle,LengthOfDescription,commentnum,title,body,comment,newthr]=i
    proissnewratio=generateRate(isslist,newthr)
    ownerissnewratio=generateRate(ownerissues,newthr)
    proissnewnum=generateNum(isslist,newthr)
    ownerissnewnum=generateNum(ownerissues,newthr)
    labelevent=labeleventcount(eventdatalist,newthr)
    ifnew=get_label(resolver_commit_num,newthr)
    event=eventcount(eventdatalist,newthr)
    commentuser=getcommentuser(commentlist,newthr)
    rptisnew=ifrptnew(rptcmt,newthr)
    rptnpratio=getratio(rptissues,newthr)


    res={'owner':owner,'name':reponame,'number':number, 'ifnew':ifnew, 'clst':clst, 'pro_star':pro_star,'proissnewnum':proissnewnum,'propr':propr,
                'rptcmt':rptcmt, 'rptiss':rptiss,'rptpr':rptpr, 'rptnpratio':rptnpratio,'rptisnew':rptisnew,'proissnewratio':proissnewratio,
                'ownercmt':ownercmt, 'owneriss':owneriss,'ownerpr':ownerpr, 'ownerissnewnum':ownerissnewnum,'ownerissnewratio':ownerissnewratio,
                'procmt':procmt, 'contributornum':contributornum, 'crtclsissnum':crtclsissnum, 'openiss':openiss, 'openissratio':openissratio, 'clsisst':clsisst,
                'labels':labels, 'event':event, 'commentuser':commentuser, 'rpthasevent':rpthasevent,'rpthascomment':rpthascomment,'labelevent':labelevent,
                'NumOfCode':NumOfCode,'NumOfUrls':NumOfUrls,'NumOfPics':NumOfPics,'coleman_liau_index':coleman_liau_index,'flesch_reading_ease':flesch_reading_ease,'flesch_kincaid_grade':flesch_kincaid_grade,
                'automated_readability_index':automated_readability_index,'LengthOfTitle':LengthOfTitle,'LengthOfDescription':LengthOfDescription,'commentnum':commentnum,'title':title,'body':body,'comment':comment
        }
    return res

def load_df(newthr):
    myclient = pymongo.MongoClient('mongodb://localhost:27017/',connect=False)
    mydb = myclient['gfibot']['issuedataset']
    df=pd.DataFrame(columns=('owner','name','resolver_commit_num','pro_star','isslist','propr', 'rptcmt', 'rptiss','rptpr', 'rptissues','ownercmt', 'owneriss','ownerpr', 'ownerissues','procmt', 'contributornum', 'crtclsissnum', 'openiss', 'openissratio', 'clsisst',
              'labels', 'events', 'commentusers', 'rpthasevent', 'rpthascomment',
              'NumOfCode','NumOfUrls','NumOfPics','coleman_liau_index','flesch_reading_ease''flesch_kincaid_grade',
              'automated_readability_index','LengthOfTitle','LengthOfDescription','commentnum','title','body','comment'))
    issuelist=[[x['owner'],x['name'],x['number'],x['resolver_commit_num'],x['clst'],x['pro_star'],x['isslist'],x['propr'], x['rptcmt'], x['rptiss'],x['rptpr'], x['rptissues'],x['ownercmt'], x['owneriss'],x['ownerpr'], x['ownerissues'],x['procmt'], x['contributornum'], x['crtclsissnum'], x['openiss'], x['openissratio'], x['clsisst'],
              x['labels'], x['events'], x['commentusers'], x['rpthasevent'], x['rpthascomment'],
              x['NumOfCode'],x['NumOfUrls'],x['NumOfPics'],x['coleman_liau_index'],x['flesch_reading_ease'],x['flesch_kincaid_grade'],
              x['automated_readability_index'],x['LengthOfTitle'],x['LengthOfDescription'],x['commentnum'],
              x['title'],x['body'],x['comment'],newthr] for x in mydb.find()]
    
    #for i in issuelist:
    #    res=getdataset(i)
    with mp.Pool(mp.cpu_count() // 2) as pool:
        res = pool.starmap(getdataset,issuelist)
    rowdf=pd.DataFrame(res)
    title=pd.DataFrame(get_text_feature(rowdf['title'].values))
    body=pd.DataFrame(get_text_feature(rowdf['body'].values))
    comment_text=pd.DataFrame(get_text_feature(rowdf['comment'].values))
    rowdf1=rowdf[["ifnew","owner","name","number","title","body","comment","clst"]]
    rowdf2=rowdf[['pro_star','proissnewnum','propr','rptcmt', 'rptiss',
                #'rptnpratio',
                'rptpr', 'rptisnew','proissnewratio',
                'ownercmt', 'owneriss','ownerpr', 'ownerissnewnum','ownerissnewratio',
                'procmt', 'contributornum', 'crtclsissnum', 'openiss', 'openissratio', 'clsisst',
                'rpthasevent','rpthascomment',
                'NumOfCode','NumOfUrls','NumOfPics','coleman_liau_index','flesch_reading_ease','flesch_kincaid_grade',
                'automated_readability_index','LengthOfTitle','LengthOfDescription','commentnum'
                ]]
    labelevent=unfold(rowdf,"labelevent")
    commentuser=unfold(rowdf,"commentuser")
    event=unfold(rowdf,"event")
    labels=unfold(rowdf,"labels")


    df=pd.concat([title,body,comment_text,rowdf1,rowdf2,labelevent,commentuser,event,labels],axis=1)
    #df=pd.concat([title,body,comment_text,rowdf1,rowdf2,labelevent,commentuser],axis=1)

    c=[]
    for i in range(title.shape[1]):
        c.append("title"+str(i))
    for i in range(body.shape[1]):
        c.append("description"+str(i))
    for i in range(comment_text.shape[1]):
        c.append("com"+str(i))
    c+=["ifnew","owner","name","number","title","body","comment","clst"]
    for i in range(rowdf2.shape[1]):
        c.append("rowdf"+str(i))  
    for i in range(labelevent.shape[1]):
        c.append("labelevent"+str(i))
    for i in range(commentuser.shape[1]):
        c.append("commentuser"+str(i))
    for i in range(event.shape[1]):
        c.append("event"+str(i))
    for i in range(labels.shape[1]):
        c.append("labels"+str(i))
    df.columns=c
#    T.dropna(inplace=True)
    return df

def load_train_test_data(df,settype,owner,name):
    if settype=='one4one':
        prodf=df.loc[(df["owner"] == owner) & (df["name"] == name)]
        prodf.sort_values(by='clst')
        p_train_split=int(0.9*prodf.shape[0])
        train_data=prodf.iloc[:p_train_split]
        test_data=prodf.iloc[p_train_split+1:]
    elif settype=='all4one':
        pd.set_option('display.max_rows', None)
        prodf=df.loc[(df["owner"] == owner) & (df["name"] == name)]
        prodf=prodf.sort_values(by='clst')
        df=df.sort_values(by='clst')
        prodf=prodf.reset_index(drop=True)
        df=df.reset_index(drop=True)

        p_train_split=int(0.9*prodf.shape[0])
        test_data=prodf.iloc[p_train_split+1:]
        test_data=test_data.reset_index(drop=True)
        owner=test_data.loc[0,"owner"]
        name=test_data.loc[0,"name"]
        number=test_data.loc[0,"number"]
        ind=df[(df["owner"] == owner) & (df["name"] == name) & (df["number"] == number)].index.tolist()[0]
        train_data=df.iloc[:ind]
    else:
        df.sort_values(by='clst')
        p_train_split=int(0.9*df.shape[0])
        train_data=df.iloc[:p_train_split]
        test_data=df.iloc[p_train_split+1:]

    print(train_data[train_data.ifnew == 1].shape[0],train_data[train_data.ifnew == 0].shape[0],test_data.shape[0])#ifnew=1和0的数量
    p_train = train_data[train_data.ifnew == 1]
    p_train = p_train.sample(frac=2000/p_train.shape[0],replace=True,random_state=0)

    n_train = train_data[train_data.ifnew == 0]
    n_train=n_train.sample(frac=2000/n_train.shape[0],replace=True,random_state=0)

    train_data=pd.concat([p_train,n_train],ignore_index=True)
    train_data=train_data.sample(frac=1, random_state=0)
    y_train=train_data['ifnew']
    y_test=test_data['ifnew']

    del train_data['ifnew']
    del train_data['owner']
    del train_data['name']
    del train_data['number']
    del train_data['title']
    del train_data['body']
    del train_data['comment']
    del train_data['clst']

    del test_data['ifnew']
    del test_data['owner']
    del test_data['name']
    del test_data['number']
    del test_data['title']
    del test_data['body']
    del test_data['comment']
    del test_data['clst']
    X_train=train_data
    X_test=test_data
    return X_train, X_test, y_train, y_test

def get_all_metrics(eval_labels, pred_labels,scores):
    fpr, tpr, thresholds_keras = roc_curve(eval_labels,scores)
    print(thresholds_keras[np.argmax(tpr - fpr)])
    auc_ = auc(fpr, tpr)
    print("auc_keras:" + str(auc_))

    precision = precision_score(eval_labels, pred_labels)
    print('Precision score: {0:0.8f}'.format(precision))

    recall = recall_score(eval_labels, pred_labels)
    print('Recall score: {0:0.8f}'.format(recall))

    f1 = f1_score(eval_labels, pred_labels)
    print('F1 score: {0:0.8f}'.format(f1))

    average_precision = average_precision_score(eval_labels, pred_labels)
    print('Average precision-recall score: {0:0.8f}'.format(average_precision))
    
    return auc_, precision, recall, f1, average_precision

