import pandas as pd
import logging
import lightgbm
import numpy as np
import random
import math
import os


def get_proname(owner, name):
    return owner + "/" + name


def combine(title, body):
    return title + body


def norm_score(scores, max_score, min_score):
    if max_score == min_score:
        norm_sore_list = [1.0 for score in scores]
    else:
        norm_sore_list = [
            1.0 * (score - min_score) / (max_score - min_score) for score in scores
        ]
    return np.asarray([norm_sore_list])


def get_lamb_metrics(training_set, valid_set, test_set, idname, xnames):
    qids_train = training_set.groupby(idname)[idname].count().to_numpy()
    X_train = training_set[xnames]
    y_train = training_set[["match"]]

    qids_validation = valid_set.groupby(idname)[idname].count().to_numpy()
    X_validation = valid_set[xnames]
    y_validation = valid_set[["match"]]

    model = lightgbm.LGBMRanker(
        objective="lambdarank",
    )

    model.fit(
        X=X_train,
        y=y_train,
        group=qids_train,
        eval_set=[(X_validation, y_validation)],
        eval_group=[qids_validation],
        eval_at=5,
    )
    metrics = get_metrics(model, idname, test_set, xnames)
    return metrics


def toisgfi(gfilabelnum):
    return int(gfilabelnum > 0)


def get_metrics(model, idname, test_set, xnames):
    global randseed
    top1match = []
    top3match = []
    top5match = []
    top10match = []
    firstrank = []
    list_ids = list(set(test_set[idname].values.tolist()))
    list_ids.sort()

    true_relevance_list = []
    scores_list = []
    max_score = 0
    min_score = 0
    for id in list_ids:
        clsset = test_set[test_set[idname] == id]
        clsset.reset_index(drop=True, inplace=True)
        clsset = clsset.copy()
        X_test = clsset[xnames]
        X_test.reset_index(drop=True, inplace=True)

        true_relevance = np.asarray([clsset["match"].values.tolist()])
        scores = list(model.predict(X_test))
        max_score = max(scores + [max_score])
        min_score = min(scores + [min_score])

        true_relevance_list.append(true_relevance)
        scores_list.append(scores)

    new_scores_list = [norm_score(s, max_score, min_score) for s in scores_list]

    for i in range(len(new_scores_list)):
        true_relevance = true_relevance_list[i]
        if len(true_relevance[0]) < 10:
            continue
        scores = new_scores_list[i]

        matchrank = rank(true_relevance, scores)
        top1match.append(int(sum([i < 1 for i in matchrank]) > 0))
        top3match.append(int(sum([i < 3 for i in matchrank]) > 0))
        top5match.append(int(sum([i < 5 for i in matchrank]) > 0))
        top10match.append(int(sum([i < 10 for i in matchrank]) > 0))
        firstrank.append(min(matchrank))

    ratio1 = np.mean(top1match)
    ratio3 = np.mean(top3match)
    ratio5 = np.mean(top5match)
    ratio10 = np.mean(top10match)

    firstrank = [i + 1 for i in firstrank]
    firsthitmedian = np.median(firstrank)
    return [ratio1, ratio3, ratio5, ratio10, firsthitmedian]


def rank(a, b):
    a = list(a[0])
    b = list(b[0])
    indlst = []
    while 1 in a:
        ind = a.index(1)
        indlst.append(ind)
        a[ind] = 0
    sortlst = [b[i] for i in indlst]
    b.sort()
    res0 = [len(b) - b.index(i) - 1 for i in sortlst]
    b.sort(reverse=True)
    res1 = [b.index(i) for i in sortlst]
    res = [math.floor((res0[i] + res1[i]) / 2) for i in range(len(res0))]
    return res


def ifclsnew(clscmt):
    if clscmt < cmtthre:
        return 1
    else:
        return 0


