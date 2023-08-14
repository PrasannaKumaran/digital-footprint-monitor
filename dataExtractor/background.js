const downs = {};

chrome.alarms.create("History routine",
    { delayInMinutes : 5, periodInMinutes: 30}
);

chrome.alarms.create("Bookmarks routine",
    { delayInMinutes: 5, periodInMinutes: 1440}
);

chrome.downloads.onCreated.addListener(function (downloadItem) {
    downs[downloadItem.id] = {
        id: downloadItem.id,
        startTime: downloadItem.startTime,
        totalBytes: downloadItem.totalBytes,
        receivedBytes: 0,
        identity: null,
        mime: downloadItem.mime,
        danger: downloadItem.danger,
        url: downloadItem.url,
        incognito: downloadItem.incognito,
        referrer: downloadItem.referrer,
        endTime: null,
        status: null,
    };
});

async function processDownloadDelta(downloadDelta) {
    if (downloadDelta.state) {
        if (downloadDelta.state.current === "complete" || downloadDelta.state.current === "interrupted") {
            downs[downloadDelta.id].status = downloadDelta.state.current;
            try {
                const userInfo = await new Promise((resolve) => {
                    chrome.identity.getProfileUserInfo(resolve);
                });
                downs[downloadDelta.id].identity = userInfo;
            } catch (error) {
                console.error("Error getting user profile info:", error);
            }
            downs[downloadDelta.id].endTime = downloadDelta.endTime.current;
            const data = { download: downs[downloadDelta.id] };
            userDownloads(data);
            delete downs[downloadDelta.id];
        }
    }
}

function processAlarmData(alarm) {
    if (alarm.name === "History routine") {
        const recordedTime = new Date().getTime() - 30 * 60 * 1000;
        chrome.history.search({ text: '', maxResults: 2, startTime: recordedTime}, async function (pastData) {
            const userInfo = await new Promise((resolve) => {
                chrome.identity.getProfileUserInfo(resolve);
            });
            data = {
                history: pastData,
                recordedAt: recordedTime,
                identity: userInfo
            }
            routineData(data, 'periodicHistory');
        });
    }
    else if(alarm.name === "Bookmarks routine") {
        const recordedTime = new Date().getTime() - 30 * 60 * 1000;
        chrome.bookmarks.getTree(async function (bookMarks) {
            const userInfo = await new Promise((resolve) => {
                chrome.identity.getProfileUserInfo(resolve);
            });
            data = {
                bookmarks: bookMarks,
                recordedAt: recordedTime,
                identity: userInfo
            }
            routineData(data, 'periodicBookmarks');
        });
    }
}

chrome.downloads.onChanged.addListener(function (downloadDelta) {
    processDownloadDelta(downloadDelta);
});

chrome.alarms.onAlarm.addListener(function (alarm) {
    processAlarmData(alarm);
});

function routineData(data, routine) {
    if (routine === 'periodicHistory') {
        fetch('http://127.0.0.1:8000/routine/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'data': data,
                'routine': routine
            })
        })
            .then(response => response.json())
            .then(data => {
                console.log('Successfully sent user history to server:', data);
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }
    else if (routine === 'periodicBookmarks') {
        fetch('http://127.0.0.1:8000/routine/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'data': data,
                'routine': routine
            })
        })
            .then(response => response.json())
            .then(data => {
                console.log('Successfully sent user bookmark data to server:', data);
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }
}

function userDownloads(data) {
    fetch('http://127.0.0.1:8000/downloads/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())  
        .then(data => {
            console.log('Successfully sent user download data to server:', data);
        }
    )
        .catch(error => {
            console.error('Error:', error);
        }
    );  
}