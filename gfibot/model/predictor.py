import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
import os
import sys

current_work_dir = os.path.dirname(__file__)
utpath = os.path.join(current_work_dir, "..")
sys.path.append(utpath)
from model import utils


def show_performance(
    settype="overall", newthr=1, owner=None, name=None
):  # load data set and output performance metrics according to the set type (and owner,name if there are)
    # settype: 'overall','all4one','one4one'
    # 'overall': the model is trained with histarical issues from all projects in the data set and tested with latest issues from all projects
    # 'all4one': trained with histarical issues from all projects and tested with latest issues from project 'owner/name', owner (str) and name (str) are necessary
    # 'one4one': trained with histarical issues from project 'owner/name', owner (str) and name (str) are necessary, and tested with latest issues from the project 'owner/name', owner (str) and name (str) are necessary
    # if a developer contributed less than newthr commits in a project, the developer is a newcomer for the project
    if settype == "one4one":
        data = utils.load_data(newthr, owner, name)
    else:
        data = utils.load_data(newthr)
    X_train, X_test, y_train, y_test = utils.load_train_test_data(
        data, settype, owner, name
    )
    model = XGBClassifier()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_score = model.predict_proba(X_test)[:, 1]

    auc, precision, recall, f1 = utils.get_all_metrics(y_test, y_pred, y_score)
    acc = accuracy_score(y_test, y_pred)
    y_test = y_test.values.tolist()
    """
    list0 = []  # for plot bar
    list1 = []
    for i in range(len(y_test)):
        if y_test[i] == 0:
            list0.append(y_score[i])
        else:
            list1.append(y_score[i])
    """
    return np.array([auc, precision, recall, f1, acc])


"""
def getGFIlist(owner: str,name: str,settype="one4one",newthr=1):#settype="all4one" or "one4one"
    if settype=="all4one":
        data = utils.load_data(newthr)
    else:
        data = utils.load_data(newthr,owner,name)
    X_train, X_test, y_train = utils.load_train_data(
        data, settype, owner, name
    )
    issnumber=X_test["number"].values
    del X_test["number"]
    model = XGBClassifier()
    model.fit(X_train, y_train)
    y_score = model.predict_proba(X_test)[:, 1]
    isslist=[[issnumber[i],y_score[i]] for i in range(len(issnumber))]
    print(isslist)
"""
if __name__ == "__main__":
    # GFIlist=getGFIlist("Mihara", "RasterPropMonitor")
    metric, list0, list1 = show_performance(
        "one4one", 1, "Revolutionary-Games", "Thrive"
    )
    print(metric)  # ,list0,list1)
