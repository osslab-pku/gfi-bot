from os import name
import pymongo
import json
import numpy as np
from datetime import timedelta, datetime
import logging
import multiprocessing as mp
import pandas as pd
import random
from typing import Pattern
import re
import textstat
from sentistrength import PySentiStr
from tqdm import tqdm
from gensim.models.word2vec import Word2Vec

eventtypelist = [
    "labeled",
    "subscribed",
    "referenced",
    "mentioned",
    "closed",
    "assigned",
    "milestoned",
    "unlabeled",
    "moved_columns_in_project",
    "locked",
    "added_to_project",
    "demilestoned",
    "removed_from_project",
    "unassigned",
    "renamed",
    "reopened",
    "head_ref_force_pushed",
    "transferred",
    "unsubscribed",
    "merged",
    "head_ref_deleted",
    "comment_deleted",
    "review_requested",
    "connected",
    "marked_as_duplicate",
]
gfilabellist = [
    "good first issue",
    "good-first-issue",
    "easy",
    "Easy",
    "low hanging fruit",
    "low-hanging-fruit",
    "minor bug",
    "Easy Pick",
    "easy pick",
    "Easy pick",
    "Easy to Fix",
    "Easy-fix",
    "easy-fix",
    "EasyToFix",
    "help-wanted-easy",
    "effort: easy",
    "easy-pick",
    "Difficulty: Easy",
    "easy fix",
    "Easy to implement",
    "Effort: Easy",
    "EASY",
    "good first bug",
    "beginner",
    "good first contribution",
    "Good first task",
    "newbie",
    "starter bug",
    "beginner-task",
    "beginner-friendly",
    "d. Beginner",
    "exp: beginner",
    "good for beginner",
    "Good for Beginners",
    "Difficulty: beginner",
    "Minor Bug",
    "easy-pick",
    "minor feature",
    "help wanted (easy)",
    "up-for-grabs",
    "good-first-bug",
    "good-first-contribution",
    ":wave: Good First Issue",
    "first-timer",
    "first PR",
    "Effort Low",
    "type: bug (minor)",
    "Good First Issue",
    "Good First Task",
    "first-timers-only",
    "Good first issue",
    "good first issue (taken)",
    "first timers welcome",
    "Good first issue :mortar_board:",
    "Good First Issue :wave:",
    "Good as first PR",
    "First-Time-Issue",
    "gsoc first issue",
    "good-first-issue",
    "Low-Hanging Fruit",
    "type: feature (minor)",
    "bug: minor",
    "feature: minor",
    "semver-minor",
    "minor",
    "low fruit",
    "Difficulty Novice",
    "starter project",
    "starter issue",
    "Difficulty: starter",
    "difficulty: starter",
    "Project-specific starter issue",
    "starter",
    "starter bug",
    "Starter bug",
]
buglabellist = [
    "bug",
    "Bug",
    "t/bug :bug:",
    "[Type] Bug",
    "<Bug>",
    ">bug",
    "type: bug",
    "confirmed-bug",
    "Potential Bug",
    "confirmed bug",
    "type: bug (minor)",
    "type - bug",
    "original bug",
    "t/bug",
    "Type: Bug",
    "good first bug",
    ":beetle: type: bug",
    "good-first-bug",
    "Type: Bug Report",
    "potential bug",
    "Bug Report",
    "BUG",
    "Issue-Bug",
    "Minor Bug",
    "bug: minor",
    "type: bug (major)",
    "type:Bug",
    "test bug",
    "Bug Bash",
    "minor bug",
    "🏷 type: bug",
    "bug: major",
    "type: bug :beetle:",
    "I-bug",
    "Type: Bug :bug:",
    "status: confirmed bug",
    "type: bug 🐛",
    ":bug: Bug",
    "bug report",
    "bug 🐛",
    "Docs Bug",
    "Confirmed bug",
    "kind: bug",
    "bug bash",
    "major bug",
    "data file bug",
    "AI bug",
    "Serious Bug",
    "starter bug",
    "C-bug",
    "Starter bug",
    "apibug",
    "bug :bug:",
    "Bug: triage",
    "bug 🤹\u200d♂️",
    "[Type] WP Core Bug",
    "Bug :bug:",
    "bug: confirmed",
    "bug-publishing",
    "<Bugfix>",
    "t: bug 🐛",
    "Bug Fix",
    "good contrib bug",
]
testlabellist = [
    "test",
    ">test-failure",
    "tests",
    "Needs Tests",
    "Testing",
    "Tests",
    "Needs Testing",
    "CI / flaky test",
    "Test",
    "testing",
    "v-test",
    "failed-test",
    "test bug",
    "Test Improvement",
    "area: testing-infrastructure",
    ">test",
    "Unreliable Test",
    "Area-Test",
    "feature-unit-testing",
    "Automated Testing",
    "smoke-test",
    "area: testing-coverage",
    "🔩Test Infrastructure",
    "needs unit test",
    "test failure",
    "integration-test",
    "team: refactoring and unit tests (@BenHenning)",
    "unit-testing",
    "new-test-script",
    "new test script",
    "Code: Tests",
]
buildlabellist = [
    "CI",
    "CI / flaky test",
    "Testing / Continuous Integration (CI)",
    "Build / CI",
    "build",
    "Build",
    "Build system",
    ":Core/Infra/Build",
    "Area-Build",
    ":Core/Build",
    "build-system",
    "build system",
    ":Delivery/Build",
    "Build Tooling",
    "build/tooling",
    "[Type] Build Tooling",
    "Code: Build",
    "Component: Build & Tooling",
    "Component: Build Infrastructure",
]
doclabellist = [
    "documentation",
    "Documentation",
    "doc",
    "Docs",
    "docs",
    "Documentation",
    "documentation",
    ">docs",
    "area: documentation (user)",
    "Docs and Output",
    "docs-requested",
    "area: documentation (api and integrations)",
    "<Documentation>",
    "🏷 type: documentation",
    "Docs Request",
    "Component: Documentation & Website",
    "area: documentation (developer)",
    "Documentation Request",
    "Docs Bug",
    "area: documentation (production)",
    "docs/generated",
    "Team:Docs",
    "Documentation :book:",
    "tag:Documentation",
    "DOC",
    "TODO: tech (design doc)",
    "Doc Request",
    "category - doc",
    "t/docs",
    "submitty.org / documentation",
    "[Type] Documentation",
    "Documentation Lockdown",
    "needs design doc",
    "area/docs",
    "Area-Documentation",
    "[Component] Document Outline",
    "Inline documentation",
    "javadoc",
    "needs-breaking-change-doc-created",
    ":Nested Docs",
    ":Docs",
    "Documentation: needs merge to stable",
    ":no_entry_sign:Docs",
    "scope: docs",
    "status: needs docs review",
    "cat:Documentation",
    "component:Document Registry",
    "Domain: JSDoc",
    "impact: docs",
    "a/docs",
    "documentation (api and integrations)",
    "area: documentation",
    "I-docs",
    "release_note:enhancement",
    "[Feature] Rich Text",
    "[Component] Rich Text",
    "[Package] Rich text",
]
enhancelabellist = [
    "enhancement",
    "Enhancement",
    "[Type] Enhancement",
    "type: enhancement",
    ">enhancement",
    "t/enhancement ➕",
    "<Enhancement / Feature>",
    "t/enhancement",
    "type: feature or enhancement",
    "type:Enhancement",
    "Issue-Enhancement",
    "Type: Enhancement",
    "type - enhancement",
    "release_note:enhancement",
    "kind: enhancement",
    "Type-Enhancement",
    "status: enhancement",
    "t: enhancement",
    "enhancement / feature request",
    "changelog: enhancement",
    "test enhancement",
    "Experience Enhancement",
    "kind/enhancement",
]
codinglabellist = ["coding", "Coding", "TODO: coding", "programming"]
featurelabellist = [
    "feature-request",
    "feature",
    "Feature",
    "feature request",
    "Feature Request",
    "type: feature request",
    "Feature:Logs UI",
    "Feature:TSVB",
    "Feature:Metrics UI",
    "type: feature (minor)",
    "New Language Feature - Nullable Reference Types",
    "<Enhancement / Feature>",
    "type: feature (important)",
    "[Feature] Inserter",
    "feature: dav",
    "Feature:Alerting",
    "feature: ldap",
    "[Feature] Rich Text",
    "[Feature] Reusable Blocks",
    "New Language Feature - Local Functions",
    "type: feature or enhancement",
    "New feature",
    "feature: important",
    "feature-inspections",
    "[Feature] Full Site Editing",
    ">feature",
    ":Core/Features/Watcher",
    "New Feature - IOperation",
    "feature: files",
    "minor feature",
    ":Core/Features/Ingest",
    "Type: Feature Request",
    "new feature",
    "New Language Feature - Tuples",
    "Feature:Observability Landing - Milestone 1",
    "Feature:XYAxis",
    "feature: settings",
    "t/feature",
    "Feature:ElasticCharts",
    "feature: theming",
    "feature: minor",
    "Type: New Feature :heavy_plus_sign:",
    "Feature:Custom Links",
    "Feature:Observability Landing",
    "Feature:Vislib",
    ":rocket: Feature Request",
    "feature: install and update",
    "[Feature] Writing Flow",
    "[Feature] Themes",
    "Team:Core/Features",
    "Feature:Plugins",
    "Feature:Custom Actions",
    "feature: users and groups",
    "type: feature",
    "Feature request",
    "[Feature] Raw Handling",
    "[Feature] Patterns",
    "[Feature] Blocks",
    "New Language Feature - Pattern Matching",
    ":Core/Features/Monitoring",
    "Feature:Discover",
    "Feature:Vis Editor",
    "🏷 type: feature",
    "kind: feature",
    "feature: sharing",
    "feature: authentication",
    "feature-smart-indenter",
    "core feature",
    "[Feature] Permalink",
    "[Feature] UI Components",
    "New Language Feature - Records",
    ":Core/Features/Java High Level REST Client",
    "Feature:EPM",
    "Feature:Fleet",
    "Feature:APM Agent Configuration",
    "New Feature",
    "feature: contacts menu",
    "feature: filesystem",
    "feature-code-explorer",
    "feature-settings",
    "feature-inspection-quickfixes",
    "major feature",
    "[Feature] Block Navigation",
    "[Feature] Style Variations",
    "[Feature] Drag and Drop",
    "[Feature] Widgets Screen",
    "[Feature] Extensibility",
    "[Feature] Site Editor",
    "New Language Feature - Ref Locals and Returns",
    ":Core/Features/CAT APIs",
    ":Core/Features/Java Low Level REST Client",
    "Feature:Visualizations",
    "Feature:Task Manager",
    "Feature:Anomaly Detection",
    "Feature:Service Maps",
    "Feature:Endpoint",
    "Feature:Dashboard",
    "Feature:NP Migration",
    "Feature:Lens",
    "Feature:APM alerting",
    "Feature:EventLog",
    "Feature:Pie Chart",
    "Feature:Logging",
    "feature: search",
    "feature: tags",
    "feature: comments",
    "feature: apps management",
    "feature: workflows",
    "feature: external storage",
    "feature: locking",
    "feature-annotations",
    "New Language Feature - Readonly References",
    "[Feature] Nested / Inner Blocks",
    "[Feature] REST API Interaction",
    "[Feature] Code Editor",
    "[Feature] Block API",
    "[Feature] Block Directory",
    "[Feature] Design Tools",
    "[Feature] Block settings menu",
    "New Feature - Source Generators",
    ":New Feature",
    "Feature:Coordinate Map",
    "Feature:Rollups",
    "Feature:New Platform",
    "Feature:Dependencies",
    "Feature:Data Frame Analytics",
    "Feature:SharingURLs",
    "Feature:Input Control",
    "Feature:UIActions",
    "Feature:Filters",
    "Feature:Timelion",
    "Type: Feature",
    "feature: logging",
    "feature: scss",
    "feature: activity and notification",
    "feature: language l10n and translations",
    "feature: trashbin",
    "feature: filepicker",
    "Feature:FieldFormatters",
    "Feature:Search Profiler",
]
majorlabellist = [
    "important",
    "type: feature (important)",
    "feature: important",
    "Important",
    "type: bug (major)",
    "bug: major",
    "p2 - major",
    "major bug",
    "major",
    "major feature",
    "severity: major",
    "Serious Bug",
    "core",
    "Core",
    ":Core/Infra/Core",
    ":Core/Infra/Build",
    ":Core/Build",
    ":Core/Infra/Packaging",
    ":Core/Features/Watcher",
    "Core Team",
    ":Core/Features/Ingest",
    "difficult",
    "Difficulty: Hard",
    "breaking",
    "Breaking Change",
    "Breaking-Change",
    "breaking-change",
    "breaking-java",
    "breaking change",
    "priority: high",
    "p1 - priority",
    "high priority",
    "Priority High",
    "Priority: High",
    "[Priority] High",
    "High Priority",
    "Priority: Critical",
    "priority - high",
]
mediumlabellist = [
    "Effort Medium",
    "Medium Severity",
    "Priority: Medium",
    "priority: medium",
    "medium",
    "Priority-Medium",
    "medium priority",
    "severity-medium",
    "Difficulty: Medium",
    "p. Medium",
    "(P3 - Medium)",
    "effort/medium",
    "Priority Medium",
    "Difficulty: medium",
    "Priority: 3 - Medium :unamused:",
    "medium difficult",
    "impact:medium",
    "Prio-medium",
    "Difficulty Intermediate",
    "intermediate",
    "exp: intermediate",
    "difficulty: intermediate",
    "intermediate-task",
    "Difficulty Advanced",
]
untriagedlabellist = [
    "untriaged",
    "needs-triage",
    "Needs Triage",
    "status/needs-triage",
    "needs triage",
    "0. Needs triage",
    "status: triage needed",
    "needs:triage",
    "triage_needed",
    "Needs: Triage :mag:",
    "status: needs triage",
    "Needs: Triage",
    "status: needs help for triage",
    "no triage",
]
triagedlabellist = [
    "triaged",
    "triage",
    "Bug: triage",
    "hasPR",
    "Has fix",
    "has-pr",
    "has PR",
    "Has PR",
    "in-progress",
    "in progress",
    "fix in progress",
    "[Status] In Progress",
    "waffle:in progress",
    "[zube]: In Progress",
    "waffle:progress",
    "status: in progress",
    "State: Work In Progress",
    "status/in-progress",
    "work in progress",
    "status: fix in progress",
    "fixed but not closed",
    "Fixed",
    "Resolution-Fixed",
    "fixed-pls-verify",
    "fixed",
    "Resolution: Fixed",
    ":confetti_ball:Fixed",
    "Fixed in 2.3.x",
    "wontfix",
    "Resolution: Wontfix",
    "status: wontfix",
]
labellist = [
    gfilabellist,
    buglabellist,
    testlabellist,
    buildlabellist,
    doclabellist,
    enhancelabellist,
    codinglabellist,
    featurelabellist,
    majorlabellist,
    mediumlabellist,
    untriagedlabellist,
    triagedlabellist,
]
res = []


