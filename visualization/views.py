import pymongo
import pandas as pd
import altair as alt
from django.conf import settings
from urllib.parse import urlparse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

my_client = pymongo.MongoClient(settings.MONGO_DB_NAME)


def getRecentHistoryData(history_df):
    history_df['lastVisitTime'] = pd.to_datetime(
        history_df['lastVisitTime'], unit='ms')
    history_df['timeFormated'] = history_df['lastVisitTime'].dt.strftime(
        '%d/%m/%Y %H:%M')
    history_df['dmy'] = pd.to_datetime(
        history_df['lastVisitTime'], unit='ms').dt.strftime('%d/%m/%Y')
    history_df['domain'] = history_df['url'].apply(
        lambda x: urlparse(x).netloc.split('.')[-2])
    daysAgo = pd.Timestamp.today() - pd.Timedelta(days=10)
    return history_df[(history_df['lastVisitTime'] >= daysAgo) & (history_df['lastVisitTime'] <= pd.Timestamp.today())]


def getRecentBookmarksData(bookmark_df, days=100):
    bookmark_df['dateAdded'] = pd.to_datetime(
        bookmark_df['dateAdded'], unit='ms')
    bookmark_df['timeFormated'] = bookmark_df['dateAdded'].dt.strftime(
        '%d/%m/%Y %H:%M')
    bookmark_df['dmy'] = pd.to_datetime(
        bookmark_df['dateAdded'], unit='ms').dt.strftime('%d/%m/%Y')
    bookmark_df['domain'] = bookmark_df['url'].apply(
        lambda x: urlparse(x).netloc.split('.')[-2])
    bookmark_df['dayOfWeek'] = bookmark_df['dateAdded'].dt.day_name()
    daysAgo = pd.Timestamp.today() - pd.Timedelta(days=days)
    return bookmark_df[(bookmark_df['dateAdded'] >= daysAgo) & (bookmark_df['dateAdded'] <= pd.Timestamp.today())]


def getRecentDownloadsData(downloads_df):
    downloads_df['referrer'] = downloads_df['referrer'].apply(
        lambda x: urlparse(x).netloc.split('.')[-2])
    downloads_df['endTime'] = pd.to_datetime(downloads_df['endTime'])
    days_ago = pd.Timestamp.utcnow() - pd.Timedelta(days=10)  # Convert to UTC time
    records_within_10_days = downloads_df[downloads_df['endTime'] >= days_ago]
    records_within_10_days['endTime'] = records_within_10_days['endTime'].dt.strftime(
        "%d/%m/%Y %H:%M")
    return records_within_10_days


