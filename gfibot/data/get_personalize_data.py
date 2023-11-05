import pymongo
import numpy as np
import pandas as pd
import logging
import multiprocessing as mp
import traceback
from typing import *
import json
import requests
import time
import gc
import os
import argparse
from collections import defaultdict
from datetime import datetime, timedelta
from gfibot import CONFIG, TOKENS
from gfibot.check_tokens import check_tokens
from gfibot.collections import *


def remove_and_match(lst1, lst2, value):
    index_to_remove = next((i for i, x in enumerate(lst1) if x == value), None)
    if index_to_remove is not None:
        del lst1[index_to_remove]
        del lst2[index_to_remove]


def run_query(query, variables, token):
    global v4tokenid, sleep_token
    for _ in range(0, 3):
        v4tokenid = v4tokenid + 1
        token = valid_tokens[v4tokenid % len(valid_tokens)]
        while token in sleep_token:
            time.sleep(10)
            v4tokenid = v4tokenid + 1
            token = valid_tokens[v4tokenid % len(valid_tokens)]
        headers = {
            "Authorization": "token " + token,
            "Accept": "application/vnd.github.hawkgirl-preview+json",
        }
        try:
            request = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=headers,
            )
            content = request.json()
            remaining = content["data"]["rateLimit"]["remaining"]
            resetAt = content["data"]["rateLimit"]["resetAt"]
            resetAt = datetime.strptime(resetAt, "%Y-%m-%dT%H:%M:%SZ") + timedelta(
                hours=8
            )
            resetAt = resetAt.timestamp()
            sleep_time = resetAt - time.time() + 10
            if remaining < 100:
                logging.info(
                    "Rate limit reached, wait for {} seconds...".format(sleep_time)
                )
                sleep_token.append(token)
                time.sleep(max(1.0, sleep_time))
                sleep_token.remove(token)
            else:
                return content
        except Exception as ex:
            logging.error("{}: {}: {}".format(type(ex), ex, variables))
            time.sleep(5)
    return None