def count_code_number(str):
    p = re.compile(r"```.+?```", flags=re.S)
    if str == None:
        return 0
    return len(p.findall(str))


def delete_code(str):
    if str == None:
        return ""
    p = re.compile(r"```.+?```", flags=re.S)
    s = p.sub("", str)
    return " ".join(s.split())


def count_url(str):
    if str == None:
        return 0

    def notPic(s):
        if s.endswith("jpg") or s.endswith("jpeg") or s.endswith("png"):
            return False
        return True

    p = re.compile(r"http[:/\w\.]+")
    lst = list(filter(notPic, p.findall(str)))
    return len(lst)


def count_pic(str):
    if str == None:
        return 0
    p = re.compile(r"http[:/\w\.]+")

    def isPic(s):
        if s.endswith("jpg") or s.endswith("jpeg") or s.endswith("png"):
            return True
        return False

    lst = list(filter(isPic, p.findall(str)))
    return len(lst)


def delete_url(str):
    if str == None:
        return ""
    p = re.compile(r"http[:/\w\.]+")
    s = p.sub("", str)
    return " ".join(s.split())


def count_comment_num(lst):
    return len(lst)


def joincomment(lst):
    return "".join(lst)


def count_text_len(str):
    if str == None:
        return 0
    return len(str.split())