def visitActivity(history_df):
    records_within_10_days = getRecentHistoryData(history_df)
    activityPlotData = records_within_10_days.groupby(['timeFormated', 'domain']).agg({
        'visitCount': 'sum',
        'domain': 'size'
    }).rename(columns={'domain': 'domainCount'}).reset_index()

    brush = alt.selection_interval()
    color_palette = 'inferno'
    points = alt.Chart(activityPlotData).mark_point(shape='triangle').encode(
        x=alt.X('timeFormated', title='Date and Time', axis=alt.Axis(
            labelAngle=60, tickCount=activityPlotData.shape[0] // 10, labelFontSize=8)),
        y=alt.Y('visitCount').title('Total Current Visits'),
        color=alt.Color('domain:N', title='Domain name',
                        scale=alt.Scale(scheme=color_palette)),
        tooltip=alt.Tooltip('timeFormated'),
    ).add_selection(brush).properties(width=400)

    bars = alt.Chart(activityPlotData).mark_bar(orient='horizontal').encode(
        y=alt.Y('domain').title('Domain'),
        x=alt.X('domainCount').title('Total Visits'),
        opacity=alt.value(0.8),
        color=alt.Color('domain:N', title='Domain name',
                        scale=alt.Scale(scheme=color_palette)),
        tooltip=alt.Tooltip('domainCount:N', title='Domain visits')
    ).transform_filter(brush).properties(width=400)

    return points & bars


def mostVisited(history_df, k=10):
    records_within_10_days = getRecentHistoryData(history_df)
    titleGroup = records_within_10_days.groupby(['title']).agg({
        'visitCount': 'sum',
    }).rename(columns={'domain': 'domainCount'}).reset_index()
    return alt.Chart(titleGroup).transform_window(
        rank='rank(visitCount)',
        sort=[alt.SortField('visitCount', order='descending')]
    ).transform_filter(
        alt.datum.rank <= k
    ).mark_bar().encode(
        y=alt.Y('title:N', title=''),
        x=alt.X('visitCount:Q', title='Number of visits'),
        color='visitCount:Q',
        tooltip=[alt.Tooltip('title:N'), alt.Tooltip('visitCount:Q')]
    ).properties(
        title=f'Top {k} most visited websites',
        resolve=alt.Resolve(scale={'color': 'independent'})
    ).interactive()


def bookMarksActivity(bookmarks_df):
    data = getRecentBookmarksData(bookmarks_df).groupby(['dayOfWeek', 'domain']).agg({
        'domain': 'sum',
        'domain': 'size'
    }).rename(columns={'domain': 'domainCount'}).reset_index().sort_values(by='domainCount', ascending=False)
    top_domains_weekly = (data.groupby('dayOfWeek')
                          .apply(lambda x: x.nlargest(3, 'domainCount'))
                          .reset_index(drop=True))
    color_palette = 'viridis'
    return alt.Chart(top_domains_weekly, title='Top 3 bookmarked domains each day in the past week').mark_bar().encode(
        x=alt.X('dayOfWeek:N', title='Day of Week',
                axis=alt.Axis(labelAngle=0,)),
        y=alt.Y('domainCount:Q', title='Number of visits'),
        color=alt.Color('domain:N', title='',
                        scale=alt.Scale(scheme=color_palette)),
        tooltip=['domain', 'domainCount']
    ).properties(width=200, height=300, resolve=alt.Resolve(scale={'color': 'independent'})).interactive()


def bookMarksCounts(bookmarks_df):
    data = getRecentBookmarksData(bookmarks_df)
    numberOfbookmarks = data.groupby(
        'dayOfWeek')['dayOfWeek'].count().reset_index(name='count')
    return alt.Chart(numberOfbookmarks, title='Days vs No. of bookmarks').mark_line().encode(
        x=alt.X('dayOfWeek', title='Day of Week',
                axis=alt.Axis(labelAngle=0,)),
        y=alt.Y('count', title='Total bookmarks'),
    ).properties(width=200, resolve=alt.Resolve(scale={'color': 'independent'}))


def mimeInformation(download_df):
    color_palette = 'category20b'
    mime_counts = download_df['mime'].value_counts().reset_index()
    mime_counts.columns = ['mime', 'count']
    return alt.Chart(mime_counts, title='Distribution of downloaded file types').mark_arc(innerRadius=50).encode(
        theta=alt.Theta("count", title="Number of files"),
        color=alt.Color("mime:N", title='File type',
                        scale=alt.Scale(scheme=color_palette)),
        tooltip=[alt.Tooltip('count', title='Number of files'),
                 alt.Tooltip('mime', title='Type')]
    ).properties(resolve=alt.Resolve(scale={'color': 'independent'}))


def nsfwInformation(download_df):
    danger = download_df.groupby(['danger', 'status']).agg({
        'status': 'sum',
        'status': 'size'
    }).rename(columns={'status': 'statusCount'}).reset_index().sort_values(by='statusCount', ascending=False)
    color_palette = 'tableau10'
    return alt.Chart(danger, title='File Security and Status Information').mark_bar(opacity=0.8).encode(
        y=alt.Y('status:O', title='', axis=alt.Axis(labelAngle=0,)),
        x=alt.X('statusCount:Q', title='Number of downloads').stack(None),
        color=alt.Color('danger:N', title='',
                        scale=alt.Scale(scheme=color_palette)),
        row=alt.Row('danger:N', title='')
    ).properties(resolve=alt.Resolve(scale={'color': 'independent'}))


def referrerInformation(download_df):
    referrer_df = download_df.groupby(['referrer']).agg({
        'referrer': 'size',
    }).rename(columns={'referrer': 'refcount'}).reset_index()
    example = pd.DataFrame([{'referrer': 'yahoo', 'refcount': 2}])
    referrer_df = pd.concat([referrer_df, example])

    color_palette = 'set1'
    base = alt.Chart(referrer_df, title='Information about number of downloads associated with a referrer').encode(
        theta=alt.Theta("refcount:Q").stack(True),
        radius=alt.Radius("refcount").scale(
            type="sqrt", zero=True, range=[20, 100]),
        color=alt.Color("referrer:N", title='Referrer',
                        scale=alt.Scale(scheme=color_palette)),
        opacity=alt.value(0.8),
        tooltip=[alt.Tooltip('refcount', title='Number of visits'), alt.Tooltip(
            'referrer', title='Referrer')]
    )
    pie = base.mark_arc(outerRadius=120).properties(
        resolve=alt.Resolve(scale={'color': 'independent'}))
    return pie


@csrf_exempt
def chart_view(request):
    history_collection = my_client['userChromeData']['history']
    retrieved = history_collection.find({})
    history_data = []
    for histData in retrieved:
        history_data.append(histData['data'])
    history_df = pd.DataFrame(history_data)

    uservisitActivity = visitActivity(history_df)
    userMostVisited = mostVisited(history_df)
    historyCharts = alt.vconcat(
        uservisitActivity, userMostVisited).resolve_scale(color='independent')

    bookmark_collection = my_client['userChromeData']["bookmarks"]
    retrieved = bookmark_collection.find({})
    bookmarks_data = []
    for bookmark in retrieved:
        bookmarks_data.append(bookmark)
    bookmark_df = pd.DataFrame(bookmarks_data)
    stackedBookmarkChart = bookMarksActivity(bookmark_df)
    countsBookmarksChart = bookMarksCounts(bookmark_df)
    bookmarkCharts = alt.vconcat(
        stackedBookmarkChart, countsBookmarksChart).resolve_scale(color='independent')

    download_collection = my_client['userChromeData']['downloads']
    retrieved = download_collection.find({})
    download_data = []
    for download in retrieved:
        download_data.append(download)
    download_df = pd.DataFrame(download_data)
    download_df = getRecentDownloadsData(download_df)
    mimeDataChart = mimeInformation(download_df)
    dangerDataChart = nsfwInformation(download_df)
    referrerChart = referrerInformation(download_df)
    downloadCharts = alt.vconcat(
        mimeDataChart, dangerDataChart, referrerChart).resolve_scale(color='independent')

    allCharts = alt.hconcat(historyCharts, bookmarkCharts, downloadCharts)
    return HttpResponse(allCharts.to_html(), content_type='text/html')
