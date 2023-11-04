import json
import os
import pandas as pd
import re
from textblob import TextBlob
from gensim.parsing.preprocessing import remove_stopwords
from decimal import Decimal, ROUND_HALF_UP
from gensim.parsing.preprocessing import stem_text
from gensim.parsing.preprocessing import strip_multiple_whitespaces
from gensim.parsing.preprocessing import strip_numeric
from gensim.parsing.preprocessing import strip_tags
from gensim.parsing.preprocessing import strip_non_alphanum
import torch
from transformers import AutoModel, AutoTokenizer
import numpy as np
import logging
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from textblob import TextBlob
from gensim.parsing.preprocessing import remove_stopwords
from decimal import Decimal, ROUND_HALF_UP
from gensim.parsing.preprocessing import stem_text
from gensim.parsing.preprocessing import strip_multiple_whitespaces
from gensim.parsing.preprocessing import strip_numeric
from gensim.parsing.preprocessing import strip_tags
from gensim.parsing.preprocessing import strip_non_alphanum
from transformers import AutoModel, AutoTokenizer
import multiprocessing as mp
import gc
import spacy
import traceback
from collections import Counter
import pymongo
import nltk


def count_code_number(str):
    p = re.compile(r"```.+?```", flags=re.S)
    return len(p.findall(str))


def delete_code(str):
    p = re.compile(r"```.+?```", flags=re.S)
    s = p.sub("", str)
    return " ".join(s.split())


def count_url(str):
    def notPic(s):
        if s.endswith("jpg") or s.endswith("jpeg") or s.endswith("png"):
            return False
        return True

    p = re.compile(r"http[:/\w\.]+")
    lst = list(filter(notPic, p.findall(str)))
    return len(lst)


def count_pic(str):
    p = re.compile(r"http[:/\w\.]+")

    def isPic(s):
        if s.endswith("jpg") or s.endswith("jpeg") or s.endswith("png"):
            return True
        return False

    lst = list(filter(isPic, p.findall(str)))
    return len(lst)


def delete_url(str):
    p = re.compile(r"http[:/\w\.]+")
    s = p.sub("", str)
    return " ".join(s.split())


def _count_code_snippets(s: str) -> int:
    p = re.compile(r"```.+?```", flags=re.S)
    if s is None or s == []:
        return 0
    return len(p.findall(s))


def _delete_code_snippets(s: str) -> str:
    if s is None or s == []:
        return ""
    p = re.compile(r"```.+?```", flags=re.S)
    s = p.sub("", s)
    # return " ".join(s.split())
    return s


def _count_urls(s: str) -> int:
    if s is None or s == []:
        return 0
    p = re.compile(r"http[:/\w\.]+")
    lst = list(
        filter(  # do not count images, this will be done in count_imgs()
            lambda s2: not (
                s2.endswith("jpg") or s2.endswith("jpeg") or s2.endswith("png")
            ),
            p.findall(s),
        )
    )
    return len(lst)


def _delete_urls(s: str) -> str:
    if s is None or s == []:
        return ""
    p = re.compile(r"http[:/\w\.]+")
    s = p.sub("", s)
    # return " ".join(s.split())
    return s


def _count_imgs(s: str) -> int:
    if s is None or s == []:
        return 0
    p = re.compile(r"http[:/\w\.]+")
    lst = list(
        filter(
            lambda s2: s2.endswith("jpg") or s2.endswith("jpeg") or s2.endswith("png"),
            p.findall(s),
        )
    )
    return len(lst)


def ifclsnew(clscmt):
    if clscmt < cmtthre:
        return 1
    else:
        return 0


def ltc(llst):
    if len(llst) > 500 and (max(llst) - min(llst)) > 1825 * 86400000:
        return 1


#'''


def count_event(dfall, s):
    dfall = dfall[s].values
    evtlst = []
    for i in dfall:
        dic = {}
        for j in range(len(i)):
            dic[j] = len(i[j])
        evtlst.append(dic)
    return pd.DataFrame(evtlst)


def getlabellist(events):
    return events[0]


def getsubsclist(events):
    return events[1]


def getallnum(userlst):
    return len(userlst)


def getsen(s):
    blob = TextBlob(s)
    return blob.sentiment.polarity


def count_text_len(s):
    return len(s.split())


def getqmark(s):
    return s.count("?")


def getemark(s):
    return s.count("!")


def len_text(s):
    s = remove_stopwords(s)
    return len(re.findall(r"\w+", s))


def ifallcmtnew(l):
    return int(l[5] < 100)


def getallcmt(l):
    return l[5]


def deci(data):
    return str(Decimal(data).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP))


def getlen(lst):
    return len(lst)


def update_rptcmt(lst):
    return lst[0]


def update_rptallcmt(lst):
    return lst[5]


def update_rptpronum(lst):
    return lst[4]


def update_rptfoll(lst):
    return lst[6]


def update_rptalliss(lst):
    return lst[7]


def update_rptiss(lst):
    return lst[2]


def update_rptallpr(lst):
    return lst[8]


def update_rptpr(lst):
    return lst[1]


def add_rptfolling(lst):
    return lst[3]


def get_clscmt(lst):
    return lst[1][0]


def get_clsallcmt(lst):
    return lst[1][4]


def get_clspronum(lst):
    return lst[1][3]


def get_clswatchpro(lst):
    return lst[1][7]


def get_clsalliss(lst):
    return lst[1][5]


def get_clsiss(lst):
    return lst[1][2]


def get_clsallpr(lst):
    return lst[1][6]


def get_clspr(lst):
    return lst[1][1]


def get_clstexts(lst):
    return lst[0]


def get_clsreadmenum(lst):
    return lst[0][8]


def get_clsprostopic(lst):
    return lst[0][9]


def get_clsissuelabels(lst):
    return lst[0][10]


def get_clsprlabels(lst):
    return lst[0][11]


def get_clscommentissuelabels(lst):
    return lst[0][16]


def get_clsprreview(lst):
    return lst[1][8]


def get_clsallprreview(lst):
    return lst[1][9]


def get_clsforkpronum(lst):
    return lst[1][10]


def get_clsorg(lst):
    return lst[1][11]


def get_clscomp(lst):
    return lst[1][12]


def get_clslife(lst):
    return lst[1][13]


def get_clsfollower(lst):
    return lst[1][14]


def get_clsfollowing(lst):
    return lst[1][15]


def get_clsonemonth_cmt(lst):
    return lst[1][16]


def get_clstwomonth_cmt(lst):
    return lst[1][17]


def get_clsthreemonth_cmt(lst):
    return lst[1][18]


def get_clsonemonth_pr(lst):
    return lst[1][19]


def get_clstwomonth_pr(lst):
    return lst[1][20]


def get_clsthreemonth_pr(lst):
    return lst[1][21]


def get_clsonemonth_iss(lst):
    return lst[1][22]


def get_clstwomonth_iss(lst):
    return lst[1][23]


def get_clsthreemonth_iss(lst):
    return lst[1][24]


