from flask import Flask, redirect, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import requests

import pymongo
import json
from bson import ObjectId
from datetime import datetime, date
from urllib import parse
import numpy as np

from typing import Dict, Final

import urllib.parse

import yagmail

from concurrent.futures import ThreadPoolExecutor
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

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
db_gfi_email: Final = 'gmail-email'


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
    language = request.args.get('lang')
    repos = gfi_db.get_collection(db_repos)
    res = repos.count_documents({})
    if (language != None and language != ''):
        res = repos.count_documents({'language': language})
    return {
        'code': 200,
        'result': res
    }


@app.route('/api/repos/detailed_info')
def get_repo_detailed_info():
    start_idx = request.args.get('start')
    req_size = request.args.get('length')
    lang = request.args.get('lang')
    if start_idx != None and req_size != None:
        start_idx = int(start_idx)
        req_size = int(req_size)
        repos = gfi_db.get_collection(db_repos)
        count = repos.count_documents({})
        if lang != None and lang != '':
            count = repos.count_documents({'language': lang})
        start_idx = max(0, start_idx)
        req_size = min(req_size, count)
        res = []
        if start_idx < count:
            repo_enum = repos.find({})
            if lang != None and lang != '':
                repo_enum = repos.find({'language': lang})
            for i, temp in enumerate(repo_enum):
                if i >= start_idx and i - start_idx < req_size:
                    res.append(json.dumps(temp, cls=JSONEncoder))
                    app.logger.info(temp['name'])
        return {
            'code': 200,
            'result': res,
        }
    else:
        abort(400)


