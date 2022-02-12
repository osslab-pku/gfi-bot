import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
from gfibot.model import utils


def getdf(newthr):
    df = utils.load_df(newthr)
    return df


def run(
    df, settype, owner, name
):  # load data set and output performance metrics according to the set type (and owner,name if there are)
    X_train, X_test, y_train, y_test = utils.load_train_test_data(
        df, settype, owner, name
    )
    model = XGBClassifier()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_score = model.predict_proba(X_test)[:, 1]

    auc, precision, recall, f1, average_precision = utils.get_all_metrics(
        y_test, y_pred, y_score
    )
    acc = accuracy_score(y_test, y_pred)
    y_test = y_test.values.tolist()
    list0 = []  # for plot bar
    list1 = []
    for i in range(len(y_test)):
        if y_test[i] == 0:
            list0.append(y_score[i])
        else:
            list1.append(y_score[i])
    return np.array([auc, precision, recall, f1, average_precision, acc]), list0, list1


def show_performance(
    settype="overall", newthr=1, owner=None, name=None
):  # settype: 'overall','all4one','one4one'
    # 'overall': the model is trained with histarical issues from all projects in the data set and tested with latest issues from all projects
    # 'all4one': trained with histarical issues from all projects and tested with latest issues from project 'owner/name', owner (str) and name (str) are necessary
    # 'one4one': trained with histarical issues from project 'owner/name', owner (str) and name (str) are necessary, and tested with latest issues from the project 'owner/name', owner (str) and name (str) are necessary
    # if a developer contributed less than newthr commits in a project, the developer is a newcomer for the project
    df = getdf(newthr)
    metric, list0, list1 = run(df, settype, owner, name)
    return metric, list0, list1


if __name__ == "__main__":
    metric, list0, list1 = show_performance(
        "one4one", 1, "Revolutionary-Games", "Thrive"
    )
    print(metric)  # ,list0,list1)