def get_lamb_lst(training_set, valid_set, test_set, idname, xnames):
    qids_train = training_set.groupby(idname)[idname].count().to_numpy()
    X_train = training_set[xnames]
    y_train = training_set[["match"]]

    qids_validation = valid_set.groupby(idname)[idname].count().to_numpy()
    X_validation = valid_set[xnames]
    y_validation = valid_set[["match"]]

    model = lightgbm.LGBMRanker(
        objective="lambdarank",
    )

    model.fit(
        X=X_train,
        y=y_train,
        group=qids_train,
        eval_set=[(X_validation, y_validation)],
        eval_group=[qids_validation],
        eval_at=5,
    )
    return get_lst(model, idname, test_set, xnames)


def get_lst(model, idname, test_set, xnames):
    global randseed
    list_ids = list(set(test_set[idname].values.tolist()))
    list_ids.sort()
    issrecnumbs = []
    issnumbs = []
    wrongnum = []
    pronamelst = []
    for id in list_ids:
        clsset = test_set[test_set[idname] == id]
        clsset.reset_index(drop=True, inplace=True)
        clsset = clsset.copy()
        X_test = clsset[xnames]
        X_test.reset_index(drop=True, inplace=True)

        true_relevance = clsset["match"].values.tolist()
        owner = clsset["owner"].values.tolist()
        name = clsset["name"].values.tolist()
        number = clsset["number"].values.tolist()
        isgfi = clsset["cls_isnew"].values.tolist()

        scores = list(model.predict(X_test))

        rightind = true_relevance.index(1)
        rightprob = scores[rightind]
        issrecnumb = []
        issnumb = []
        eqissnumb = []
        for m in range(len(true_relevance)):
            issrecnumb.append(owner[m] + name[m] + str(number[m]))
            if scores[m] > rightprob:
                issnumb.append(owner[m] + name[m] + str(number[m]))
            if scores[m] == rightprob and rightind != m:
                eqissnumb.append(owner[m] + name[m] + str(number[m]))
        half_length = math.floor(len(eqissnumb) / 2)
        random.seed(randseed)
        randseed += 1
        random_elements = random.sample(eqissnumb, half_length)
        issnumb += random_elements
        pronamelst.append(owner[0] + name[0])
        wrongnum.append(len(issnumb))
        issnumbs.extend(issnumb)
        issrecnumbs.extend(issrecnumb)

    oneissfail = []
    theissnumbslst = list(set(issrecnumbs))

    theissnumbslst.sort()
    for aiss in theissnumbslst:
        if issrecnumbs.count(aiss) > 0:
            oneissfail.append(issnumbs.count(aiss) / issrecnumbs.count(aiss))

    return np.median(oneissfail), np.median(wrongnum)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)

    idname = "issgroupid"
    xnames_sub_cumu = [  ##General experience
        # Cumulative OSS experience
        "clsallcmt",
        "clsallpr",
        "clsalliss",
        "clspronum",
        "clsiss",
        "clsallprreview",
    ]

    xnames_sub_act = [  ##General experience
        # Activeness
        "clsonemonth_cmt",
        "clstwomonth_cmt",
        "clsthreemonth_cmt",
        "clsonemonth_pr",
        "clstwomonth_pr",
        "clsthreemonth_pr",
        "clsonemonth_iss",
        "clstwomonth_iss",
        "clsthreemonth_iss",
    ]

    xnames_sub_sen = [  ##General experience
        # Sentiment
        "clsissuesenmean",
        "clsissuesenmedian",
        "clsprsenmean",
        "clsprsenmedian",
    ]

    xnames_sub_clssolvediss = [  ##Specific experience
        # Content of historical contributions
        "solvedisscos_sim",
        "solvedisscos_mean",
        #'solvedisseuc_sim','solvedisseuc_mean',
        "solvedissjaccard_sim",
        "solvedissjaccard_sim_mean",
        "solvedissuelabel_sum",
        "solvedissuelabel_ratio",
    ]

    xnames_sub_clsrptiss = [  ##Specific experience
        # Content of historical contributions
        "issjaccard_sim",
        "issjaccard_sim_mean",
        "isscos_sim",
        "isscos_mean",
        # "isseuc_sim", "isseuc_mean",
        "issuelabel_sum",
        "issuelabel_ratio",
    ]

    xnames_sub_clscomtiss = [  ##Specific experience
        # Content of historical contributions
        "commentissuelabel_sum",
        "commentissuelabel_ratio",
        "commentissuecos_sim",
        "commentissuecos_sim_mean",
        #'commentissueeuc_sim','commentissueeuc_sim_mean',
        "commentissuejaccard_sim",
        "commentissuejaccard_sim_mean",
    ]

    xnames_sub_clscmt = [  ##Specific experience
        # Content of historical contributions
        "cmtjaccard_sim",
        "cmtjaccard_sim_mean",
        "cmtcos_sim",
        "cmtcos_mean",
        # "cmteuc_sim", "cmteuc_mean",
    ]

    xnames_sub_clspr = [  ##Specific experience
        # Content of historical contributions
        "prjaccard_sim",
        "prjaccard_sim_mean",
        "prcos_sim",
        "prcos_mean",
        # "preuc_sim", "preuc_mean",
        "prlabel_sum",
        "prlabel_ratio",
    ]

    xnames_sub_clsprreview = [  ##Specific experience
        # Content of historical contributions
        "prreviewcos_sim",
        "prreviewcos_sim_mean",
        #'prrevieweuc_sim', 'prrevieweuc_sim_mean',
        "prreviewjaccard_sim",
        "prreviewjaccard_sim_mean",
    ]

    xnames_sub_clscont = (
        xnames_sub_clscmt
        + xnames_sub_clspr
        + xnames_sub_clsprreview
        + xnames_sub_clsrptiss
        + xnames_sub_clscomtiss
        + xnames_sub_clssolvediss
        + ["lan_sim"]
    )

    xnames_sub_domain = [  ##Specific experience
        # Domain of historical contributions
        "readmecos_sim_mean",
        "readmecos_sim",
        "readmejaccard_sim_mean",
        "readmejaccard_sim",
        #'readmeeuc_sim_mean', 'readmeeuc_sim',
        "procos_mean",
        "procos_sim",
        "projaccard_mean",
        "projaccard_sim",
        # "proeuc_mean", "proeuc_sim",
        "prostopic_sum",
        "prostopic_ratio",
    ]

    xnames_sub_isscont = [  ##Candidate issues
        # Content of issues
        "LengthOfTitle",
        "LengthOfDescription",
        "NumOfCode",
        "NumOfUrls",
        "NumOfPics",
        "buglabelnum",
        "featurelabelnum",
        "testlabelnum",
        "buildlabelnum",
        "doclabelnum",
        "codinglabelnum",
        "enhancelabelnum",
        "gfilabelnum",
        "mediumlabelnum",
        "majorlabelnum",
        "triagedlabelnum",
        "untriagedlabelnum",
        "labelnum",
        "issuesen",
        "coleman_liau_index",
        "flesch_reading_ease",
        "flesch_kincaid_grade",
        "automated_readability_index",
    ]

    xnames_sub_back = [  ##Candidate issues
        # Background of issues
        "pro_gfi_ratio",
        "pro_gfi_num",
        "proclspr",
        "crtclsissnum",
        "pro_star",
        "openiss",
        "openissratio",
        "contributornum",
        "procmt",
        "rptcmt",
        "rptiss",
        "rptpr",
        "rptpronum",
        "rptallcmt",
        "rptalliss",
        "rptallpr",
        "rpt_reviews_num_all",
        "rpt_max_stars_commit",
        "rpt_max_stars_issue",
        "rpt_max_stars_pull",
        "rpt_max_stars_review",
        "rptisnew",
        "rpt_gfi_ratio",  #
        "ownercmt",
        "owneriss",
        "ownerpr",
        "ownerpronum",
        "ownerallcmt",
        "owneralliss",
        "ownerallpr",
        "owner_reviews_num_all",
        "owner_max_stars_commit",
        "owner_max_stars_issue",
        "owner_max_stars_pull",
        "owner_max_stars_review",
        "owner_gfi_ratio",
        "owner_gfi_num",
    ]

    xnames_LambdaMART = (
        xnames_sub_cumu
        + xnames_sub_act
        + xnames_sub_sen
        + xnames_sub_clscont
        + xnames_sub_domain
        + xnames_sub_isscont
        + xnames_sub_back
    )

    xnames_noSimi = (
        xnames_sub_cumu
        + xnames_sub_act
        + xnames_sub_sen
        + xnames_sub_isscont
        + xnames_sub_back
    )
    xnames_noDev = (
        xnames_sub_clscont + xnames_sub_domain + xnames_sub_isscont + xnames_sub_back
    )
    xnames_noIss = (
        xnames_sub_cumu
        + xnames_sub_act
        + xnames_sub_sen
        + xnames_sub_clscont
        + xnames_sub_domain
    )

    xnames_nocumu = (
        xnames_sub_act
        + xnames_sub_sen
        + xnames_sub_clscont
        + xnames_sub_domain
        + xnames_sub_isscont
        + xnames_sub_back
    )
    xnames_noact = (
        xnames_sub_cumu
        + xnames_sub_sen
        + xnames_sub_clscont
        + xnames_sub_domain
        + xnames_sub_isscont
        + xnames_sub_back
    )
    xnames_nosen = (
        xnames_sub_cumu
        + xnames_sub_act
        + xnames_sub_clscont
        + xnames_sub_domain
        + xnames_sub_isscont
        + xnames_sub_back
    )
    xnames_noclscontent = (
        xnames_sub_cumu
        + xnames_sub_act
        + xnames_sub_sen
        + xnames_sub_domain
        + xnames_sub_isscont
        + xnames_sub_back
    )
    xnames_nodomain = (
        xnames_sub_cumu
        + xnames_sub_act
        + xnames_sub_sen
        + xnames_sub_clscont
        + xnames_sub_isscont
        + xnames_sub_back
    )
    xnames_noisscontent = (
        xnames_sub_cumu
        + xnames_sub_act
        + xnames_sub_sen
        + xnames_sub_clscont
        + xnames_sub_domain
        + xnames_sub_back
    )
    xnames_noback = (
        xnames_sub_cumu
        + xnames_sub_act
        + xnames_sub_sen
        + xnames_sub_clscont
        + xnames_sub_domain
        + xnames_sub_isscont
    )

    cmtthre = 1
    path_name = os.path.dirname(__file__) + "/../data/dataset_"

    datasetname = "simcse"
    model_list = ["LambdaMART"]
    ratio1lsts = []
    ratio3lsts = []
    ratio5lsts = []
    ratio10lsts = []
    firsthitmedianlsts = []
    for model_name in model_list:
        ratio1lst = []
        ratio3lst = []
        ratio5lst = []
        ratio10lst = []
        firsthitmedianlst = []
        for dataset_fold in [
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        ]:
            datasetlst = []
            for i in range(dataset_fold - 1):
                datasetlst.append(
                    pd.read_pickle(
                        path_name + "_" + str(cmtthre) + "_" + str(i) + ".pkl"
                    )
                )
            training_set = pd.concat(datasetlst, axis=0)
            valid_set = pd.read_pickle(
                path_name + str(cmtthre) + "_" + str(dataset_fold - 1) + ".pkl"
            )
            test_set = pd.read_pickle(
                path_name + str(cmtthre) + "_" + str(dataset_fold) + ".pkl"
            )
            metrics = get_lamb_metrics(
                training_set, valid_set, test_set, idname, xnames_LambdaMART
            )

            if metrics is None:
                continue
            ratio1lst.append(metrics[0])
            ratio3lst.append(metrics[1])
            ratio5lst.append(metrics[2])
            ratio10lst.append(metrics[3])
            firsthitmedianlst.append(metrics[4])
        ratio1lsts.append(ratio1lst)
        ratio3lsts.append(ratio3lst)
        ratio5lsts.append(ratio5lst)
        ratio10lsts.append(ratio10lst)
        firsthitmedianlsts.append(firsthitmedianlst)

    for i in range(len(model_list)):
        print(
            model_list[i],
            np.mean(ratio1lsts[i]),
            np.mean(ratio3lsts[i]),
            np.mean(ratio5lsts[i]),
            np.mean(ratio10lsts[i]),
            np.mean(firsthitmedianlsts[i]),
            np.median(ratio1lsts[i]),
            np.median(ratio3lsts[i]),
            np.median(ratio5lsts[i]),
            np.median(ratio10lsts[i]),
            np.median(firsthitmedianlsts[i]),
        )
    print("finish")
