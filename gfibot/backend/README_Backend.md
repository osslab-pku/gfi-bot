# GFI-Bot

![Python Lint](https://github.com/osslab-pku/gfi-bot/actions/workflows/python-lint.yml/badge.svg)
![GFI-Bot Tests](https://github.com/osslab-pku/gfi-bot/actions/workflows/test-gfi-bot.yml/badge.svg)
![GFI-Bot Coverage](https://img.shields.io/codecov/c/github/osslab-pku/gfi-bot?label=GFI-Bot%20Coverage)
![License](https://img.shields.io/github/license/osslab-pku/gfi-bot?label=License)
[![GFI-Bot](https://gfibot.io/api/repo/badge?owner=osslab-pku&name=gfi-bot)](https://gfibot.io/?owner=osslab-pku&name=gfi-bot)

ML-powered 🤖 for finding and labeling good first issues in your GitHub project!

GFI-Bot Backend Routes Description
Route-->`/api/repos/num`
Get the no of repos for good first issue by filtering with
1)Language
2)Sort by option

Route-->`/api/repos/info`
Search for the repos for gfi to fetch
1)name
2)owner
3)Small Description
4)Language
5)Topics

Route-->`/api/repos/info/detail`
It returns the name and owner of the repos with filtering  
sort by option like:  
"popularity",  
"median_issue_resolve_time",  
"newcomer_friendly",  
"gfis"  

Route-->`/api/repos/info/search`  
This route takes user search request by typing   
1)repo name or   
2)repo url  

Route-->`/api/repos/add`  
If user want to add any issue to the bot they can add with     
repo_name, repo_owner, and their own user_name  

Route-->`/api/repos/recommend`  
Recommendation by thr gfi-bot currently it is random  

Route-->`/api/repos/language`  
Searching gif for the specific language  

Route-->`/api/repos/update/`  
To update any repo information(query is resolved or unresolved)

Route-->`/api/issue/gfi`
Get GFI issue from repo with repo_name and repo_owner

Route-->`/api/issue/gfi/num`
Get no of GFi by repo name

Route-->`/api/user/github/login`
User auth0 login with github

Route-->`/api/model/training/result`
GFi probability result with percentage

Route-->`/api/user/queries`
The user queries details like added and deleted by the user

Route-->`/api/user/searches`
the specific search made by the user

Route-->`/api/github/app/installation`
Adding gifibot to any repo 

Route-->`/api/github/actions/webhook`
Webhook action process by github app

Route-->`/api/repo/badge`
Automate generate github readme badge for some repo
