from flask import Flask, request
from flask_cors import CORS

import pymongo
import json
from bson import ObjectId
from datetime import datetime, date

from typing import Final

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


@app.route('/')
def hello_world():
    return '<p> hello world </p>'


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
        if start_idx < count:
            res = []
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


