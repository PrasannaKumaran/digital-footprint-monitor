import json
import openai
import pymongo
import requests
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

client = pymongo.MongoClient(settings.MONGO_DB_NAME)
openai.api_key = settings.OPENAI_API_KEY


def get_embedding(text, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model=model)['data'][0]['embedding']


def authorization(body):
    REDDIT_DATA = {'grant_type': 'password',
                   'username': body['username'], 'password': body['password']}
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
def redditQuery(request):
    data = json.loads(request.body)
    token = authorization(data)
    try:
        if token:
            collection = client['redditData']['userRedditData']
            query = data['query']
            num_posts = int(data['numposts'])
            pipeline = settings.SEARCH_PIPELINE
            vector_query = get_embedding(query)
            pipeline[0]['$search']['knnBeta']['vector'] = vector_query
            pipeline[0]['$search']['knnBeta']['k'] = num_posts
            pipeline[2]['$match']['username'] = data['username']
            cursor = collection.aggregate(pipeline)
            redditData = []
            for doc in cursor:
                redditData.append(doc)
            return JsonResponse({'response': redditData}, safe=False)
        else:
            return JsonResponse({'error': 'invalid credentials'})
    except:
        return JsonResponse({'error': 'error'})


@csrf_exempt
def searchQuery(request):
    return render(request, 'search.html')


@csrf_exempt
def displayRedditData(request):
    data = request.GET.get('data', '{}')
    data = json.loads(data)
    return render(request, 'display.html', {'response': data['response']})
