import json
import pymongo
import requests
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

my_client = pymongo.MongoClient(settings.MONGO_DB_NAME)


def authorization(body):
    REDDIT_DATA = {
        'grant_type': 'password',
        'username': body['username'],
        'password': body['password']
    }
    try:
        REDDIT_AUTH = requests.auth.HTTPBasicAuth(
            settings.REDDIT_CLIENT_ID, settings.REDDIT_SECRET)
        response = requests.post(
            settings.REDDIT_BASE_URL + 'api/v1/access_token',
            data=REDDIT_DATA,
            headers={'user-agent': 'APP-NAME by REDDIT-USERNAME'},
            auth=REDDIT_AUTH
        )
        response = response.json()
    except:
        return 'error'
    return 'bearer ' + response['access_token']


@csrf_exempt
def redditProcessing(request):
    body = json.loads(request.body)
    username = body['username']
    limit = body['limit']
    token = authorization(body)
    headers = {
        'Authorization': token,
        'User-Agent': 'APP-NAME by REDDIT-USERNAME'
    }
    response = requests.get(settings.REDDIT_OAUTH_URL +
                            f'/user/{username}/upvoted?limit={limit}&t=week', headers=headers)
    try:
        upvoteData = []
        for post in response.json()['data']['children']:
            upvoteData.append(
                {
                    'username': username,
                    'thumbnail': post['data']['thumbnail'],
                    'url': post['data']['url'],
                    'listing': 'upvoted',
                    'title': post['data']['title'],
                    'subreddit': post['data']['subreddit'],
                    'subredditType': post['data']['subreddit_type'],
                    'author': post['data']['author'],
                    'upvote_ratio': post['data']['upvote_ratio'],
                    'ups': post['data']['ups'],
                    'downs': post['data']['downs'],
                    'score': post['data']['score'],
                    'created': post['data']['created'],
                    'num_comments': post['data']['num_comments'],
                    'subreddit_subscribers': post['data']['subreddit_subscribers'],
                    'nsfw': post['data']['over_18'],
                    'isVideo': post['data']['is_video'],
                }
            )
        dbname = my_client['redditData']
        collection_name = dbname["userRedditData"]
        collection_name.insert_many(upvoteData)
    except Exception as e:
        return e
    return render(request, 'bookmarks.html', {'data': upvoteData})
