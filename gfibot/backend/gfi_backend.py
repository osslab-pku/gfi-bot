from flask import Flask, redirect, request
from flask_cors import CORS

import pymongo
import json
from bson import ObjectId
from datetime import datetime, date

from typing import Dict, Final

import requests

import urllib.parse

import numpy as np

app = Flask(__name__)

if app.debug:
    app.logger.info('enable CORS')
    CORS(app, supports_credentials=True)

MONGO_URI : Final = 'mongodb://localhost:27017/'
db_client = pymongo.MongoClient(MONGO_URI)
gfi_db = db_client['gfi-bot']

db_issue_dataset : Final = 'issuedataset'
db_issues : Final = 'issues'
db_repos : Final = 'repos'
db_repos_commits : Final = 'repos.commits'
db_repos_issues : Final = 'repos.issues'
db_repos_stars : Final = 'repos.stars'
db_gfi_users : Final = 'gfi-users'
db_github_tokens : Final = 'github-tokens'


def generate_update_msg(dict: Dict) -> Dict:
    return { '$set': dict }


class JSONEncoder(json.JSONEncoder):
    """
    A Modified JSON Encoder 
    Deal with datatypes that can't be encoded by default
    """
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        elif isinstance(o, (datetime, date)):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)
        

@app.route('/api/repos/num')
def get_repo_num():
    repos = gfi_db.get_collection(db_repos)
    return {
        'code': 200,
        'result': repos.count_documents({})
    }


@app.route('/api/repos/info')
def get_repo_info():
    start_idx = request.args.get('start')
    req_size = request.args.get('length')
    if start_idx != None and req_size != None:
        start_idx = int(start_idx)
        req_size = int(req_size)
        repos = gfi_db.get_collection(db_repos)
        count = repos.count_documents({})
        start_idx = max(0, start_idx)
        req_size = min(req_size, count)
        res = []
        if start_idx < count:
            for i, temp in enumerate(repos.find()):
                if i >= start_idx and i - start_idx < req_size:
                    res.append(json.dumps(temp, cls=JSONEncoder))
                    app.logger.info(temp['name'])
        return {
            'code': 200,
            'result': res,
        }
    else:
        abort(400)


@app.route('/api/repos/language')
def get_deduped_repo_languages():
    repos = gfi_db.get_collection(db_repos)
    languages = repos.distinct('language')
    return {
        'code': 200,
        'result': languages
    }


GITHUB_LOGIN_URL : Final = 'https://github.com/login/oauth/authorize'

@app.route('/api/user/github/login')
def github_login():
    """
    Process Github OAuth login procedure
    """
    client_id = gfi_db.get_collection(db_github_tokens).find_one({})['client_id']
    return {
        'code': 200,
        'result': GITHUB_LOGIN_URL + '?client_id=' + client_id
    }


@app.route('/api/repos/recommend')
def get_recommend_repo():
    """
    get recommened repo name (currently using random)
    """
    repos = gfi_db.get_collection(db_repos).find({})
    res_list = []
    for repo in repos:
        res_list.append({ 
            'name': repo['name'],
            'owner': repo['owner'],
        })
    res = np.random.choice(res_list, size=1).tolist()[0]
    return {
        'code': 200,
        'result': res
    }
  
  
@app.route('/api/issue/num')
def get_issue_num():
    issues = gfi_db.get_collection(db_issue_dataset)
    return {
        'code': 200,
        'result': issues.count_documents({})
    }

  
@app.route('/api/issue/gfi')
def get_issue_info():
    """
    get random issues by repo name
    """
    repo_name = request.args.get('repo')
    if repo_name != None:
        issues = gfi_db.get_collection(db_issue_dataset)
        res = []
        if issues.count_documents({ 'name': repo_name }) > 0:
            for temp in issues.find({ 'name': repo_name }):
                res.append(temp['number'])
            res = np.random.choice(res, size=5).tolist()
            return {
                'code': 200,
                'result': res,
            }
        else:
            return {
                'code': 404,
                'result': 'repo not found'
            }
    else:
        abort(400)
    

@app.route('/api/user/github/callback')
def github_login_redirect():
    """
    Process Github OAuth callback procedure
    """
    code = request.args.get('code')

    client_id = gfi_db.get_collection(db_github_tokens).find_one({})['client_id']
    client_secret = gfi_db.get_collection(db_github_tokens).find_one({})['client_secret']

    if client_id == None or client_secret == None:
        abort(500)

    if code != None:
        r = requests.post('https://github.com/login/oauth/access_token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
        })
        if r.status_code == 200:
            app.logger.info(r.text)
            res_dict = dict(urllib.parse.parse_qsl(r.text))
            access_token = res_dict['access_token']
            if access_token != None:
                r = requests.get('https://api.github.com/user', headers={
                    'Authorization': 'token ' + access_token
                })
                if r.status_code == 200:
                    user_res = json.loads(r.text)
                    user_collection = gfi_db.get_collection(db_gfi_users)
                    user_data = {
                            'github_id': user_res['id'],
                            'github_login': user_res['login'],
                            'github_name': user_res['name'],
                            'github_avatar_url': user_res['avatar_url'],
                            'github_access_token': access_token,
                            'github_email': user_res['email'],
                            'github_url': user_res['url'],
                            'twitter_user_name': user_res['twitter_username'],
                        }
                    if user_collection.find_one_and_update({'github_id': user_res['id']}, generate_update_msg({'github_access_token': access_token})) == None:
                        user_collection.insert_one(user_data)
                    return redirect('/login/redirect?github_name={}&github_id={}&github_token={}&github_avatar_url={}'.format(user_res['name'], user_res['id'], access_token, user_res['avatar_url']), code=302)
                return {
                    'code': r.status_code,
                    'result': r.text
                }
            else:
                return {
                    'code': 400,
                    'result': 'access_token is None',
                }
        else:
            return {
                'code': r.status_code,
                'result': 'Github login failed',
            }
    else:
        return {
            'code': 400,
            'result': 'No code provided',
        }