@app.route('/api/repos/info')
def get_repo_info_by_name_or_url():
    repo_name = request.args.get('repo')
    repo_url = parse.unquote(request.args.get('url'))
    app.logger.info(repo_url)
    user_name = request.args.get('user')

    if repo_url:
        repo_name = repo_url.split('.git')[0].split('/')[-1]
        
    app.logger.info(
        'repo_name: {}, repo_url: {}, user_name: {}'.format(repo_name, repo_url, user_name)
    )

    if repo_name:
        app.logger.info(repo_name)
        repos = gfi_db.get_collection(db_repos)
        if repos.count_documents({ 'name': repo_name }) > 0:
            repo = repos.find_one({ 'name': repo_name })
            return {
                'code': 200,
                'result': {
                    'name': repo['name'],
                    'owner': repo['owner'],
                }
            }
        elif repo_url == '':
            return {
                'code': 404,
                'result': 'Repo not found'
            }
        else:
            get_gfi_by_repo_url(repo_url, user_name)
            return {
                'code': 200,
                'result': '',
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


@app.route('/api/repos/get_gfi')
def get_gfi_by_repo_name_or_url():
    repo_name = request.args.get('repo_name')
    repo_url = request.args.get('repo_url')
    github_id = request.args.get('github_id')
    if repo_name != None:
        gfi_list = get_gfi_by_repo_name(repo_name)
        if gfi_list != None:
            return {
                'code': 200,
                'result': gfi_list,
            }
        else:
            return {
                'code': 404,
                'result': 'repo not found'
            }
    elif repo_url != None and github_id != None:
        gfi_container = get_gfi_by_repo_url(repo_url, github_id)
        if gfi_container != None:
            return {
                'code': 200,
                'result': gfi_container,
            }
        else:
            return {
                'code': 200,
                'result': 'request submitted',
            }
    else:
        return {
            'code': 400,
            'result': 'Bad request'
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
        gfi_list = get_gfi_by_repo_name(repo_name)
        if gfi_list != None:
            return {
                'code': 200,
                'result': gfi_list,
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
                            'queries': [],
                            'finished_queries': []
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


def get_gfi_by_repo_name(repo_name):
    if repo_name != None:
        issues = gfi_db.get_collection(db_issue_dataset)
        res = []
        if issues.count_documents({ 'name': repo_name }) > 0:
            for temp in issues.find({ 'name': repo_name }):
                res.append(temp['number'])
            res = np.random.choice(res, size=5).tolist()
            return res
    return []


@app.route('/api/repos/searches')
def get_processing_requests():
    user_name = request.args.get('user')
    should_clear_session = request.args.get('clear_session')
    github_id = gfi_db.get_collection(db_gfi_users).find_one({'github_name': user_name})['github_id']

    if github_id != None:
        processing_quires = gfi_db.get_collection(db_gfi_users).find_one({'github_id': github_id})['queries']
        user_succeed_queries = gfi_db.get_collection(db_gfi_users).find_one({'github_id': github_id})['finished_queries']
        app.logger.info('should clear session: {}'.format(should_clear_session))
        if should_clear_session != None:
            app.logger.info('clear session !')
            gfi_db.get_collection(db_gfi_users).find_one_and_update({'github_name': user_name}, generate_update_msg({'queries': [], 'finished_queries': []}))
        return {
            'code': 200,
            'result': {
                'user_query_num': len(processing_quires),
                'user_succeed_queries': ['material-ui' for i in user_succeed_queries], # for debug
            }
        }
    return {
        'code': 404,
        'result': 'user not found'
    }

executor = ThreadPoolExecutor(max_workers=10)

def get_gfi_by_repo_url(repo_url, github_name):
    repo_name = repo_url.split('.git')[0].split('/')[-1]
    res = get_gfi_by_repo_name(repo_name)
    if res:
        return res
    else:
        app.logger.info('repo not found, start to process')
        app.logger.info('github id: {}'.format(github_name))
        processing_queries = gfi_db.get_collection(db_gfi_users).find_one({'github_name': github_name})['queries']
        if repo_name not in processing_queries:
            processing_queries.append(repo_name)
            gfi_db.get_collection(db_gfi_users).find_one_and_update({'github_name': github_name}, generate_update_msg({'queries': processing_queries}))
            executor.submit(fetch_repo_gfi, repo_url, github_name)
        return []


def fetch_repo_gfi(repo_url, github_name):
    time.sleep(10)
    print('fetching repo gfi')
    repo_name = repo_url.split('.git')[0].split('/')[-1]
    # send_email(user_github_id, 'Fetching repo gfi succeed', repo_url)
    send_when_gfi_process_finished(repo_name, github_name)


def send_email(user_github_id, subject, body):
    """
    Send email to user
    """
    
    app.logger.info('send email to user {}'.format(user_github_id))

    user_email = gfi_db.get_collection(db_gfi_users).find_one({'github_name': user_github_id})['github_email']

    email = gfi_db.get_collection(db_gfi_email).find_one({})['email']
    password = gfi_db.get_collection(db_gfi_email).find_one({})['password']

    app.logger.info('Sending email to {} using {}'.format(user_email, email))
    
    if user_email != None:
        yag = yagmail.SMTP(email, password)
        yag.send(user_email, subject, body)
        yag.close()


# using websocket to handle user query

@socketio.on('connect', namespace='/gfi_process')
def connect_gfi_process():
    """
    Process socketio connection
    """
    app.logger.info('gfi_process connected')
    emit('socket_connected', {'data': 'Connected'})


@socketio.on('disconnect', namespace='/gfi_process')
def disconnect_gfi_process():
    """
    Process socketio disconnection
    """
    app.logger.info('gfi_process disconnected')


def send_when_gfi_process_finished(repo_name, user_name):
    """
    Send message to client when gfi process finished
    """

    app.logger.info('gfi_process finished')

    processing_queries = gfi_db.get_collection(db_gfi_users).find_one({'github_name': user_name})['queries']
    processing_queries.remove(repo_name)
    gfi_db.get_collection(db_gfi_users).find_one_and_update({'github_name': user_name}, generate_update_msg({'queries': processing_queries}))

    user_succeed_queries = gfi_db.get_collection(db_gfi_users).find_one({'github_name': user_name})['finished_queries']
    if repo_name not in user_succeed_queries:
        user_succeed_queries.append(repo_name)
        gfi_db.get_collection(db_gfi_users).find_one_and_update({'github_name': user_name}, generate_update_msg({'finished_queries': user_succeed_queries}))

    app.logger.info('gfi_process finished?')
    emit('socket_connected', {'data': 'material-ui'}, namespace='/gfi_process')
    app.logger.info('gfi_process finished')


socketio.run(app, debug=True)
    