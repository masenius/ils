#!/usr/bin/env python

#System
import urllib3
import pickle
import os.path
from bs4 import BeautifulSoup
import time
from datetime import datetime 
from queue import Queue
from threading import Thread
import json
import sys

urllib3.disable_warnings()

class Video:
	def __init__(self, url):
		self.url = url
		
	def parse(self, http=None):
		if http == None:
			http = urllib3.PoolManager()
		r = http.request('GET', self.url, headers={'User-Agent' : "Chrome"})
		s = BeautifulSoup(r.data)

		self.title = s.title.text.split(' - ')[0]
		for item in s.find_all('div',class_='bold'):
			if "Posted" in item.text:
				self.date = datetime.strptime(item.next_sibling.text, '%B %d, %Y')
			if "Source" in item.text:
				self.video_url = item.next_sibling.text
		self.tags = []
		for item in (s.find_all('ul', class_='post_tags')):
			for tag in item.find_all('a'):
				self.tags.append(tag.text)

		self.shares = 0

def index():
	http = urllib3.PoolManager(100)

	#Threading
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

	if os.path.isfile('videos.p'):
		f = open('videos.p','rb')
		video_list = pickle.load(f)
		f.close()

		for video in video_list:
			video_url_list.append(video.url)

	r = http.request('GET','http://iloveskydiving.org/', headers={'User-Agent' : "Magic Browser"})
	i = 0
	done = False

	while (done != True and r.status != 404):
		s = BeautifulSoup(r.data)
		href = s.find_all("a", class_="moretag")
		video_url_list_tmp = []

		for link in href:
			url = link.get("href")
			print("Video for consideration: " + url)
			if url not in video_url_list:
				if not '/photos/' in url:
					video_url_list_tmp.append(url)
			else:
				done = True
				break;

		video_url_list_new = video_url_list_new + video_url_list_tmp

		if done != True:
			i += 1
			r = http.request('GET','http://iloveskydiving.org/page/' + str(i+1) + '/', headers={'User-Agent' : "Magic Browser"})

	print(str(len(video_url_list_new)) + " new videos.")

	i = 0
	for url in video_url_list_new:
		video = Video(url)
		video_queue.put(video)
		video_list.insert(i, video)
		i += 1

	video_queue.join()

	print("Latest video: " + video_list[0].url)
	print("Total videos indexed: " + str(len(video_list)))

	f = open('videos.p','wb')
	pickle.dump(video_list, f)
	f.close()

def update_shares():
	video_list = []

	base_query = 'https://graph.facebook.com/?ids='

	if os.path.isfile('videos.p'):
		f = open('videos.p','rb')
		video_list = pickle.load(f)
		f.close()

	query_list = []

	i=0
	tmp_list = []

	while (i < len(video_list)):
		tmp_list.append(video_list[i].url)
		if (i % 500 == 0 and i != 0 or i == len(video_list) - 1):
			query_list.append(base_query + ','.join(tmp_list))
			tmp_list = []
		i += 1

	http = urllib3.PoolManager()

	j = {}
	for query in query_list:
		r = http.request('GET', query)
		if (r.status == 200):
			j.update(json.loads(r.data.decode('utf-8')))
		else:
			print (r.data)

	for video in video_list:
		try:
			video.shares = j[video.url]['shares']
		except:
			print("Warning: Could not find shares for: " + video.url)

	f = open('videos.p','wb')
	pickle.dump(video_list, f)
	f.close()

def generate_site(path):
	video_list = []

	if os.path.isfile('videos.p'):
		f = open('videos.p','rb')
		video_list = pickle.load(f)
		f.close()

	video_list.sort(key=lambda x: x.date, reverse=True)

	f = open('case.inc','r')
	html = f.read()
	f.close()

	rows = ""
	for video in video_list:
		rows += '<tr>\n'
		rows += '<td class="date"><div style="width: 100px" >' + video.date.strftime("%Y-%m-%d") + '</div></td>\n'
		rows += '<td class="shares">' + str(video.shares) + '</td>\n'
		rows += '<td class="title"><a href=' + video.url + ' target="_blank">' + video.title + '</a></td>\n'
		rows += '<td class="tags">' + ' '.join(video.tags) + '</td>\n'
		rows += '</tr>\n'

	table = '<table>\n' + '<tbody class="list">\n' + rows + '</tbody>\n' + '</table>'

	html = html.replace('&replace&', table)


	f = open(path, 'w')
	f.write(html)
	f.close()

def main(argv=None):
	if argv is None:
		argv = sys.argv

	if len(argv) != 2:
		print("Usage: ils.py path-to-index.htm")
		sys.exit(1)

	print("Looking for videos to add...")
	index()
	print("Updating share count...")
	update_shares()
	print("Generating site...")
	generate_site(argv[1])

if __name__ == "__main__":
    main()