def unfold(dfall, s):
    dfall = dfall[s].values
    lst = []
    for i in dfall:
        dic = {}
        for j in range(len(i)):
            dic[j] = i[j]
        lst.append(dic)
    return pd.DataFrame(lst)


def textencode(text):
    text = _delete_code_snippets(text)
    text = _delete_urls(text)
    text = strip_multiple_whitespaces(text)
    text = stem_text(text)
    text = remove_stopwords(text)
    text = strip_numeric(text)
    text = strip_tags(text)
    text = strip_non_alphanum(text)

    inputs = tokenizer(text, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        embeddings = model(
            **inputs, output_hidden_states=True, return_dict=True
        ).pooler_output
    return embeddings


def get_issue_sen(title, body):
    return getsen(title + body)


def cls_issue_sen_mean(clstexts):
    titles = clstexts[0]
    bodys = clstexts[1]
    lst = []
    for i in range(len(titles)):
        text = titles[i] + " " + bodys[i]
        lst.append([getsen(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_issue_sen_median(clstexts):
    titles = clstexts[0]
    bodys = clstexts[1]
    lst = []
    for i in range(len(titles)):
        text = titles[i] + " " + bodys[i]
        lst.append([getsen(text)])
    if lst == []:
        return 0
    else:
        return np.median(lst)


def cls_pr_sen_mean(clstexts):
    titles = clstexts[2]
    bodys = clstexts[3]
    lst = []
    for i in range(len(titles)):
        text = titles[i] + " " + bodys[i]
        lst.append([getsen(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_pr_sen_median(clstexts):
    titles = clstexts[2]
    bodys = clstexts[3]
    lst = []
    for i in range(len(titles)):
        text = titles[i] + " " + bodys[i]
        lst.append([getsen(text)])
    if lst == []:
        return 0
    else:
        return np.median(lst)


def emb_issue(title, body):
    return textencode(title + body)


def emb_cls_issue(clstexts):
    titles = clstexts[0]
    bodys = clstexts[1]
    lst = []
    for i in range(len(titles)):
        text = titles[i] + " " + bodys[i]
        lst.append([textencode(text)])
    return lst


def emb_cls_pr(clstexts):
    titles = clstexts[2]
    bodys = clstexts[3]
    lst = []
    for i in range(len(titles)):
        text = titles[i] + " " + bodys[i]
        lst.append([textencode(text)])
    return lst


def emb_cls_prreview(clstexts):
    titles = clstexts[12]
    bodys = clstexts[13]
    lst = []
    for i in range(len(titles)):
        text = titles[i] + " " + bodys[i]
        lst.append([textencode(text)])
    return lst


def emb_cls_commentissue(clstexts):
    titles = clstexts[14]
    bodys = clstexts[15]
    lst = []
    for i in range(len(titles)):
        text = titles[i] + " " + bodys[i]
        lst.append([textencode(text)])
    return lst


def emb_cls_cmt(clstexts):
    texts = clstexts[4]
    lst = []
    for i in texts:
        lst.append([textencode(i)])
    return lst


def emb_cls_pro(clstexts):
    texts = clstexts[5]
    lst = []
    for i in texts:
        lst.append([textencode(i)])
    return lst


def emb_cls_readme(clstexts):
    texts = clstexts[7]
    lst = []
    for i in texts:
        if len(i) > 0:
            lst.append([textencode(i["text"])])
    return lst


def cls_iss_count_code_number_mean(clstexts):
    bodys = clstexts[1]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        lst.append([count_code_number(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_iss_count_url_mean(clstexts):
    bodys = clstexts[1]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        lst.append([count_url(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_iss_count_pic_mean(clstexts):
    bodys = clstexts[1]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        lst.append([count_pic(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_iss_count_title_len_mean(clstexts):
    titles = clstexts[0]
    lst = []
    for i in range(len(titles)):
        text = titles[i]
        lst.append([count_text_len(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_iss_count_body_len_mean(clstexts):
    bodys = clstexts[1]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        text = delete_code(text)
        text = delete_url(text)
        lst.append([count_text_len(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_iss_count_code_number_median(clstexts):
    bodys = clstexts[1]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        lst.append([count_code_number(text)])
    if lst == []:
        return 0
    else:
        return np.median(lst)


def cls_iss_count_url_median(clstexts):
    bodys = clstexts[1]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        lst.append([count_url(text)])
    if lst == []:
        return 0
    else:
        return np.median(lst)


def cls_iss_count_pic_median(clstexts):
    bodys = clstexts[1]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        lst.append([count_pic(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_iss_count_title_len_median(clstexts):
    titles = clstexts[0]
    lst = []
    for i in range(len(titles)):
        text = titles[i]
        lst.append([count_text_len(text)])
    if lst == []:
        return 0
    else:
        return np.median(lst)


def cls_iss_count_body_len_median(clstexts):
    bodys = clstexts[1]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        text = delete_code(text)
        text = delete_url(text)
        lst.append([count_text_len(text)])
    if lst == []:
        return 0
    else:
        return np.median(lst)


def cls_pr_count_code_number_mean(clstexts):
    bodys = clstexts[3]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        lst.append([count_code_number(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_pr_count_url_mean(clstexts):
    bodys = clstexts[3]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        lst.append([count_url(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_pr_count_pic_mean(clstexts):
    bodys = clstexts[3]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        lst.append([count_pic(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_pr_count_title_len_mean(clstexts):
    titles = clstexts[2]
    lst = []
    for i in range(len(titles)):
        text = titles[i]
        lst.append([count_text_len(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_pr_count_body_len_mean(clstexts):
    bodys = clstexts[3]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        text = delete_code(text)
        text = delete_url(text)
        lst.append([count_text_len(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_pr_count_code_number_median(clstexts):
    bodys = clstexts[3]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        lst.append([count_code_number(text)])
    if lst == []:
        return 0
    else:
        return np.median(lst)


def cls_pr_count_url_median(clstexts):
    bodys = clstexts[3]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        lst.append([count_url(text)])
    if lst == []:
        return 0
    else:
        return np.median(lst)


def cls_pr_count_pic_median(clstexts):
    bodys = clstexts[3]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        lst.append([count_pic(text)])
    if lst == []:
        return 0
    else:
        return np.mean(lst)


def cls_pr_count_title_len_median(clstexts):
    titles = clstexts[2]
    lst = []
    for i in range(len(titles)):
        text = titles[i]
        lst.append([count_text_len(text)])
    if lst == []:
        return 0
    else:
        return np.median(lst)


def cls_pr_count_body_len_median(clstexts):
    bodys = clstexts[3]
    lst = []
    for i in range(len(bodys)):
        text = bodys[i]
        text = delete_code(text)
        text = delete_url(text)
        lst.append([count_text_len(text)])
    if lst == []:
        return 0
    else:
        return np.median(lst)


def get_proidenti(owner, name, number):
    return owner + name + str(number)


def cal_feature():
    global fold
    current_work_dir = os.path.dirname(__file__)

    with open(current_work_dir + "/../data/personalizeddata.json") as f:
        issuestr = json.load(f)
    issuedata = issuestr["0"]
    lst = []
    for i in range(len(issuedata)):
        lst.append(issuedata[str(i)])
    dfall = pd.DataFrame(lst)

    dfall["proidenti"] = dfall.apply(
        lambda row: get_proidenti(row["owner"], row["name"], row["number"]), axis=1
    )
    dfall.reset_index(drop=True, inplace=True)

    fold = 5
    indlist = range(len(dfall))
    n = int(len(dfall) / fold) + 1
    b = [indlist[i : i + n] for i in range(0, len(indlist), n)]

    existiss = []
    existdf = pd.DataFrame()
    if os.path.exists(current_work_dir + "/../data/processeddata" + str(0) + ".pkl"):
        for fnum in range(fold):
            dffnum = pd.read_pickle(
                current_work_dir + "/../data/processeddata" + str(fnum) + ".pkl"
            )
            existiss.extend(dffnum["proidenti"].values.tolist())
            dffnum = pd.read_pickle(
                os.path.dirname(__file__)
                + "/../data/processeddata"
                + str(fnum)
                + ".pkl"
            )
            existdf = pd.concat([existdf, dffnum], axis=0)

    for fnum in range(fold):
        rangelst = b[fnum]
        df = dfall.iloc[rangelst]
        df = df.copy()
        matching_rows = df[df["proidenti"].isin(existiss)]
        matching_proidenti_values = matching_rows["proidenti"].tolist()
        matching_rows = existdf[existdf["proidenti"].isin(matching_proidenti_values)]
        matchingdf = pd.DataFrame(matching_rows)

        df = df[~df["proidenti"].isin(existiss)]

        df.reset_index(drop=True, inplace=True)

        df["cls_isnew"] = df["clscmt"].apply(ifclsnew)

        df["clsallcmt"] = df["clsdata"].apply(get_clsallcmt)
        df["clspronum"] = df["clsdata"].apply(get_clspronum)
        df["clswatchpro"] = df["clsdata"].apply(get_clswatchpro)
        df["clsalliss"] = df["clsdata"].apply(get_clsalliss)
        df["clsiss"] = df["clsdata"].apply(get_clsiss)
        df["clsallpr"] = df["clsdata"].apply(get_clsallpr)
        df["clspr"] = df["clsdata"].apply(get_clspr)
        df["clstexts"] = df["clsdata"].apply(get_clstexts)

        df["clsreadmeemb"] = df["clstexts"].apply(emb_cls_readme)
        df["clsprreviewemb"] = df["clstexts"].apply(emb_cls_prreview)
        df["clscommentissueemb"] = df["clstexts"].apply(emb_cls_commentissue)

        df["clsreadmenum"] = df["clsdata"].apply(get_clsreadmenum)
        df["clsprostopic"] = df["clsdata"].apply(get_clsprostopic)
        df["clsissuelabels"] = df["clsdata"].apply(get_clsissuelabels)
        df["clsprlabels"] = df["clsdata"].apply(get_clsprlabels)
        df["clscommentissuelabels"] = df["clsdata"].apply(get_clscommentissuelabels)

        df["clsprreview"] = df["clsdata"].apply(get_clsprreview)
        df["clsallprreview"] = df["clsdata"].apply(get_clsallprreview)
        df["clsforkpronum"] = df["clsdata"].apply(get_clsforkpronum)
        df["clsorg"] = df["clsdata"].apply(get_clsorg)
        df["clscomp"] = df["clsdata"].apply(get_clscomp)
        df["clslife"] = df["clsdata"].apply(get_clslife)
        df["clsfollower"] = df["clsdata"].apply(get_clsfollower)
        df["clsfollowing"] = df["clsdata"].apply(get_clsfollowing)
        df["clsonemonth_cmt"] = df["clsdata"].apply(get_clsonemonth_cmt)
        df["clstwomonth_cmt"] = df["clsdata"].apply(get_clstwomonth_cmt)
        df["clsthreemonth_cmt"] = df["clsdata"].apply(get_clsthreemonth_cmt)
        df["clsonemonth_pr"] = df["clsdata"].apply(get_clsonemonth_pr)
        df["clstwomonth_pr"] = df["clsdata"].apply(get_clstwomonth_pr)
        df["clsthreemonth_pr"] = df["clsdata"].apply(get_clsthreemonth_pr)
        df["clsonemonth_iss"] = df["clsdata"].apply(get_clsonemonth_iss)
        df["clstwomonth_iss"] = df["clsdata"].apply(get_clstwomonth_iss)
        df["clsthreemonth_iss"] = df["clsdata"].apply(get_clsthreemonth_iss)
        del df["clsdata"]

        df["issuesen"] = df.apply(
            lambda row: get_issue_sen(row["title"], row["body"]), axis=1
        )
        df["clsissuesenmean"] = df["clstexts"].apply(cls_issue_sen_mean)
        df["clsissuesenmedian"] = df["clstexts"].apply(cls_issue_sen_median)
        df["clsprsenmean"] = df["clstexts"].apply(cls_pr_sen_mean)
        df["clsprsenmedian"] = df["clstexts"].apply(cls_pr_sen_median)

        df["clsissue_NumOfCode_mean"] = df["clstexts"].apply(
            cls_iss_count_code_number_mean
        )
        df["clsissue_NumOfUrls_mean"] = df["clstexts"].apply(cls_iss_count_url_mean)
        df["clsissue_NumOfPics_mean"] = df["clstexts"].apply(cls_iss_count_pic_mean)
        df["clsissue_LengthOfTitle_mean"] = df["clstexts"].apply(
            cls_iss_count_title_len_mean
        )
        df["clsissue_LengthOfDescription_mean"] = df["clstexts"].apply(
            cls_iss_count_body_len_mean
        )

        df["clsissue_NumOfCode_median"] = df["clstexts"].apply(
            cls_iss_count_code_number_median
        )
        df["clsissue_NumOfUrls_median"] = df["clstexts"].apply(cls_iss_count_url_median)
        df["clsissue_NumOfPics_median"] = df["clstexts"].apply(cls_iss_count_pic_median)
        df["clsissue_LengthOfTitle_median"] = df["clstexts"].apply(
            cls_iss_count_title_len_median
        )
        df["clsissue_LengthOfDescription_median"] = df["clstexts"].apply(
            cls_iss_count_body_len_median
        )

        df["clspr_NumOfCode_mean"] = df["clstexts"].apply(cls_pr_count_code_number_mean)
        df["clspr_NumOfUrls_mean"] = df["clstexts"].apply(cls_pr_count_url_mean)
        df["clspr_NumOfPics_mean"] = df["clstexts"].apply(cls_pr_count_pic_mean)
        df["clspr_LengthOfTitle_mean"] = df["clstexts"].apply(
            cls_pr_count_title_len_mean
        )
        df["clspr_LengthOfDescription_mean"] = df["clstexts"].apply(
            cls_pr_count_body_len_mean
        )

        df["clspr_NumOfCode_median"] = df["clstexts"].apply(
            cls_pr_count_code_number_median
        )
        df["clspr_NumOfUrls_median"] = df["clstexts"].apply(cls_pr_count_url_median)
        df["clspr_NumOfPics_median"] = df["clstexts"].apply(cls_pr_count_pic_median)
        df["clspr_LengthOfTitle_median"] = df["clstexts"].apply(
            cls_pr_count_title_len_median
        )
        df["clspr_LengthOfDescription_median"] = df["clstexts"].apply(
            cls_pr_count_body_len_median
        )

        # texts embedding
        df["issueemb"] = df.apply(
            lambda row: emb_issue(row["title"], row["body"]), axis=1
        )

        df["readmeemb"] = df["readme"].apply(textencode)
        df["prodesemb"] = df["prodescription"].apply(textencode)
        df["clsissueemb"] = df["clstexts"].apply(emb_cls_issue)
        df["clspremb"] = df["clstexts"].apply(emb_cls_pr)
        df["clscmtemb"] = df["clstexts"].apply(emb_cls_cmt)
        df["clsprodesemb"] = df["clstexts"].apply(emb_cls_pro)

        df = pd.concat([df, matchingdf], axis=0)

        df.to_pickle(current_work_dir + "/../data/processeddata" + str(fnum) + ".pkl")
        logging.info(fnum)


def lemma(text):
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc])


def ifclsnew(clscmt):
    if clscmt < cmtthre:
        return 1
    else:
        return 0


def has_clscomp(clscomp):
    if clscomp is None:
        return 0
    else:
        return 1


def get_negdf(s):
    try:
        fts = clsfeatures + ["issuet", "clst", "owner", "name", "number"]
        oneclsdata = df.loc[[subdfgfi[s]], fts]
        oneclsdata = oneclsdata.copy()
        oneclsdata.reset_index(drop=True, inplace=True)
        clsname = oneclsdata.at[0, "clsname"]
        startt = oneclsdata.at[0, "issuet"]
        endt = oneclsdata.at[0, "clst"]
        owner = oneclsdata.at[0, "owner"]
        name = oneclsdata.at[0, "name"]
        number = oneclsdata.at[0, "number"]
        issgroupid = owner + name + str(number)
        oneclsdata.drop(
            ["clst", "issuet", "owner", "name", "number"], axis=1, inplace=True
        )
        negiss = []

        for negi in range(len(subdf)):
            if (
                (df.at[subdf[negi], "owner"] == owner)
                & (df.at[subdf[negi], "name"] == name)
                & (
                    (df.at[subdf[negi], "clst"] >= endt)
                    & (df.at[subdf[negi], "issuet"] <= endt)
                )
                & (df.at[subdf[negi], "number"] != number)
                & (df.at[subdf[negi], "clsname"] != clsname)
            ):
                negiss.append(df.loc[[subdf[negi]]])
            if len(negiss) > 48:  #
                break
        print(len(negiss))
        if len(negiss) < negsampnum:
            logging.info("skip")
            return None, len(negiss) + 1
        negiss = pd.concat(negiss, axis=0)
        negiss.reset_index(drop=True, inplace=True)
        randind = list(range(len(negiss)))
        onenegdfset = []
        for ind in randind:
            oneissdata = negiss.loc[[ind], issfeatures]
            oneissdata.reset_index(drop=True, inplace=True)
            oneclsdata.reset_index(drop=True, inplace=True)
            onenegdf = pd.concat([oneissdata, oneclsdata], axis=1)
            onenegdf.insert(0, "match", value=0)
            onenegdf.insert(0, "issgroupid", value=issgroupid)

            isslabelsnum = [
                onenegdf["buglabelnum"].values.tolist()[0],
                onenegdf["featurelabelnum"].values.tolist()[0],
                onenegdf["testlabelnum"].values.tolist()[0],
                onenegdf["buildlabelnum"].values.tolist()[0],
                onenegdf["doclabelnum"].values.tolist()[0],
                onenegdf["codinglabelnum"].values.tolist()[0],
                onenegdf["enhancelabelnum"].values.tolist()[0],
                onenegdf["gfilabelnum"].values.tolist()[0],
                onenegdf["mediumlabelnum"].values.tolist()[0],
                onenegdf["majorlabelnum"].values.tolist()[0],
                onenegdf["triagedlabelnum"].values.tolist()[0],
                onenegdf["untriagedlabelnum"].values.tolist()[0],
            ]
            adddf = add_features(
                onenegdf["issueemb"].values.tolist()[0],
                onenegdf["clsissueemb"].values.tolist()[0],
                onenegdf["prodesemb"].values.tolist()[0],
                onenegdf["clspremb"].values.tolist()[0],
                onenegdf["clscmtemb"].values.tolist()[0],
                onenegdf["clsprodesemb"].values.tolist()[0],
                onenegdf["title"].values.tolist()[0],
                onenegdf["body"].values.tolist()[0],
                onenegdf["clstexts"].values.tolist()[0],
                onenegdf["prodescription"].values.tolist()[0],
                onenegdf["readmeemb"].values.tolist()[0],
                onenegdf["clsreadmeemb"].values.tolist()[0],
                onenegdf["clsprreviewemb"].values.tolist()[0],
                onenegdf["clscommentissueemb"].values.tolist()[0],
                onenegdf["readme"].values.tolist()[0],
                onenegdf["topics"].values.tolist()[0],
                onenegdf["clsprostopic"].values.tolist()[0],
                onenegdf["clsissuelabels"].values.tolist()[0],
                onenegdf["clsprlabels"].values.tolist()[0],
                onenegdf["clscommentissuelabels"].values.tolist()[0],
                isslabelsnum,
                onenegdf["lan"].values.tolist()[0],
                clsname,
                startt,
                onenegdf["clsreadmenum"].values.tolist()[0],
            )
            onenegdf.reset_index(drop=True, inplace=True)
            adddf.reset_index(drop=True, inplace=True)
            onenegdf = pd.concat([onenegdf, adddf], axis=1)
            onenegdfset.append(onenegdf)

        fts = clsfeatures + issfeatures
        rawiss = df.loc[[subdfgfi[s]], fts]
        rawiss.insert(0, "match", value=1)
        rawiss.insert(0, "issgroupid", value=issgroupid)
        isslabelsnum = [
            rawiss["buglabelnum"].values.tolist()[0],
            rawiss["featurelabelnum"].values.tolist()[0],
            rawiss["testlabelnum"].values.tolist()[0],
            rawiss["buildlabelnum"].values.tolist()[0],
            rawiss["doclabelnum"].values.tolist()[0],
            rawiss["codinglabelnum"].values.tolist()[0],
            rawiss["enhancelabelnum"].values.tolist()[0],
            rawiss["gfilabelnum"].values.tolist()[0],
            rawiss["mediumlabelnum"].values.tolist()[0],
            rawiss["majorlabelnum"].values.tolist()[0],
            rawiss["triagedlabelnum"].values.tolist()[0],
            rawiss["untriagedlabelnum"].values.tolist()[0],
        ]
        adddf = add_features(
            rawiss["issueemb"].values.tolist()[0],
            rawiss["clsissueemb"].values.tolist()[0],
            rawiss["prodesemb"].values.tolist()[0],
            rawiss["clspremb"].values.tolist()[0],
            rawiss["clscmtemb"].values.tolist()[0],
            rawiss["clsprodesemb"].values.tolist()[0],
            rawiss["title"].values.tolist()[0],
            rawiss["body"].values.tolist()[0],
            rawiss["clstexts"].values.tolist()[0],
            rawiss["prodescription"].values.tolist()[0],
            rawiss["readmeemb"].values.tolist()[0],
            rawiss["clsreadmeemb"].values.tolist()[0],
            rawiss["clsprreviewemb"].values.tolist()[0],
            rawiss["clscommentissueemb"].values.tolist()[0],
            rawiss["readme"].values.tolist()[0],
            rawiss["topics"].values.tolist()[0],
            rawiss["clsprostopic"].values.tolist()[0],
            rawiss["clsissuelabels"].values.tolist()[0],
            rawiss["clsprlabels"].values.tolist()[0],
            rawiss["clscommentissuelabels"].values.tolist()[0],
            isslabelsnum,
            rawiss["lan"].values.tolist()[0],
            clsname,
            startt,
            rawiss["clsreadmenum"].values.tolist()[0],
        )
        rawiss.reset_index(drop=True, inplace=True)
        adddf.reset_index(drop=True, inplace=True)
        rawiss = pd.concat([rawiss, adddf], axis=1)
        onenegdfset = pd.concat(onenegdfset, axis=0)
        rawiss.reset_index(drop=True, inplace=True)
        onenegdfset.reset_index(drop=True, inplace=True)
        onenegdfset = pd.concat([onenegdfset, rawiss], axis=0)
        onenegdfset.reset_index(drop=True, inplace=True)
        del onenegdfset["issueemb"]
        del onenegdfset["clsissueemb"]
        del onenegdfset["prodesemb"]
        del onenegdfset["clspremb"]
        del onenegdfset["clscmtemb"]
        del onenegdfset["clsprodesemb"]
        del onenegdfset["title"]
        del onenegdfset["body"]
        del onenegdfset["clstexts"]
        del onenegdfset["prodescription"]
        del onenegdfset["readmeemb"]
        del onenegdfset["clsreadmeemb"]
        del onenegdfset["clsprreviewemb"]
        del onenegdfset["clscommentissueemb"]
        del onenegdfset["readme"]
        del onenegdfset["topics"]
        del onenegdfset["clsprostopic"]
        del onenegdfset["clsissuelabels"]
        del onenegdfset["clsprlabels"]
        del onenegdfset["clscommentissuelabels"]
        del onenegdfset["lan"]
        del onenegdfset["clsreadmenum"]
        gc.collect()
        logging.info(issgroupid)
    except Exception as ex:
        logging.error(f"Error: {ex}")
        return None, len(negiss) + 1
    return onenegdfset, len(negiss) + 1


def readme_cos_sim(iss, clsiss, clsreadmenum):
    sim = []
    if isinstance(clsiss, list) and len(clsiss) > 0:
        for i in range(len(clsiss)):
            sim.extend([cosine_dis(iss, clsiss[i][0])] * clsreadmenum[i])
        sim = [x for x in sim if x is not None]
    if sim == []:
        return 0, 0
    else:
        return sum(sim), np.mean(sim)


def cos_sim(iss, clsiss):
    sim = []
    if isinstance(clsiss, list) and len(clsiss) > 0:
        for i in clsiss:
            sim.append(cosine_dis(iss, i[0]))
        sim = [x for x in sim if x is not None]
    if sim == []:
        return 0, 0
    else:
        return sum(sim), np.mean(sim)


def cosine_dis(emb0, emb1):
    try:
        a = cosine_similarity(emb0, emb1)[0][0]
    except:
        return None
    return a


def readme_euc_sim(iss, clsiss, clsreadmenum):
    sim = []
    if isinstance(clsiss, list) and len(clsiss) > 0:
        for i in range(len(clsiss)):
            sim.extend([euclidean_dis(iss, clsiss[i][0])] * clsreadmenum[i])
        sim = [1 / (1 + x) for x in sim if x is not None]
    if sim == []:
        return 0, 0
    else:
        return sum(sim), np.mean(sim)


def euc_sim(iss, clsiss):
    sim = []
    if isinstance(clsiss, list) and len(clsiss) > 0:
        for i in clsiss:
            sim.append(euclidean_dis(iss, i[0]))
        sim = [1 / (1 + x) for x in sim if x is not None]
    if sim == []:
        return 0, 0
    else:
        return sum(sim), np.mean(sim)


def euclidean_dis(emb0, emb1):
    try:
        a = euclidean_distances(emb0, emb1)[0][0]
    except:
        return None
    return a


def jaccard_sim(t0, t1):
    try:
        t0 = lemma(t0)
        t1 = lemma(t1)
        a = set(t0.split())
        b = set(t1.split())
        c = a.intersection(b)
    except:
        return 0
    return float(len(c)) / (len(a) + len(b) - len(c))


def iss_jaccard_sim(title, body, clstexts):
    proiss = title + body
    cls_titles = clstexts[0]
    cls_bodys = clstexts[1]
    s = []
    for i in range(len(cls_titles)):
        text = cls_titles[i] + " " + cls_bodys[i]
        s.append(jaccard_sim(proiss, text))
    if s == []:
        return 0, 0
    else:
        return sum(s), np.mean(s)


def pr_jaccard_sim(title, body, clstexts):
    proiss = title + body
    cls_titles = clstexts[2]
    cls_bodys = clstexts[3]
    s = []
    for i in range(len(cls_titles)):
        text = cls_titles[i] + " " + cls_bodys[i]
        s.append(jaccard_sim(proiss, text))
    if s == []:
        return 0, 0
    else:
        return sum(s), np.mean(s)


def cmt_jaccard_sim(title, body, clstexts):
    proiss = title + body
    text = clstexts[4]
    s = []
    for i in range(len(text)):
        s.append(jaccard_sim(proiss, text[i]))
    if s == []:
        return 0, 0
    else:
        return sum(s), np.mean(s)


def pro_jaccard_sim(prodescription, clstexts):
    text = clstexts[5]
    if prodescription is None:
        return 0
    s = []
    for i in range(len(text)):
        if text[i] is None:
            continue
        s.append(jaccard_sim(prodescription, text[i]))
    if s == []:
        return 0, 0
    else:
        return sum(s), np.mean(s)


def readme_jaccard_sim(readme, clstexts):
    text = clstexts[7]
    s = []
    for i in range(len(text)):
        s.append(jaccard_sim(readme, text[i]))
    if s == []:
        return 0, 0
    else:
        return sum(s), np.mean(s)


def prreview_jaccard_sim(title, body, clstexts):
    proiss = title + body
    cls_titles = clstexts[12]
    cls_bodys = clstexts[13]
    s = []
    for i in range(len(cls_titles)):
        text = cls_titles[i] + " " + cls_bodys[i]
        s.append(jaccard_sim(proiss, text))
    if s == []:
        return 0, 0
    else:
        return sum(s), np.mean(s)


def commentissue_jaccard_sim(title, body, clstexts):
    proiss = title + body
    cls_titles = clstexts[14]
    cls_bodys = clstexts[15]
    s = []
    for i in range(len(cls_titles)):
        text = cls_titles[i] + " " + cls_bodys[i]
        s.append(jaccard_sim(proiss, text))
    if s == []:
        return 0, 0
    else:
        return sum(s), np.mean(s)


def get_clsname(owner, name, number):
    myclient = pymongo.MongoClient("mongodb://localhost:27017/", connect=False)
    resolved_issue = myclient["gfibot"]["resolved_issue"]
    issue = resolved_issue.find_one({"owner": owner, "name": name, "number": number})
    closer = issue["resolver"]
    myclient.close()
    return closer


def textprocess(text):
    text = strip_multiple_whitespaces(text)
    text = stem_text(text)
    text = remove_stopwords(text)
    text = strip_numeric(text)
    text = strip_tags(text)
    text = strip_non_alphanum(text)
    return text


def label_sim(labels, isslab):
    keyword_rules = {
        "bug": ["bug"],
        "feature": ["feature"],
        "test": ["test", "testing"],
        "build": ["ci", "build"],
        "doc": ["doc", "document", "documentation"],
        "coding": ["code", "coding", "program", "programming"],
        "enhance": ["enhance", "enhancement"],
        "gfi": [
            "easy",
            "starter",
            "newbie",
            "beginner",
            "starter",
            "minor",
            "novice",
            ("good", "first"),
            ("low", "fruit"),
            ("effort", "low"),
            ("first", "time"),
            ("first", "timer"),
            ("first", "pr"),
            ("up", "for", "grab"),
        ],
        "medium": ["medium", "intermediate"],
        "major": [
            "important",
            "major",
            "breaking",
            "difficult",
            "hard",
            "core",
            "serious",
            ("priority", "p1"),
            ("priority", "high"),
            ("priority", "critical"),
        ],
        "triaged": [
            "triaged",
            "triage",
            "progress",
            "haspr",
            "fixed",
            "wontfix",
            ("ha", "pr"),
            ("ha", "fix"),
        ],
        "untriaged": [
            "untriaged",
            ("need", "triage"),
            ("needed", "triage"),
            ("no", "triage"),
        ],
    }

    isssum = 0
    for i in labels:
        label_cat = Counter()
        lemmatizer = nltk.stem.WordNetLemmatizer()
        for label in i:
            words = re.compile(r"\w+").findall(label.lower().replace("_", " "))
            words = [lemmatizer.lemmatize(w) for w in words]
            for cat, rules in keyword_rules.items():
                match = 0
                for rule in rules:
                    if isinstance(rule, (tuple, list)):
                        if all(word in words for word in rule):
                            match = 1
                    elif rule in words:
                        match = 1
                    elif any(rule in w for w in words):
                        match = 1
                label_cat[cat] += match
        result_list = sorted(label_cat.items(), key=lambda item: item[1], reverse=True)
        result_list = [
            result_list[x][1] > 0 and isslab[x] > 0 for x in range(len(result_list))
        ]
        if sum(result_list) > 0:
            isssum += 1
    if len(labels) == 0:
        issratio = 0
    else:
        issratio = isssum / len(labels)
    return isssum, issratio


def topic_sim(clstopics, topics):
    topicsum = 0
    for i in clstopics:
        for t in i:
            if t in topics:
                topicsum += 1
                break
    if len(clstopics) == 0:
        topicratio = 0
    else:
        topicratio = topicsum / len(clstopics)
    return topicsum, topicratio


def get_texts(lst):
    return lst[0]


def add_features(
    issueemb,
    clsissueemb,
    prodesemb,
    clspremb,
    clscmtemb,
    clsprodesemb,
    title,
    body,
    clstexts,
    prodescription,
    readmeemb,
    clsreadmeemb,
    clsprreviewemb,
    clscommentissueemb,
    readme,
    topics,
    clsprostopic,
    clsissuelabels,
    clsprlabels,
    clscommentissuelabels,
    isslabelsnum,
    lan,
    clsname,
    startt,
    clsreadmenum,
):
    try:
        clshisdf = df[(df["clsname"] == clsname) & (df["clst"] < startt)]
        clssolvedissueemb = clshisdf["issueemb"].values.tolist()
        clssolvedissueemb = [[i] for i in clssolvedissueemb]
        clshisdfisslabelsnum = [
            clshisdf["buglabelnum"].values.tolist(),
            clshisdf["featurelabelnum"].values.tolist(),
            clshisdf["testlabelnum"].values.tolist(),
            clshisdf["buildlabelnum"].values.tolist(),
            clshisdf["doclabelnum"].values.tolist(),
            clshisdf["codinglabelnum"].values.tolist(),
            clshisdf["enhancelabelnum"].values.tolist(),
            clshisdf["gfilabelnum"].values.tolist(),
            clshisdf["mediumlabelnum"].values.tolist(),
            clshisdf["majorlabelnum"].values.tolist(),
            clshisdf["triagedlabelnum"].values.tolist(),
            clshisdf["untriagedlabelnum"].values.tolist(),
        ]
        clshissolvisslabs = []
        for m in range(len(clshisdfisslabelsnum[0])):
            onesolvedisslab = []
            if clshisdfisslabelsnum[0][m] > 0:
                onesolvedisslab.append("bug")
            elif clshisdfisslabelsnum[1][m] > 0:
                onesolvedisslab.append("feature")
            elif clshisdfisslabelsnum[2][m] > 0:
                onesolvedisslab.append("test")
            elif clshisdfisslabelsnum[3][m] > 0:
                onesolvedisslab.append("build")
            elif clshisdfisslabelsnum[4][m] > 0:
                onesolvedisslab.append("doc")
            elif clshisdfisslabelsnum[5][m] > 0:
                onesolvedisslab.append("code")
            elif clshisdfisslabelsnum[6][m] > 0:
                onesolvedisslab.append("enhance")
            elif clshisdfisslabelsnum[7][m] > 0:
                onesolvedisslab.append("easy")
            elif clshisdfisslabelsnum[8][m] > 0:
                onesolvedisslab.append("medium")
            elif clshisdfisslabelsnum[9][m] > 0:
                onesolvedisslab.append("major")
            elif clshisdfisslabelsnum[10][m] > 0:
                onesolvedisslab.append("triaged")
            elif clshisdfisslabelsnum[11][m] > 0:
                onesolvedisslab.append("untriaged")
            clshissolvisslabs.append(onesolvedisslab)

        solvedisscos_sim, solvedisscos_mean = cos_sim(issueemb, clssolvedissueemb)
        isscos_sim, isscos_mean = cos_sim(issueemb, clsissueemb)
        prcos_sim, prcos_mean = cos_sim(issueemb, clspremb)
        cmtcos_sim, cmtcos_mean = cos_sim(issueemb, clscmtemb)

        procos_sim, procos_mean = cos_sim(prodesemb, clsprodesemb)

        solvedisseuc_sim, solvedisseuc_mean = euc_sim(issueemb, clssolvedissueemb)
        isseuc_sim, isseuc_mean = euc_sim(issueemb, clsissueemb)
        preuc_sim, preuc_mean = euc_sim(issueemb, clspremb)
        cmteuc_sim, cmteuc_mean = euc_sim(issueemb, clscmtemb)
        proeuc_sim, proeuc_mean = euc_sim(prodesemb, clsprodesemb)

        solvedissjaccard_sim, solvedissjaccard_sim_mean = iss_jaccard_sim(
            title,
            body,
            [clshisdf["title"].values.tolist(), clshisdf["body"].values.tolist()],
        )
        issjaccard_sim, issjaccard_sim_mean = iss_jaccard_sim(title, body, clstexts)
        prjaccard_sim, prjaccard_sim_mean = pr_jaccard_sim(title, body, clstexts)
        cmtjaccard_sim, cmtjaccard_sim_mean = cmt_jaccard_sim(title, body, clstexts)
        projaccard_sim, projaccard_mean = pro_jaccard_sim(prodescription, clstexts)

        solvedissuelabel_sum, solvedissuelabel_ratio = label_sim(
            clshissolvisslabs, isslabelsnum
        )
        issuelabel_sum, issuelabel_ratio = label_sim(clsissuelabels, isslabelsnum)
        prlabel_sum, prlabel_ratio = label_sim(clsprlabels, isslabelsnum)
        commentissuelabel_sum, commentissuelabel_ratio = label_sim(
            clscommentissuelabels, isslabelsnum
        )

        readmecos_sim, readmecos_sim_mean = readme_cos_sim(
            readmeemb, clsreadmeemb, clsreadmenum
        )
        prreviewcos_sim, prreviewcos_sim_mean = cos_sim(issueemb, clsprreviewemb)
        commentissuecos_sim, commentissuecos_sim_mean = cos_sim(
            issueemb, clscommentissueemb
        )

        readmeeuc_sim, readmeeuc_sim_mean = readme_euc_sim(
            readmeemb, clsreadmeemb, clsreadmenum
        )
        prrevieweuc_sim, prrevieweuc_sim_mean = euc_sim(issueemb, clsprreviewemb)
        commentissueeuc_sim, commentissueeuc_sim_mean = euc_sim(
            issueemb, clscommentissueemb
        )

        readmejaccard_sim, readmejaccard_sim_mean = readme_jaccard_sim(readme, clstexts)
        prreviewjaccard_sim, prreviewjaccard_sim_mean = prreview_jaccard_sim(
            title, body, clstexts
        )
        (
            commentissuejaccard_sim,
            commentissuejaccard_sim_mean,
        ) = commentissue_jaccard_sim(title, body, clstexts)

        prostopic_sum, prostopic_ratio = topic_sim(clsprostopic, topics)
        lan_sim = clstexts[6].count(lan)

        return pd.DataFrame(
            {
                "solvedisscos_sim": solvedisscos_sim,
                "solvedisscos_mean": solvedisscos_mean,
                "solvedisseuc_sim": solvedisseuc_sim,
                "solvedisseuc_mean": solvedisseuc_mean,
                "solvedissjaccard_sim": solvedissjaccard_sim,
                "solvedissjaccard_sim_mean": solvedissjaccard_sim_mean,
                "solvedissuelabel_sum": solvedissuelabel_sum,
                "solvedissuelabel_ratio": solvedissuelabel_ratio,
                "isscos_sim": isscos_sim,
                "prcos_sim": prcos_sim,
                "cmtcos_sim": cmtcos_sim,
                "isseuc_sim": isseuc_sim,
                "preuc_sim": preuc_sim,
                "cmteuc_sim": cmteuc_sim,
                "issjaccard_sim": issjaccard_sim,
                "isseuc_mean": isseuc_mean,
                "cmtjaccard_sim": cmtjaccard_sim,
                "prjaccard_sim": prjaccard_sim,
                "isscos_mean": isscos_mean,
                "issjaccard_sim_mean": issjaccard_sim_mean,
                "cmteuc_mean": cmteuc_mean,
                "cmtcos_mean": cmtcos_mean,
                "cmtjaccard_sim_mean": cmtjaccard_sim_mean,
                "preuc_mean": preuc_mean,
                "prcos_mean": prcos_mean,
                "prjaccard_sim_mean": prjaccard_sim_mean,
                "issuelabel_sum": issuelabel_sum,
                "issuelabel_ratio": issuelabel_ratio,
                "prlabel_sum": prlabel_sum,
                "prlabel_ratio": prlabel_ratio,
                "commentissuelabel_sum": commentissuelabel_sum,
                "commentissuelabel_ratio": commentissuelabel_ratio,
                "procos_sim": procos_sim,
                "procos_mean": procos_mean,
                "proeuc_sim": proeuc_sim,
                "proeuc_mean": proeuc_mean,
                "projaccard_sim": projaccard_sim,
                "projaccard_mean": projaccard_mean,
                "readmecos_sim": readmecos_sim,
                "readmecos_sim_mean": readmecos_sim_mean,
                "prreviewcos_sim": prreviewcos_sim,
                "prreviewcos_sim_mean": prreviewcos_sim_mean,
                "commentissuecos_sim": commentissuecos_sim,
                "commentissuecos_sim_mean": commentissuecos_sim_mean,
                "readmeeuc_sim": readmeeuc_sim,
                "readmeeuc_sim_mean": readmeeuc_sim_mean,
                "prrevieweuc_sim": prrevieweuc_sim,
                "prrevieweuc_sim_mean": prrevieweuc_sim_mean,
                "commentissueeuc_sim": commentissueeuc_sim,
                "commentissueeuc_sim_mean": commentissueeuc_sim_mean,
                "readmejaccard_sim": readmejaccard_sim,
                "readmejaccard_sim_mean": readmejaccard_sim_mean,
                "prreviewjaccard_sim": prreviewjaccard_sim,
                "prreviewjaccard_sim_mean": prreviewjaccard_sim_mean,
                "commentissuejaccard_sim": commentissuejaccard_sim,
                "commentissuejaccard_sim_mean": commentissuejaccard_sim_mean,
                "prostopic_sum": prostopic_sum,
                "prostopic_ratio": prostopic_ratio,
                "lan_sim": lan_sim,
            },
            index=[0],
        )
    except Exception as ex:
        logging.error(f"Error: {ex}")
        logging.error(prodescription)
        logging.error(clstexts[5])
        traceback.print_exc()
        return None


def construct_dataset():
    global df, clsfeatures, issfeatures, subdfgfi, subdf

    issfeatures = [
        "pro_star",
        "procmt",
        "contributornum",
        "prodescription",
        "lan",
        "openiss",
        "issuet",
        "clst",
        "proclspr",
        "rptcmt",
        "rptallcmt",
        "rptpronum",
        "rptalliss",
        "rptiss",
        "rptallpr",
        "rptpr",
        "ownercmt",
        "ownerallcmt",
        "ownerpronum",
        "owneralliss",
        "owneriss",
        "ownerallpr",
        "ownerpr",
        "crtclsissnum",
        "openissratio",
        "clsisst",
        "title",
        "body",
        "NumOfCode",
        "NumOfUrls",
        "NumOfPics",
        "coleman_liau_index",
        "flesch_reading_ease",
        "flesch_kincaid_grade",
        "automated_readability_index",
        "LengthOfTitle",
        "LengthOfDescription",
        "rptisnew",
        "gfilabelnum",
        "buglabelnum",
        "testlabelnum",
        "buildlabelnum",
        "doclabelnum",
        "enhancelabelnum",
        "codinglabelnum",
        "featurelabelnum",
        "majorlabelnum",
        "mediumlabelnum",
        "untriagedlabelnum",
        "triagedlabelnum",
        "labelnum",
        "issuesen",
        "issueemb",
        "prodesemb",
        "rpt_reviews_num_all",
        "rpt_max_stars_commit",
        "rpt_max_stars_issue",
        "rpt_max_stars_pull",
        "rpt_max_stars_review",
        "rpt_gfi_ratio",
        "owner_reviews_num_all",
        "owner_max_stars_commit",
        "owner_max_stars_issue",
        "owner_max_stars_pull",
        "owner_max_stars_review",
        "owner_gfi_ratio",
        "owner_gfi_num",
        "pro_gfi_ratio",
        "pro_gfi_num",
        "owner",
        "name",
        "number",
        "readme",
        "readmeemb",
        "topics",
    ]
    clsfeatures = [
        "clsname",
        "clscmt",
        "cls_isnew",
        "clsallcmt",
        "clspronum",
        "clsalliss",
        "clsiss",
        "clsallpr",
        "clswatchpro",
        "clspr",
        "clstexts",
        "clsissueemb",
        "clspremb",
        "clscmtemb",
        "clsprodesemb",
        "clsreadmeemb",
        "clsprreviewemb",
        "clscommentissueemb",
        "clsreadmenum",
        "clsprostopic",
        "clsissuelabels",
        "clsprlabels",
        "clscommentissuelabels",
        "clsprreview",
        "clsallprreview",
        "clsforkpronum",
        "clsorg",
        "clscomp",
        "clslife",
        "clsfollower",
        "clsfollowing",
        "clsonemonth_cmt",
        "clstwomonth_cmt",
        "clsthreemonth_cmt",
        "clsonemonth_pr",
        "clstwomonth_pr",
        "clsthreemonth_pr",
        "clsonemonth_iss",
        "clstwomonth_iss",
        "clsthreemonth_iss",
        "clsissuesenmean",
        "clsissuesenmedian",
        "clsprsenmean",
        "clsprsenmedian",
    ]

    df = pd.DataFrame()
    for fnum in range(fold):
        dffnum = pd.read_pickle(
            os.path.dirname(__file__) + "/../data/processeddata" + str(fnum) + ".pkl"
        )
        df = pd.concat([df, dffnum], axis=0)

    df = df.sort_values(by=["clst"], ascending=True)
    df.reset_index(drop=True, inplace=True)
    del df["cls_isnew"]
    df["cls_isnew"] = df["clscmt"].apply(ifclsnew)
    dfgfi = df[df["cls_isnew"] == 1].index.tolist()

    gfisize = int((1 / 20) * len(dfgfi))
    datasets = []
    for i in range(20):
        if i == 0:
            datasets.append(
                list(
                    range(
                        0,
                        int(
                            (dfgfi[(i + 1) * gfisize - 1] + dfgfi[(i + 1) * gfisize])
                            / 2
                        ),
                    )
                )
            )
        elif i == 19:
            datasets.append(
                list(
                    range(
                        int((dfgfi[i * gfisize - 1] + dfgfi[i * gfisize]) / 2), len(df)
                    )
                )
            )
        else:
            datasets.append(
                list(
                    range(
                        int((dfgfi[i * gfisize - 1] + dfgfi[i * gfisize]) / 2),
                        int(
                            (dfgfi[(i + 1) * gfisize - 1] + dfgfi[(i + 1) * gfisize])
                            / 2
                        ),
                    )
                )
            )

    for i in range(len(datasets)):
        logging.info("fold")
        logging.info(i)
        subdf = datasets[i]
        subdfgfi = [item for item in subdf if item in dfgfi]

        indlist = range(len(subdfgfi))
        n = int(len(subdfgfi) / 50) + 1
        b = [list(indlist[i : i + n]) for i in range(0, len(indlist), n)]
        pklind = 0
        for indlst in b:
            logging.info("fold")
            logging.info(pklind)

            subindlist = [[subind] for subind in indlst]
            poolnum = 10
            with mp.Pool(poolnum) as pool:
                res = pool.starmap(get_negdf, subindlist)

            res = [r[0] for r in res if r[0] is not None]
            if len(res) > 0:
                res = pd.concat(res, axis=0)
                res.to_pickle(
                    os.path.dirname(__file__) + "/../data/res" + str(pklind) + ".pkl"
                )
                pklind += 1
                del res
                gc.collect()

        dflst = []
        for pkli in range(pklind):
            adf = pd.read_pickle(
                os.path.dirname(__file__) + "/../data/res" + str(pkli) + ".pkl"
            )
            dflst.append(adf)
        reslst = pd.concat(dflst, axis=0)

        reslst.reset_index(drop=True, inplace=True)
        reslst.to_pickle(
            os.path.dirname(__file__)
            + "/../data/dataset_"
            + str(cmtthre)
            + "_"
            + str(i)
            + ".pkl"
        )
        del reslst
        del dflst
        del adf
        gc.collect()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        "princeton-nlp/sup-simcse-bert-base-uncased"
    )
    model = AutoModel.from_pretrained("princeton-nlp/sup-simcse-bert-base-uncased")

    labellist = [
        "gfilabelnum",
        "buglabelnum",
        "testlabelnum",
        "buildlabelnum",
        "doclabelnum",
        "enhancelabelnum",
        "codinglabelnum",
        "featurelabelnum",
        "majorlabelnum",
        "mediumlabelnum",
        "untriagedlabelnum",
        "triagedlabelnum",
        "labelnum",
    ]
    cmtthre = 1

    cal_feature()

    nlp = spacy.load("en_core_web_sm")
    negsampnum = 9
    construct_dataset()
    logging.info("Finish")
