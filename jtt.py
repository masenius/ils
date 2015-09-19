#!/usr/bin/env python

# System
import urllib3
import pickle
import os.path
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
from queue import Queue
from threading import Thread
import json
import sys
import getopt
import time

urllib3.disable_warnings()


class Video:
    def __init__(self, url):
        self.url = url

    def parse(self, http=None):
        if http is None:
            http = urllib3.PoolManager()

        done = False
        tries = 0
        while not done and tries < 3:
            try:
                r = http.request('GET',  self.url, headers={'User-Agent': "Chrome"})
                done = True
            except:
                print("Request timed out. Trying again...")
                time.sleep(60)
                tries = tries + 1

        if (r.status == 200):
            s = BeautifulSoup(r.data, "lxml")

            for item in s.find_all('h2'):
                self.title = item.text

            for item in s.find_all('div', class_='description'):
                self.description = item.text

            for item in s.find_all('iframe'):
                video_url = item.get('data-src').split('?')[0]
                if 'youtube' in video_url:
                    self.video_url = 'https://www.youtube.com/watch?v=' + video_url.split('/')[-1]
                elif 'vimeo' in video_url:
                    self.video_url = 'https://vimeo.com/' + video_url.split('/')[-1]
                else:
                    self.video_url = 'http:' + video_url

            for item in s.find_all('div', class_="small-info"):
                datesrc = item.text.split(": ")[1]
                for d in datesrc.split():
                    if d.isdigit():
                        number = int(d)
                if "year" in datesrc:
                    self.date = datetime.today() - timedelta(days=365*number)
                elif "month" in datesrc:
                    self.date = datetime.today() - timedelta(days=30*number)
                elif "week" in datesrc:
                    self.date = datetime.today() - timedelta(weeks=number)
                elif "day" in datesrc:
                    self.date = datetime.today() - timedelta(days=number)
                elif "hour" in datesrc:
                    self.date = datetime.today() - timedelta(hours=number)
                else:
                    self.date = datetime.today()

            self.shares = 0
            self.delete = False
        else:
            self.delete = True


def findNewVideos(video_url_list):
    http = urllib3.PoolManager()
    base_url = 'http://jointheteem.com'
    r = http.request(
        'GET', base_url,
        headers={'User-Agent': "Magic Browser"})

    s = BeautifulSoup(r.data, "lxml")
    href = s.find_all("a", class_="thumb")
    video_url_list_new = []

    print (str(len(href)) + " videos for considerration.")
    for link in href:
        url = base_url + link.get("href")
        if url not in video_url_list:
            video_url_list_new.append(url)

    return video_url_list_new


def parseList(file):
    video_url_list_new = []
    with open(file, 'r') as f:
        for url in f:
            video_url_list_new.append(url.strip())
    return video_url_list_new


def index(redo=False):
    http = urllib3.PoolManager(100)

    # Threading
    num_video_threads = 100
    video_queue = Queue()

    def processVideos(q, pm):
        while True:
            video = q.get()
            print("Parsing video: " + video.url)
            video.parse()
            q.task_done()

    for i in range(num_video_threads):
        worker = Thread(target=processVideos, args=(video_queue, http,))
        worker.setDaemon(True)
        worker.start()

    video_url_list = []
    video_url_list_new = []
    video_list = []

    if os.path.isfile('videos.p') and redo is False:
        f = open('videos.p', 'rb')
        video_list = pickle.load(f)
        f.close()

        for video in video_list:
            video_url_list.append(video.url)
    else:
        video_url_list_new = parseList('default')

    video_url_list_new = video_url_list_new + findNewVideos(video_url_list)

    print(str(len(video_url_list_new)) + " new videos.")

    if len(video_url_list_new) > 0:

        i = 0
        for url in video_url_list_new:
            video = Video(url)
            video_queue.put(video)
            video_list.insert(i, video)
            i += 1

        video_queue.join()

        for video in video_list:
            if video.delete:
                video_list.remove(video)

        if redo and os.path.isfile('ils.p'):
            f = open('ils.p', 'rb')
            ils_video_list = pickle.load(f)
            f.close()

            for v in video_list:
                for u in ils_video_list:
                    if v.title == u.title:
                        v.date = u.date

        f = open('videos.p', 'wb')
        pickle.dump(video_list, f)
        f.close()

    print("Latest video: " + video_list[0].url)
    print("Total videos indexed: " + str(len(video_list)))


