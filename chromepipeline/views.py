import re
import json
import pymongo
from django.conf import settings
from django.shortcuts import render
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from corsheaders.defaults import default_headers
from django.views.decorators.http import require_http_methods

client = pymongo.MongoClient(settings.MONGO_DB_NAME)


@csrf_exempt
def routines(request):
    data = json.loads(request.body.decode('utf-8'))
    if data['routine'] == 'periodicHistory':
        historical_data = []
        for instances in data['data']['history']:
            historical_data.append({
                'data': instances,
                'identity': data['data']['identity']
            })
        dbName = client['userChromeData']
        collectionName = dbName['history']
        collectionName.insert_many(historical_data)
    else:
        leaf_nodes = extract_leaf_nodes(data["data"]["bookmarks"])
        dbName = client['userChromeData']
        collectionName = dbName['bookmarks']
        collectionName.insert_many(leaf_nodes)
    return render(request, 'bookmarks.html')


@csrf_exempt
def downloads(request):
    data = json.loads(request.body)
    dbName = client['userChromeData']
    collectionName = dbName['downloads']
    collectionName.insert_one(data['download'])
    return render(request, 'bookmarks.html', context=data)


def extract_leaf_nodes(bookmarks):
    leaf_nodes = []
    for bookmark in bookmarks:
        children = bookmark.get("children", [])
        if not children:
            leaf_nodes.append(bookmark)
        else:
            leaf_nodes.extend(extract_leaf_nodes(children))
    return extractLastWeek(leaf_nodes)


def extract_domain_name(url):
    domain_pattern = r"(?:http[s]?://)?(?:www\.)?([a-zA-Z0-9.-]+)"
    match = re.search(domain_pattern, url)
    if match:
        domain_name = match.group(1)
        return re.sub(r"\.[a-zA-Z0-9-]+$", "", domain_name)
    else:
        return None


def extractLastWeek(bookmarks):
    required_bookmarks = []
    timenow = int(datetime.timestamp(datetime.now() - timedelta(days=10)))
    for bookmark in bookmarks:
        if bookmark['dateAdded']/1000 < timenow:
            required_bookmarks.append(bookmark)
    required_bookmarks = list(map(lambda bookmark: {
        "domain": extract_domain_name(bookmark["url"]),
        "title": bookmark["title"],
        "url": bookmark["url"],
        "dateAdded": bookmark["dateAdded"],
    }, required_bookmarks))
    return required_bookmarks