def get_userdata(owner, reponame, user, commits, issues, issdb, t):
    if user == "ghost":
        return [0, 0, 0, []]
    usrcmt = commits.find(
        {"$or": [{"committer": user}, {"author": user, "committer": "web-flow"}]}
    )
    usrallcmt = []
    for cmt in usrcmt:
        if cmt["committer"] == "web-flow":
            if cmt["authored_at"] < t:
                usrallcmt.append(cmt)
        else:
            if cmt["committed_at"] < t:
                usrallcmt.append(cmt)
    commits_in_repo = sum(
        [cmt["owner"] == owner and cmt["name"] == reponame for cmt in usrallcmt]
    )
    # commits_all=len(usrallcmt)

    usriss = issues.find({"user": user, "is_pull": False})
    usralliss = [iss for iss in usriss if iss["created_at"] < t]
    issues_in_repo = sum(
        [(iss["owner"] == owner and iss["name"] == reponame) for iss in usralliss]
    )
    usralliss = [
        iss for iss in usriss if iss["closed_at"] is not None and iss["closed_at"] < t
    ]
    isslist = [
        iss["number"]
        for iss in usralliss
        if iss["owner"] == owner and iss["name"] == reponame
    ]
    if isslist == []:
        issue_closer_commits = []
    else:
        issue_closer_commits = issdb.find({"number": {"$in": isslist}})
        issue_closer_commits = [
            i["resolver_commit_num"] for i in issue_closer_commits if i is not None
        ]
    usrpr = issues.find({"user": user, "is_pull": True})
    usrallpr = [pr for pr in usrpr if pr["created_at"] < t]
    pulls_in_repo = sum(
        [pr["owner"] == owner and pr["name"] == reponame for pr in usrallpr]
    )
    return [
        commits_in_repo,
        issues_in_repo,
        pulls_in_repo,
        issue_closer_commits,
    ]