def update_shares():
    video_list = []

    base_query = 'https://graph.facebook.com/?ids='

    if os.path.isfile('videos.p'):
        f = open('videos.p', 'rb')
        video_list = pickle.load(f)
        f.close()

    query_list_url = []
    query_list_video_url = []

    i = 0
    tmp_list_url = []
    tmp_list_video_url = []

    while (i < len(video_list)):
        tmp_list_url.append(video_list[i].url)
        tmp_list_video_url.append(video_list[i].video_url)
        if (i % 500 == 0 and i != 0 or i == len(video_list) - 1):
            query_list_url.append(base_query + ','.join(tmp_list_url))
            query_list_video_url.append(base_query + ','.join(tmp_list_video_url))
            tmp_list_url = []
            tmp_list_video_url = []
        i += 1

    http = urllib3.PoolManager()

    j = {}
    for query in query_list_url:
        r = http.request('GET', query)
        if (r.status == 200):
            j.update(json.loads(r.data.decode('utf-8')))
        else:
            print(r.data)

    k = {}
    for query in query_list_video_url:
        r = http.request('GET', query)
        if (r.status == 200):
            k.update(json.loads(r.data.decode('utf-8')))
        else:
            print(r.data)

    i = 0
    for video in video_list:
        try:
            video.shares = j[video.url]['shares']
        except:
            i = i + 1

    print ("Info: " + str(i) + " urls could not be found.")

    i = 0
    for video in video_list:
        try:
            video.shares = int(video.shares) + int(k[video.video_url]['shares'])
        except:
            i = i + 1

    if os.path.isfile('ils.p'):
        f = open('ils.p', 'rb')
        ils_video_list = pickle.load(f)
        f.close()

        for v in video_list:
            for u in ils_video_list:
                if v.title == u.title:
                    v.shares = int(v.shares) + int(u.shares)

    print ("Info: " + str(i) + " video urls could not be found.")

    f = open('videos.p', 'wb')
    pickle.dump(video_list, f)
    f.close()


def generate_site(path):
    video_list = []

    if os.path.isfile('videos.p'):
        f = open('videos.p', 'rb')
        video_list = pickle.load(f)
        f.close()

    video_list.sort(key=lambda x: x.date, reverse=True)

    f = open('index.inc', 'r')
    html = f.read()
    f.close()

    rows = ""
    for video in video_list:
        rows += '<tr>\n'
        rows += '<td class="date"><div style="width: 100px" >' + video.date.strftime("%Y-%m-%d") + '</div></td>\n'
        rows += '<td class="shares">' + str(video.shares) + '</td>\n'
        rows += '<td class="title"><a href=' + video.url + ' target="_blank">' + video.title + '</a></td>\n'
        rows += '<td class="description">' + video.description + '</td>\n'
        rows += '</tr>\n'

    table = '<table>\n' + '<tbody class="list">\n' + rows + '</tbody>\n' + '</table>'

    html = html.replace('&replace&', table)

    f = open(path, 'w')
    f.write(html)
    f.close()


def main(argv):
    def printUsage():
        print("Usage: ils.py [-r] -o outfile")

    reindex = False
    outfile = ""

    try:
        opts, args = getopt.getopt(argv, "hro:")
    except:
        printUsage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            printUsage()
            sys.exit()
        elif opt == '-r':
            reindex = True
        elif opt in ("-o"):
            outfile = arg

    if outfile == "":
        printUsage()
        sys.exit(2)

    print("Looking for videos to add...")
    index(reindex)
    print("Updating share count...")
    update_shares()
    print("Generating site...")
    generate_site(outfile)

if __name__ == "__main__":
    main(sys.argv[1:])