def get_userdata(closer, issuet, nameWithOwner):
    query = """
    query($closer: String!,$time: DateTime) {
    rateLimit {
      remaining
      resetAt
    }
    user(login: $closer) {
    contributionsCollection(to: $time) {
    commitContributionsByRepository(maxRepositories: 5) {
    contributions(last: 10, orderBy: {direction: ASC, field: OCCURRED_AT}) {
      nodes {
        repository {
          description
          ...RepoFragment
          repositoryTopics(first: 10) {
          nodes {
            topic {
              name
            }
          }
          }
          languages(first: 1, orderBy: {field: SIZE, direction: DESC}) {
            nodes {
              name
            }
          }
          nameWithOwner
        }
      }
    }
    }
    issueContributions(last: 10, orderBy: {direction: ASC}) {
    nodes {
      issue {
        createdAt
        title
        body
        labels(first: 10) {
              nodes {
                name
              }
            }
        repository {
          nameWithOwner
        }
      }
    }
    }

    pullRequestContributions(last: 10, orderBy: {direction: ASC}) {
    nodes {
      pullRequest {
        createdAt
        title
        body
        commits(last: 5) {
          totalCount
          nodes {
            commit {
              message
            }
          }
        }
        labels(first: 10) {
          nodes {
            name
          }
        }
        repository {
          nameWithOwner
        }
        }
    }
    }
    pullRequestReviewContributions(last: 10, orderBy: {direction: ASC}) {
        nodes {
          pullRequest {
            title
            body
            labels(first: 10) {
              nodes {
                name
              }
            }
            repository {
              nameWithOwner
            }
          }
        }
      }
    }


    watching {
      totalCount
    }

    repositories(first: 100) {
    nodes {
      createdAt
      isFork
    }
    }
    organizations {
      totalCount
    }

    company
    createdAt
    followers {
      totalCount
    }
    following {
      totalCount
    }
    issueComments(first: 100) {
      nodes {
        issue {
          createdAt
          body
          title
          labels(first: 5) {
            nodes {
              name
            }
          }
        }
      }
    }

    }
    }

    fragment RepoFragment on Repository {
      readme1: object(expression: "master:README.md") {
        ...ReadmeText
      }
      readme2: object(expression: "master:README.MD") {
        ...ReadmeText
      }
      readme3: object(expression: "master:readme.md") {
        ...ReadmeText
      }
      readme4: object(expression: "master:Readme.md") {
        ...ReadmeText
      }
      readme5: object(expression: "master:README") {
        ...ReadmeText
      }
    }

    fragment ReadmeText on GitObject {
      ... on Blob {
        text
      }
    }
    """
    newt = (
        issuet
        - timedelta(
            hours=issuet.hour,
            minutes=issuet.minute,
            seconds=issuet.second,
            microseconds=issuet.microsecond,
        )
        - timedelta(days=1, seconds=1)
        + timedelta(hours=8)
    )
    inputt = datetime.utcfromtimestamp(
        time.mktime(
            time.strptime(newt.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
        )
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    variables = {"closer": closer, "time": inputt}
    result = run_query(query, variables)
    if result is None:
        return None
    prosdescription = []
    prosreadme = []
    prostopic = []
    prolan = []
    cmtproname = []
    issuelabels = []
    commentissuelabels = []
    prlabels = []
    if result["data"]["user"] is None:
        issuetitles = []
        issuebodys = []
        prtitles = []
        prbodys = []
        cmtmessages = []
        usercmt = 0
        userpr = 0
        useriss = 0
        userpronum = 0
        userallcmt = 0
        useralliss = 0
        userallpr = 0
        userwatchpro = 0
        userorg = 0
        usercomp = ""
        userlife = 0
        userfollower = 0
        userfollowing = 0
        prreviewtitles = []
        prreviewbodys = []
        commentissuetitles = []
        commentissuebodys = []
        readmenum = []
        readmetext = []
        userforkpronum = 0
        userprreview = 0
        userallprreview = 0
        onemonth_cmt = 0
        twomonth_cmt = 0
        threemonth_cmt = 0
        onemonth_pr = 0
        twomonth_pr = 0
        threemonth_pr = 0
        onemonth_iss = 0
        twomonth_iss = 0
        threemonth_iss = 0
    else:
        contributions = result["data"]["user"]["contributionsCollection"]
        userwatchpro = result["data"]["user"]["watching"]["totalCount"]
        userorg = result["data"]["user"]["organizations"]["totalCount"]
        usercomp = result["data"]["user"]["company"]
        userlife = (
            issuet
            - datetime.strptime(
                result["data"]["user"]["createdAt"].replace("T", " ").rstrip("Z"),
                "%Y-%m-%d %H:%M:%S",
            )
        ).days
        userfollower = result["data"]["user"]["followers"]["totalCount"]
        userfollowing = result["data"]["user"]["following"]["totalCount"]

        userprocreatedAt = [
            [i["createdAt"], i["isFork"]]
            for i in result["data"]["user"]["repositories"]["nodes"]
        ]
        if userprocreatedAt == []:
            userpronum = 0
            userforkpronum = 0
        else:
            userpronum = sum(
                [
                    datetime.strptime(
                        i[0].replace("T", " ").rstrip("Z"), "%Y-%m-%d %H:%M:%S"
                    )
                    < issuet
                    for i in userprocreatedAt
                    if i[1] is False
                ]
            )
            userforkpronum = sum(
                [
                    datetime.strptime(
                        i[0].replace("T", " ").rstrip("Z"), "%Y-%m-%d %H:%M:%S"
                    )
                    < issuet
                    for i in userprocreatedAt
                    if i[1] is True
                ]
            )

        if len(contributions["commitContributionsByRepository"]) > 0:
            for item in contributions["commitContributionsByRepository"]:
                cmtrepos = item["contributions"]["nodes"]
                repodeslst = [i["repository"]["description"] for i in cmtrepos]
                repodeslst = [i for i in repodeslst if i is not None]
                prosdescription.extend(repodeslst)

                repodeslst = []
                for i in cmtrepos:
                    repodeslst.extend(
                        [
                            i["repository"]["readme1"],
                            i["repository"]["readme2"],
                            i["repository"]["readme3"],
                            i["repository"]["readme4"],
                            i["repository"]["readme5"],
                        ]
                    )
                repodeslst = [i for i in repodeslst if i is not None]
                prosreadme.extend(repodeslst)

                repodeslst = []
                for i in cmtrepos:
                    topics = i["repository"]["repositoryTopics"]["nodes"]
                    topiclist = [m["topic"]["name"] for m in topics]
                    repodeslst.extend(topiclist)
                prostopic.append(repodeslst)

                for i in cmtrepos:
                    if (
                        "languages" in i["repository"].keys()
                        and len(i["repository"]["languages"]["nodes"]) > 0
                    ):
                        prolan.append(i["repository"]["languages"]["nodes"][0]["name"])
                cmtproname.extend([i["repository"]["nameWithOwner"] for i in cmtrepos])

        issues = contributions["issueContributions"]["nodes"]
        issuetitles = [i["issue"]["title"] for i in issues]
        issuebodys = [i["issue"]["body"] for i in issues]
        for i in issues:
            labels = i["issue"]["labels"]["nodes"]
            issuelabels.append([m["name"] for m in labels])
        issproname = [i["issue"]["repository"]["nameWithOwner"] for i in issues]
        onemonth_iss = len(
            [
                i["issue"]["repository"]["nameWithOwner"]
                for i in issues
                if datetime.strptime(
                    i["issue"]["createdAt"].replace("T", " ").rstrip("Z"),
                    "%Y-%m-%d %H:%M:%S",
                )
                > issuet - timedelta(days=30)
            ]
        )
        twomonth_iss = len(
            [
                i["issue"]["repository"]["nameWithOwner"]
                for i in issues
                if datetime.strptime(
                    i["issue"]["createdAt"].replace("T", " ").rstrip("Z"),
                    "%Y-%m-%d %H:%M:%S",
                )
                > issuet - timedelta(days=61)
            ]
        )
        threemonth_iss = len(
            [
                i["issue"]["repository"]["nameWithOwner"]
                for i in issues
                if datetime.strptime(
                    i["issue"]["createdAt"].replace("T", " ").rstrip("Z"),
                    "%Y-%m-%d %H:%M:%S",
                )
                > issuet - timedelta(days=91)
            ]
        )

        commentissues = result["data"]["user"]["issueComments"]["nodes"]
        commentissues = [
            i
            for i in commentissues
            if datetime.strptime(
                i["issue"]["createdAt"].replace("T", " ").rstrip("Z"),
                "%Y-%m-%d %H:%M:%S",
            )
            < issuet
        ]
        commentissues = commentissues[-10:]
        commentissuetitles = [i["issue"]["title"] for i in commentissues]
        commentissuebodys = [i["issue"]["body"] for i in commentissues]
        for i in commentissues:
            labels = i["issue"]["labels"]["nodes"]
            commentissuelabels.append([m["name"] for m in labels])

        prs = contributions["pullRequestContributions"]["nodes"]
        prtitles = [i["pullRequest"]["title"] for i in prs]
        prbodys = [i["pullRequest"]["body"] for i in prs]
        for i in prs:
            labels = i["pullRequest"]["labels"]["nodes"]
            prlabels.append([m["name"] for m in labels])
        onemonth_pr = 0
        twomonth_pr = 0
        threemonth_pr = 0
        onemonth_cmt = 0
        twomonth_cmt = 0
        threemonth_cmt = 0
        prproname = []
        for i in prs:
            prproname.append(i["pullRequest"]["repository"]["nameWithOwner"])
            if datetime.strptime(
                i["pullRequest"]["createdAt"].replace("T", " ").rstrip("Z"),
                "%Y-%m-%d %H:%M:%S",
            ) > issuet - timedelta(days=30):
                onemonth_pr += 1
                onemonth_cmt += i["pullRequest"]["commits"]["totalCount"]
            if datetime.strptime(
                i["pullRequest"]["createdAt"].replace("T", " ").rstrip("Z"),
                "%Y-%m-%d %H:%M:%S",
            ) > issuet - timedelta(days=61):
                twomonth_pr += 1
                twomonth_cmt += i["pullRequest"]["commits"]["totalCount"]
            if datetime.strptime(
                i["pullRequest"]["createdAt"].replace("T", " ").rstrip("Z"),
                "%Y-%m-%d %H:%M:%S",
            ) > issuet - timedelta(days=91):
                threemonth_pr += 1
                threemonth_cmt += i["pullRequest"]["commits"]["totalCount"]

        prreviews = contributions["pullRequestReviewContributions"]["nodes"]
        prreviewtitles = [i["pullRequest"]["title"] for i in prreviews]
        prreviewbodys = [i["pullRequest"]["body"] for i in prreviews]
        prreviewproname = [
            i["pullRequest"]["repository"]["nameWithOwner"] for i in prreviews
        ]

        userallcmt = len(cmtproname)
        useralliss = len(issproname)
        userallpr = len(prproname)
        userallprreview = len(prreviewproname)
        usercmt = sum([i == nameWithOwner for i in cmtproname])
        useriss = sum([i == nameWithOwner for i in issproname])
        userpr = sum([i == nameWithOwner for i in prproname])
        userprreview = sum([i == nameWithOwner for i in prreviewproname])

        cmtmessages = []
        for i in prs:
            cmts = i["pullRequest"]["commits"]["nodes"]
            for mes in cmts:
                cmtmessages.append(mes["commit"]["message"])

        readmenum = []
        readmetext = []
        for i in prosreadme:
            if i not in readmetext:
                readmetext.append(i)
        for i in range(len(readmetext)):
            readmenum.append(prosreadme.count(readmetext[i]))

    return [
        [
            issuetitles,
            issuebodys,
            prtitles,
            prbodys,
            cmtmessages,
            prosdescription,
            prolan,
            readmetext,
            readmenum,
            prostopic,
            issuelabels,
            prlabels,
            prreviewtitles,
            prreviewbodys,
            commentissuetitles,
            commentissuebodys,
            commentissuelabels,
        ],
        [
            usercmt,
            userpr,
            useriss,
            userpronum,
            userallcmt,
            useralliss,
            userallpr,
            userwatchpro,
            userprreview,
            userallprreview,
            userforkpronum,
            userorg,
            usercomp,
            userlife,
            userfollower,
            userfollowing,
            onemonth_cmt,
            twomonth_cmt,
            threemonth_cmt,
            onemonth_pr,
            twomonth_pr,
            threemonth_pr,
            onemonth_iss,
            twomonth_iss,
            threemonth_iss,
        ],
    ]


def get_issue_features(owner, name, number, issuet):
    global prodesdict
    nameWithOwner = owner + "/" + name
    try:
        prodes = prodesdict.get(nameWithOwner)
        if prodes is None:
            query = """
            query($name: String!,$owner: String!) {
            rateLimit {
              remaining
              resetAt
            }
            repository(name: $name, owner: $owner) {
            description
            ...RepoFragment
            repositoryTopics(first: 10) {
              nodes {
                topic {
                  name
                }
              }
              }
            languages(first: 1, orderBy: {field: SIZE, direction: DESC}) {
              nodes {
                name
              }
            }
            }
            }

            fragment RepoFragment on Repository {
              readme1: object(expression: "master:README.md") {
                ...ReadmeText
              }
              readme2: object(expression: "master:README.MD") {
                ...ReadmeText
              }
              readme3: object(expression: "master:readme.md") {
                ...ReadmeText
              }
              readme4: object(expression: "master:Readme.md") {
                ...ReadmeText
              }
              readme5: object(expression: "master:README") {
                ...ReadmeText
              }
            }

            fragment ReadmeText on GitObject {
              ... on Blob {
                text
              }
            }
            """
            variables = {"name": name, "owner": owner}
            result = run_query(query, variables)
            if result is None:
                return None
            else:
                repo = result["data"]["repository"]
                prodescription = repo["description"]
                lan = repo["languages"]["nodes"][0]["name"]
                readme = [
                    repo["readme1"],
                    repo["readme2"],
                    repo["readme3"],
                    repo["readme4"],
                    repo["readme5"],
                ]
                readme = [i for i in readme if i is not None]
                if len(readme) > 0:
                    readme = readme[0]["text"]
                topics = [i["topic"]["name"] for i in repo["repositoryTopics"]["nodes"]]
                prodesdict[nameWithOwner] = [prodescription, lan, readme, topics]
        else:
            prodescription = prodes[0]
            lan = prodes[1]
            readme = prodes[2]
            topics = prodes[3]

        myclient = pymongo.MongoClient("mongodb://localhost:27017/", connect=False)
        resolved_issue = myclient["gfibot"]["resolved_issue"]
        issue = resolved_issue.find_one(
            {"owner": owner, "name": name, "number": number}
        )
        closer = issue["resolver"]
        myclient.close()

        clsdata = get_userdata(closer, issuet, nameWithOwner)
        if clsdata is None:
            return None
        res = [prodescription, lan, clsdata, readme, topics, closer]
        return res
    except Exception as ex:
        logging.error(f"Error at {owner}/{name}/{number}: {ex}")
        traceback.print_exc()
        return None


def get_ratio(lst: list, threshold: int) -> float:
    if lst is None:
        return 0
    else:
        lst = [d for d in lst if d is not None]
        if lst == []:
            return 0
        pnum = sum(d < threshold for d in lst)
        nnum = len(lst) - pnum
        return pnum / (pnum + nnum)


def get_num(lst: list, threshold: int) -> int:
    if lst is None:
        return 0
    else:
        lst = [d for d in lst if d is not None]
        if lst == []:
            return 0
        pnum = sum(d < threshold for d in lst)
        return pnum


def get_issues(x):
    cmtthre = 1  # cmtthre-1: max commit numumber in a project for a newcomer
    issuet = x["created_at"]
    clst = x["closed_at"]
    clscmt = x["resolver_commit_num"]
    title = x["title"]
    body = x["body"]
    LengthOfTitle = x["len_title"]
    LengthOfDescription = x["len_body"]
    NumOfCode = x["n_code_snips"]
    NumOfUrls = x["n_urls"]
    NumOfPics = x["n_imgs"]
    coleman_liau_index = x["coleman_liau_index"]
    flesch_reading_ease = x["flesch_reading_ease"]
    flesch_kincaid_grade = x["flesch_kincaid_grade"]
    automated_readability_index = x["automated_readability_index"]
    buglabelnum = x["label_category"]["bug"]
    featurelabelnum = x["label_category"]["feature"]
    testlabelnum = x["label_category"]["test"]
    buildlabelnum = x["label_category"]["build"]
    doclabelnum = x["label_category"]["doc"]
    codinglabelnum = x["label_category"]["coding"]
    enhancelabelnum = x["label_category"]["enhance"]
    gfilabelnum = x["label_category"]["gfi"]
    mediumlabelnum = x["label_category"]["medium"]
    majorlabelnum = x["label_category"]["major"]
    triagedlabelnum = x["label_category"]["triaged"]
    untriagedlabelnum = x["label_category"]["untriaged"]
    labelnum = len(x["labels"])
    rptcmt = x["reporter_feat"]["n_commits"]
    rptiss = x["reporter_feat"]["n_issues"]
    rptpr = x["reporter_feat"]["n_pulls"]
    rptpronum = x["reporter_feat"]["n_repos"]
    rptallcmt = x["reporter_feat"]["n_commits_all"]
    rptalliss = x["reporter_feat"]["n_issues_all"]
    rptallpr = x["reporter_feat"]["n_pulls_all"]
    rpt_reviews_num_all = x["reporter_feat"]["n_reviews_all"]
    rpt_max_stars_commit = x["reporter_feat"]["max_stars_commit"]
    rpt_max_stars_issue = x["reporter_feat"]["max_stars_issue"]
    rpt_max_stars_pull = x["reporter_feat"]["max_stars_pull"]
    rpt_max_stars_review = x["reporter_feat"]["max_stars_review"]
    rptisnew = int(x["reporter_feat"]["n_commits"] < cmtthre)
    rpt_gfi_ratio = get_ratio(x["reporter_feat"]["resolver_commits"], cmtthre)

    ownercmt = x["owner_feat"]["n_commits"]
    owneriss = x["owner_feat"]["n_issues"]
    ownerpr = x["owner_feat"]["n_pulls"]
    ownerpronum = x["owner_feat"]["n_repos"]
    ownerallcmt = x["owner_feat"]["n_commits_all"]
    owneralliss = x["owner_feat"]["n_issues_all"]
    ownerallpr = x["owner_feat"]["n_pulls_all"]
    owner_reviews_num_all = x["owner_feat"]["n_reviews_all"]
    owner_max_stars_commit = x["owner_feat"]["max_stars_commit"]
    owner_max_stars_issue = x["owner_feat"]["max_stars_issue"]
    owner_max_stars_pull = x["owner_feat"]["max_stars_pull"]
    owner_max_stars_review = x["owner_feat"]["max_stars_review"]
    owner_gfi_ratio = get_ratio(x["owner_feat"]["resolver_commits"], cmtthre)
    owner_gfi_num = get_num(x["owner_feat"]["resolver_commits"], cmtthre)
    pro_gfi_ratio = get_ratio(x["prev_resolver_commits"], cmtthre)
    pro_gfi_num = get_num(x["prev_resolver_commits"], cmtthre)
    pro_star = x["n_stars"]
    proclspr = x["n_pulls"]
    procmt = x["n_commits"]
    contributornum = x["n_contributors"]
    crtclsissnum = x["n_closed_issues"]
    openiss = x["n_open_issues"]
    openissratio = x["r_open_issues"]
    clsisst = x["issue_close_time"]

    owner = x["owner"]
    name = x["name"]
    number = x["number"]
    issue_features = get_issue_features(owner, name, number, issuet)
    if issue_features is None:
        logging.info("none")
        return None
    else:
        prodescription = issue_features[0]
        lan = issue_features[1]
        clsdata = issue_features[2]
        readme = issue_features[3]
        topics = issue_features[4]
        clsname = issue_features[5]
    res = {
        "issuet": issuet,
        "clst": clst,
        "clscmt": clscmt,
        "title": title,
        "body": body,
        "LengthOfTitle": LengthOfTitle,
        "LengthOfDescription": LengthOfDescription,
        "NumOfCode": NumOfCode,
        "NumOfUrls": NumOfUrls,
        "NumOfPics": NumOfPics,
        "coleman_liau_index": coleman_liau_index,
        "flesch_reading_ease": flesch_reading_ease,
        "flesch_kincaid_grade": flesch_kincaid_grade,
        "automated_readability_index": automated_readability_index,
        "buglabelnum": buglabelnum,
        "featurelabelnum": featurelabelnum,
        "testlabelnum": testlabelnum,
        "buildlabelnum": buildlabelnum,
        "doclabelnum": doclabelnum,
        "codinglabelnum": codinglabelnum,
        "enhancelabelnum": enhancelabelnum,
        "gfilabelnum": gfilabelnum,
        "mediumlabelnum": mediumlabelnum,
        "majorlabelnum": majorlabelnum,
        "triagedlabelnum": triagedlabelnum,
        "untriagedlabelnum": untriagedlabelnum,
        "labelnum": labelnum,
        "rptcmt": rptcmt,
        "rptiss": rptiss,
        "rptpr": rptpr,
        "rptpronum": rptpronum,
        "rptallcmt": rptallcmt,
        "rptalliss": rptalliss,
        "rptallpr": rptallpr,
        "rpt_reviews_num_all": rpt_reviews_num_all,
        "rpt_max_stars_commit": rpt_max_stars_commit,
        "rpt_max_stars_issue": rpt_max_stars_issue,
        "rpt_max_stars_pull": rpt_max_stars_pull,
        "rpt_max_stars_review": rpt_max_stars_review,
        "rptisnew": rptisnew,
        "rpt_gfi_ratio": rpt_gfi_ratio,
        "ownercmt": ownercmt,
        "owneriss": owneriss,
        "ownerpr": ownerpr,
        "ownerpronum": ownerpronum,
        "ownerallcmt": ownerallcmt,
        "owneralliss": owneralliss,
        "ownerallpr": ownerallpr,
        "owner_reviews_num_all": owner_reviews_num_all,
        "owner_max_stars_commit": owner_max_stars_commit,
        "owner_max_stars_issue": owner_max_stars_issue,
        "owner_max_stars_pull": owner_max_stars_pull,
        "owner_max_stars_review": owner_max_stars_review,
        "owner_gfi_ratio": owner_gfi_ratio,
        "owner_gfi_num": owner_gfi_num,
        "pro_gfi_ratio": pro_gfi_ratio,
        "pro_gfi_num": pro_gfi_num,
        "pro_star": pro_star,
        "proclspr": proclspr,
        "procmt": procmt,
        "contributornum": contributornum,
        "crtclsissnum": crtclsissnum,
        "openiss": openiss,
        "openissratio": openissratio,
        "clsisst": clsisst,
        "owner": owner,
        "name": name,
        "number": number,
        "clsname": clsname,
        "prodescription": prodescription,
        "lan": lan,
        "readme": readme,
        "topics": topics,
        "clsdata": clsdata,
    }
    logging.info("fulldata")
    return res


def main():
    global prodesdict, valid_tokens, sleep_token
    logger = logging.getLogger(__name__)
    sleep_token = []
    prodesdict = {}
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--nprocess", type=int, default=mp.cpu_count())
    parser.add_argument("--repos", type=str, default="")
    args = parser.parse_args()
    dburl = CONFIG["gfibot"]["mongodb"]["url"]
    myclient = pymongo.MongoClient(dburl, connect=False)
    mydb = myclient["gfibot"]["dataset"]

    existiss = []
    existdata = []
    if os.path.exists(os.path.dirname(__file__) + "/../data/personalizeddata.json"):
        with open(os.path.dirname(__file__) + "/../data/personalizeddata.json") as f:
            issuestr = json.load(f)
        issuedata = issuestr["0"]
        for i in range(len(issuedata)):
            iss = issuedata[str(i)]
            existiss.append(iss["owner"] + iss["name"] + str(iss["number"]))
            existdata.append(iss)

    rawissuelist = [
        x
        for x in mydb.find()
        if x["created_at"] == x["before"]
        and x["owner"] + x["name"] + str(x["number"]) not in existiss
    ]
    del mydb
    gc.collect()
    myclient.close()

    # limit training set size
    max_size = 10000
    sorted_list = sorted(rawissuelist, key=lambda x: x["created_at"], reverse=True)
    issuelist = sorted_list[:max_size]

    failed_tokens = check_tokens(TOKENS)
    valid_tokens = list(set(TOKENS) - failed_tokens)

    logger.info("Personalized data collection started at {}".format(datetime.now()))

    params = defaultdict(list)
    for i, issue in enumerate(issuelist):
        params[valid_tokens[i % len(valid_tokens)]].append(issue)
    with mp.Pool(min(args.nprocess, len(valid_tokens))) as pool:
        res = pool.starmap(get_issues, issuelist)
        res = [i for i in res if i is not None]
    res.extend(existdata)
    res = np.array(res)
    pd.DataFrame(res).to_json(
        os.path.dirname(__file__) + "/../data/personalizeddata.json"
    )
    logger.info("Personalized data collection finished at {}".format(datetime.now()))


if __name__ == "__main__":
    main()