def get_feature(
    id, owner, reponame, number, resolver, resolver_commit_num, resolved_in, eventslist
):
    cls = None
    for event in eventslist:
        if event["type"] == "closed":
            t = event["time"]
            cls = event["actor"]
            break
    if cls == None:
        return None

    mgclient = pymongo.MongoClient("mongodb://localhost:27017/", connect=False)
    issuedataset = mgclient["gfibot"]["issuedataset"]
    if (
        issuedataset.find_one({"owner": owner, "name": reponame, "number": number})
        is not None
    ):
        mgclient.close()
        logging.info("skip")
        return

    issues = mgclient["gfibot"]["repos.issues"]
    issue = issues.find_one({"owner": owner, "name": reponame, "number": number})
    if issue["is_pull"] == True or issue["state"] == "open":
        mgclient.close()
        return None

    repos = mgclient["gfibot"]["repos"]
    commits = mgclient["gfibot"]["repos.commits"]
    stars = mgclient["gfibot"]["repos.stars"]
    issdb = mgclient["gfibot"]["issues"]

    eventdatalist = [[] for i in range(len(eventtypelist) + 1)]
    commentlist = []
    commentbody = []
    eventlabel = []
    alleventlabel = []
    cmtor = []
    rpthasevent = 0
    rpthascomment = 0
    labels = [0] * 13

    rpt = issue["user"]
    title = issue["title"]
    body = issue["body"]
    alllabels = issue["labels"]
    clst = issue["closed_at"]

    for event in eventslist:
        etyp = event["type"]
        evtt = event["time"]
        if evtt < t:
            ind = eventtypelist.index(etyp) if etyp in eventtypelist else None
            if ind == None:
                ind = -1
            eventer = event["actor"]
            userdata = get_userdata(owner, reponame, eventer, commits, issues, issdb, t)
            eventdatalist[ind].append(userdata)
            if eventer == rpt and etyp != "labeled":
                rpthasevent = 1
            if etyp == "commented":
                commenter = eventer
                commentbody.append(event["comment"])
                if commenter == rpt:
                    rpthascomment = 1
                userdata = get_userdata(
                    owner, reponame, commenter, commits, issues, issdb, t
                )
                commentlist.append(userdata)
            if etyp == "labeled":
                label = event["label"]
                eventlabel.append(label)
                alleventlabel.append(label)
            if etyp == "unlabeled":
                label = event["label"]
                if label in eventlabel:
                    eventlabel.remove(label)
                if label in alleventlabel:
                    alleventlabel.remove(label)
        else:
            if etyp == "labeled":
                label = event["label"]
                alleventlabel.append(label)
            if etyp == "unlabeled":
                label = event["label"]
                if label in alleventlabel:
                    alleventlabel.remove(label)

    isstlabel = [l for l in alllabels if l not in alleventlabel]
    reftlabel = isstlabel + eventlabel
    if reftlabel is None:
        reftlabel = []

    for lab in reftlabel:
        for i in range(len(labellist)):
            if lab in labellist[i]:
                labels[i] += 1
        labels[-1] = len(reftlabel)

    repo = repos.find_one({"owner": owner, "name": reponame})
    pro_star = sum(
        [star["count"] for star in repo["monthly_stars"] if star["month"] < t]
    )
    propr = sum([pr["count"] for pr in repo["monthly_pulls"] if pr["month"] < t])
    procmt = sum([cmt["count"] for cmt in repo["monthly_commits"] if cmt["month"] < t])
    cmts = commits.find({"owner": owner, "name": reponame})
    for cmt in cmts:
        if cmt["committer"] == "web-flow":
            if cmt["authored_at"] < t:
                cmtor.append(cmt["author"])
        else:
            if cmt["committed_at"] < t:
                cmtor.append(cmt["committer"])
    contributornum = len(list(set(cmtor)))

    proissues = issues.find({"owner": owner, "name": reponame})
    isslist = [
        iss
        for iss in proissues
        if iss["closed_at"] is not None and iss["closed_at"] < t
    ]
    crtclsissnum = len(isslist)
    latestclsiss = [iss["closed_at"] - iss["created_at"] for iss in isslist]
    isslist = [iss["number"] for iss in isslist]
    clsissues = issdb.find(
        {"owner": owner, "name": reponame, "number": {"$in": isslist}}
    )
    isslist = [iss["resolver_commit_num"] for iss in clsissues]
    if latestclsiss == []:
        clsisst = 1000.0
    else:
        clsisst = np.median(latestclsiss)
        clsisst = clsisst.total_seconds() // 3600
    openiss = sum(
        [
            iss["created_at"] < t and (iss["closed_at"] > t or iss["closed_at"] is None)
            for iss in proissues
        ]
    )
    if openiss + crtclsissnum == 0:
        openissratio = 0.0
    else:
        openissratio = openiss / (openiss + crtclsissnum)

    [ownercmt, owneriss, ownerpr, ownerissues] = get_userdata(
        owner, reponame, owner, commits, issues, issdb, t
    )
    [rptcmt, rptiss, rptpr, rptissues] = get_userdata(
        owner, reponame, rpt, commits, issues, issdb, t
    )

    NumOfCode = count_code_number(body)
    body = delete_code(body)
    NumOfUrls = count_url(body)
    NumOfPics = count_pic(body)
    body = delete_url(body)
    coleman_liau_index = textstat.coleman_liau_index(body)
    flesch_reading_ease = textstat.flesch_reading_ease(body)
    flesch_kincaid_grade = textstat.flesch_kincaid_grade(body)
    automated_readability_index = textstat.automated_readability_index(body)
    LengthOfTitle = count_text_len(title)
    LengthOfDescription = count_text_len(body)
    comment = joincomment(commentbody)
    commentnum = count_comment_num(commentbody)

    issuedataset.insert_one(
        {
            "owner": owner,
            "name": reponame,
            "number": number,
            "resolver_commit_num": resolver_commit_num,
            "clst": clst,
            "pro_star": pro_star,
            "isslist": isslist,
            "propr": propr,
            "rptcmt": rptcmt,
            "rptiss": rptiss,
            "rptpr": rptpr,
            "rptissues": rptissues,
            "ownercmt": ownercmt,
            "owneriss": owneriss,
            "ownerpr": ownerpr,
            "ownerissues": ownerissues,
            "procmt": procmt,
            "contributornum": contributornum,
            "crtclsissnum": crtclsissnum,
            "openiss": openiss,
            "openissratio": openissratio,
            "clsisst": clsisst,
            "labels": labels,
            "events": eventdatalist,
            "commentusers": commentlist,
            "rpthasevent": rpthasevent,
            "rpthascomment": rpthascomment,
            "NumOfCode": NumOfCode,
            "NumOfUrls": NumOfUrls,
            "NumOfPics": NumOfPics,
            "coleman_liau_index": coleman_liau_index,
            "flesch_reading_ease": flesch_reading_ease,
            "flesch_kincaid_grade": flesch_kincaid_grade,
            "automated_readability_index": automated_readability_index,
            "LengthOfTitle": LengthOfTitle,
            "LengthOfDescription": LengthOfDescription,
            "commentnum": commentnum,
            "title": title,
            "body": body,
            "comment": comment,
        }
    )
    mgclient.close()
    logging.info("add")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )
    myclient = pymongo.MongoClient("mongodb://localhost:27017/", connect=False)
    mydb = myclient["gfibot"]["issues"]
    issuelist = [
        [
            x["_id"],
            x["owner"],
            x["name"],
            x["number"],
            x["resolver"],
            x["resolver_commit_num"],
            x["resolved_in"],
            x["events"],
        ]
        for x in mydb.find()
    ]
    logging.info(len(issuelist))
    # if gfibot.issuedataset not exists, add it
    if "issuedataset" in myclient["gfibot"].list_collection_names():
        logging.warning(
            "Collection %s already exists (%d documents), skipping",
            "issuedataset",
            myclient["gfibot"]["issuedataset"].count_documents(filter={}),
        )
        logging.info("Use --drop to drop all collections before re-initializing")
    else:
        with open("issuedataset.json", "r") as f:
            schema = json.load(f)
        myclient["gfibot"].create_collection(
            "issuedataset", validator={"$jsonSchema": schema}
        )
        addind = [
            "owner",
            "name",
            "number",
            "resolver_commit_num",
            "clst",
            "pro_star",
            "isslist",
            "propr",
            "rptcmt",
            "rptiss",
            "rptpr",
            "rptissues",
            "ownercmt",
            "owneriss",
            "ownerpr",
            "ownerissues",
            "procmt",
            "contributornum",
            "crtclsissnum",
            "openiss",
            "openissratio",
            "clsisst",
            "labels",
            "events",
            "commentusers",
            "rpthasevent",
            "rpthascomment",
            "NumOfCode",
            "NumOfUrls",
            "NumOfPics",
            "coleman_liau_index",
            "flesch_reading_ease",
            "flesch_kincaid_grade",
            "automated_readability_index",
            "LengthOfTitle",
            "LengthOfDescription",
            "commentnum",
            "title",
            "body",
            "comment",
        ]

        all_index = mydb.index_information()
        for ind in addind:
            if ind == "url":
                uni = True
            else:
                uni = False
            myclient["gfibot"]["issuedataset"].create_index(
                [(ind, pymongo.ASCENDING)],
                unique=uni,
            )

    myclient.close()
    with mp.Pool(mp.cpu_count() // 2) as pool:
        res = pool.starmap(get_feature, issuelist)
    logging("Finish")
