"""
	https://dev.twitter.com/rest/public
	Twitter API
	Based off of tapi.py
"""
service = 'twitter'
import socket, shutil, requests, re, os, time, datetime, json, logging, threading









def create_oauth(access_token='', access_token_secret=''):
	"""Usage: session.get(url), session.post(url, body=None, json=None, **kwargs)"""
	from rauth import OAuth1Service
	twitter = OAuth1Service(
		name='twitter',
		consumer_key='',
		consumer_secret='',
		request_token_url='https://api.twitter.com/oauth/request_token',
		access_token_url='https://api.twitter.com/oauth/access_token',
		authorize_url='https://api.twitter.com/oauth/authorize',
		base_url='https://api.twitter.com/1.1/')
	session = twitter.get_session((access_token, access_token_secret))
	return session


















#
#
# Utilities
#
#




def dmake(d):
	if not os.path.exists(d): os.makedirs(d)
def fmake(f):
	if not os.path.exists(f): open(f, 'a').close()
def url_split(url):
	return re.search(r'(?:.*://)?(.+?)(/.+)', url).groups()
def test_net():
	try: return bool(socket.create_connection((socket.gethostbyname('www.google.com'), 80), 2))
	except: return False
def make_host_name(name):
	return name+'.tumblr.com'
def increment_filename(fn):
	if not os.path.exists(fn):
		return fn
	i = 1
	while os.path.exists( '%s_%d'% (fn, i)):
		i += 1
	return fn+str(i)
def chunkify(l, n):
	for i in xrange(0, len(l), n):
		yield l[i:i+n]
def date_increment_filename(fn):
	date = time.strftime("%Y-%m-%d")
	new_fn = increment_filename( '%s_%s'%(fn, date) )
	os.rename(fn, new_fn)
	return open(fn, 'wb')
def _find(lst, key, value):
	for i, dic in enumerate(lst):
		if dic[key] == value:
			return i
	return -1
def write_pages(farg, pages):
	size_limit = 1024*1024*2
	wfd = open(farg,'ab')
	for page_index in reversed(sorted(pages)):
		if os.stat(farg).st_size > size_limit:
			wfd.close()
			wfd = date_increment_filename(farg)
		f = pages[page_index]
		with open(f,'rb') as fd:
			shutil.copyfileobj(fd, wfd)
	wfd.write(',\n')
	wfd.close()
def create_temp(dusr, fn, posts, page_index):
	# remove self, give dusr
	temp_name = os.path.join(dusr, '%s%d'%(fn, page_index))
	with open(temp_name, 'w') as nctn:
		nctn.write(json.dumps(list(reversed(posts)), indent=1, sort_keys=True).decode('unicode-escape').encode('utf8'))
	return temp_name
def delete_temp_files(pages):
	for page_index in pages:
		fn = pages[page_index]
		os.remove(fn)

def getFromDict(dataDict, mapList):
	return reduce(lambda d, k: d[k], mapList, dataDict)

def setInDict(dataDict, mapList, value):
	getFromDict(dataDict, mapList[:-1])[mapList[-1]] = value

def record_changes(obj, keys, key, value):
	for _ in xrange(len(keys)+10):
		try:
			setInDict(obj, keys+[key], value)
			return obj
		except:
			for i in range(len(keys)+1)[1:]:
				try:
					assert isinstance(getFromDict(obj, keys[:i]), dict)
				except:
					setInDict(obj, keys[:i], {})
	else:
		raise Exception

def compare_object(N, record):
	changes = {}
	D = N.copy()
	nested_keys = []
	for key in D:
		if isinstance(D[key], dict) and D[key]:
			nested_keys.append([key])
		else:
			if D[key] != record.get(key, None):
				record[key] = D[key]
				changes[key] = D[key]
	for keys in nested_keys:
		d = getFromDict(N, keys)
		for key in d:
			if isinstance(d[key], dict) and d[key]:
				nested_keys.append(keys+[key])
			else:
				try:
					if d[key] != getFromDict(record, keys+[key]):
						setInDict(record, keys+[key], d[key])
						changes = record_changes(changes, keys, key, d[key])
				except:
					record = record_changes(record, keys, key, d[key])
					changes = record_changes(changes, keys, key, d[key])
	return [record, changes]






#
#
# Utilities
#
#















































































































def _load_account():
	""" { 'id':0, 'name':'', 'cookie':'', 'access':'', 'access_secret':'' } """
	return settings['accounts'][0]

def _load_api(acc):
	global s # session
	s = create_oauth(acc['access'], acc['access_secret'])

def create_user(name):
	with top.lock:
		settings['users'].append({ 'id': len(settings['users']), 'tid':0, 'active': True, 'root_name': name, 'name': name, 'recovery': { 'close_friend':None }, 'last_pid': 0, 'last_updated': 0, 'state': 'new', 'ppd': '1990-04-12 17:07:11', 'fail_count': 0, 'subdir': '', 'new_user': True })

def test_input_name(name):
	test_result = _find(settings['users'], 'name', name)
	name_not_found = test_result < 0
	if name_not_found:
		create_user(name)
	return settings['users'][test_result]['id']

def set_account(account_name='', account_id=None):
	if account_name:
		account_id = _find(settings['accounts'], 'name', account_name)
	settings['accounts'].insert(0, settings['accounts'].pop(account_id))






































































#
#
# Service
#
#



class Service(object):

	def __init__(self, obj):
		"""Argument obj: the controller instance."""
		global top
		global errors
		global output
		global svc
		global settings
		top = obj
		svc = self
		errors = logging.getLogger('errors')
		output = logging.getLogger('output')
		settings = top.settings[service]
		self.threads = []
		self.string_time = time.strftime("%Y-%m-%d %H:%M:%S")
		self.start_time = datetime.datetime.strptime(self.string_time, '%Y-%m-%d %H:%M:%S')
		self.raise_hell = False
		self.look_infoz = False
		self.bork = False
		self.dsvc = os.path.join(top.d_root, 'tw')
		ppc = datetime.datetime.strptime(settings['ppc'], '%Y-%m-%d %H:%M:%S')
		pit = datetime.datetime.strptime(settings['pit'], '%Y-%m-%d %H:%M:%S')
		if (self.start_time - ppc).days > 3:
			self.raise_hell = True
		if (self.start_time - pit).seconds >= 3600:
			self.look_infoz = True

	def open_settings(self):
		if not settings:
			settings = {'ppc':'', 'pit':'', 'users':[], 'code_broken':False, 'accounts':[]}

	def close_settings(self):
		if self.raise_hell:
			settings['ppc'] = str(self.string_time)
		if self.look_infoz:
			settings['pit'] = str(self.string_time)
		if self.bork:
			settings['code_broken'] = True
			errors.critical('Catch-all CODE BROKE error report. By way of FAIL COUNT EXCEEDED switch trigger.\nThe code_broke switch must be manually reset.')
		# Might want to implement another error check for % of failed threads. Meh
		# Might want to do an internet test before running. done

	def new_user(self, name):
		# Not implementing any automatic creation here for now
		errors.error('%s: this name is still active', name)

	def run(self, todo_list):
		"""Argument todo_list: a list of usernames or null."""
		if not test_net():
			return False
		if todo_list:
			todo_list = [test_input_name(name) for name in todo_list]
		else:
			todo_list = [user['id'] for user in settings['users'] if user['active']]
		acc = _load_account()
		_load_api(acc)

		chunks = [todo_list[x:x+25] for x in xrange(0, len(todo_list), 25)]
		for chunk in chunks:
			threads = []
			heavy = []
			self.recovery = []
			for user_id in chunk:
				thread = Worker(user_id)
				if thread.heavy:
					heavy.append(thread)
				else:
					thread.start()
					threads.append(thread)
			for thread in threads:
				thread.join()
			for thread in heavy:
				thread.start()
				thread.join()
			for user_id in self.recovery:
				thread = Worker(user_id)
				thread.start()
				threads.append(thread)
			for thread in threads:
				thread.join()
			self.threads += threads + heavy
		self.close_settings()












#
#
# Service
#
#


































#
#
# User
#
#



class User(object):
	"""About: hold user info."""

	def __init__(self, user_id):
		self.id = user_id
		self._load_info()
		self._load_files()

	def where(self):
		if not self.tid:
			try:
				self.tid = find_tid(self.info['name'])
			except requests.exceptions.HTTPError as e:
				if e.response.status_code == 404:
					self.state = '404'
				else:
					raise

	def new_user(self):
		if self.info.get('new_user', False):
			del self.info['new_user']
			self.where()
			if os.path.exists(self.dusr):
				self.dusr = increment_filename(self.dusr)
				settings['users'][self.id]['root_name'] = os.path.basename(self.dusr)
				self.info['root_name'] = os.path.basename(self.dusr)

	def _load_info(self):
		"""Load the user's stats from the settings object. Copy it and update it afterward. last pid grabbed, tumblelog key, previous paged date"""
		info = settings['users'][self.id].copy()
		self.name = info['name']
		self.tid = info['tid']
		self.state = info['state']
		self.reference_pid = int(info['last_pid'])
		self.ppd = datetime.datetime.strptime(info['ppd'], '%Y-%m-%d %H:%M:%S')
		self.info = info

	def _load_files(self):
		self.dusr = os.path.join(svc.dsvc, self.info['root_name'])
		self.new_user()
		if self.info['subdir']:
			self.dusr = os.path.join(self.dusr, self.info['subdir'])
		self.ddump = os.path.join(self.dusr, 'dumps')
		self.dnotes = os.path.join(self.dusr, 'notes')
		self.dpages = os.path.join(self.dusr, 'pages')
		self.ffeed = os.path.join(self.dusr, 'feed')
		self.ffav = os.path.join(self.dusr, 'favorites')
		self.ffollows = os.path.join(self.dusr, 'follow')
		self.ffavids = os.path.join(self.dusr, 'favids')
		self.ffollowerids = os.path.join(self.dusr, 'folids')
		self.ffriendids = os.path.join(self.dusr, 'frieds')
		self.fuser = os.path.join(self.dusr, 'user')
		dmake(self.dusr)
		dmake(self.ddump)
		dmake(self.dnotes)
		dmake(self.dpages)
		fmake(self.ffeed)
		fmake(self.ffav)
		fmake(self.ffollows)
		fmake(self.ffavids)
		fmake(self.ffollowerids)
		fmake(self.ffriendids)
		if not os.path.exists(self.fuser):
			with open(self.fuser, 'a') as nctn:
				nctn.write("""{"record": {}, "changes": {}}""")

#
#
# User
#
#











































#
#
# Worker
#
#

class Worker(threading.Thread):

	def __init__(self, user_id):
		threading.Thread.__init__(self)
		self.user = User(user_id)
		self.heavy = not bool(self.user.info['last_pid'])
		self.string_time = time.strftime("%Y-%m-%d %H:%M:%S")
		self.start_time = datetime.datetime.strptime(self.string_time, '%Y-%m-%d %H:%M:%S')
		self.failed = False
		self.exam_success = False

	def close_settings(self):
		if self.failed:
			self.user.info['fail_count'] += 1
			if self.user.info['fail_count'] > 4:
				svc.bork = True
		else:
			self.user.info['fail_count'] = 0 

		if self.user.info['state'] == '404':
			if self.user.state != '404':
				user_report(self.user.id, 'No longer 404')
		elif self.user.state == '404':
			user_report(self.user.id, 'IS DELETED!!')

		if self.user.info['state'] == 'empty':
			if self.user.state != 'empty':
				user_report(self.user.id, 'No longer empty')
		elif self.user.state == 'empty':
			user_report(self.user.id, 'IS EMPTY!!')

		self.user.info['name'] = self.user.name
		self.user.info['tid'] = self.user.tid
		self.user.info['state'] = self.user.state
		self.user.info['last_pid'] = self.user.reference_pid
		self.user.info['ppd'] = str(self.user.ppd)
		settings['users'][self.user.id] = self.user.info
		top.write_lists()

	def safely_start_page(self, target, args):
		for _ in range(300):
			if threading.active_count() < 205:
				try:
					t = threading.Thread(target=target, args=args)
					t.start()
					return t
				except:
					errors.exception(self.user)
					time.sleep(3)
			else:
				time.sleep(3)
		else:
			raise Exception

	def pager(self):
		f = os.path.join(self.user.dpages, self.string_time)
		data = get_html_feed(self.user.name).encode('utf8')
		with open(f, 'w') as nctn:
			nctn.write(data)
		self.user.ppd = self.start_time

	def dead(self):
		return self.user.state == '404'

	def bleak_plus(self):
		return self.user.state in {'empty', 'new', 'normal'}

	def happ(self):
		return self.user.state == 'normal'

	def heart(self):
		return bool(self.user.info.get('<3', 0))

	def examine_blog(self):
		try:
			info = get_user(self.user.tid)
		except requests.exceptions.HTTPError as e:
			if e.response.status_code == 404:
				if not self.dead():
					self.user.state = '404'
					user_report(self.user.id, 'IS DELETED!!')
			else:
				raise
		else:
			self.user.name = info['screen_name']
			if info['protected']:
				if self.user.state != 'protected':
					self.user.state = 'protected'
					user_report(self.user.id, 'IS PROTECTED!!')
			else:
				if self.user.state == 'protected':
					user_report(self.user.id, 'NO LONGER PROTECTED')
				self.exam_success = True
				self.user.state = 'normal'
			self.handle_blog(info)

	def handle_blog(self, info):
		with open(self.user.fuser, 'r') as nctn:
			record = json.load(nctn)
		info = parse_info(info)
		new_info, changes = compare_object(info, record['record'])
		if changes:
			record['record'] = new_info
			record['changes'][self.string_time] = changes
			output.info('%s: Updated info', self.user.name)
		with open(self.user.fuser, 'w') as nctn:
			nctn.write(json.dumps(record))

	def favorites_worker(self, pid=0, page_index=0, init=0):
		def post_is_new(post):
			return post['id'] not in self.fav_ids
		def present(posts):
			return not set([post['id'] for post in posts[-10:]]) <= self.fav_ids
		threshold = 3
		try:
			posts = get_favorites(self.user.tid, pid)
		except:
			errors.exception(self.user.name)
			self.fav_failed = True
			return False
		if posts:
			low = posts[-1]['id']
			suspect = present(posts)
		else:
			return False
		posts = [post for post in posts if post_is_new(post)]
		if posts:
			if suspect or len(posts) >= threshold:
				self.safely_start_page(target=self.favorites_worker, args=(low, page_index+1))
			posts = [handle_post(post) for post in posts]
			self.new_fav_ids = self.new_fav_ids | set([post['id'] for post in posts])
			self.new_fav_count += len(posts)
			self.fav_pages[page_index] = create_temp(self.user.dusr, 'favtemp', posts, page_index)
			return True
		return False

	def handle_favorites(self):
		"""Is persecuted the same as handle_posts.
		
			What are we trying to do with these?
				1. Sync the ID list
				2. Print the favorites (posts) to the fav-feed. That's all
		"""
		self.fav_threads = []
		self.fav_pages = {}
		self.new_fav_count = 0
		self.fav_failed = False
		self.new_fav_ids = set()
		with open(self.user.ffavids, 'r') as f:
			self.fav_ids = set([int(i) for i in f.read().split()])
		r = self.favorites_worker()
		if r:
			for thread in self.fav_threads:
				thread.join()
			if self.fav_failed: return False
			write_pages(self.user.ffav, self.fav_pages)
			delete_temp_files(self.fav_pages)
			output.info('%s favorited: %d', self.user.name, self.new_fav_count)
			with open(self.user.ffavids, 'w') as f:
				f.writelines([str(i)+'\n' for i in list(self.fav_ids | self.new_fav_ids)])
		else:
			return False

	def sync_follow(self, func, msgs):
		"""About: collect follow IDs. Find appreciated and deprecated IDs. Download these active members. """
		ymsg, nmsg = msgs
		actual_follow_ids = set()
		users = []
		next_cursor = -1
		while next_cursor != 0:
			r = func(self.user.tid, cursor=next_cursor)
			next_cursor = r['next_cursor']
			actual_follow_ids = actual_follow_ids | set(r['ids'])
		appreciated = actual_follow_ids - self.follow_ids
		deprecated = self.follow_ids - actual_follow_ids
		for bulk in chunkify([str(i) for i in list(appreciated|deprecated)], 100):
			try:
				users += get_bulk_users(','.join(bulk))
			except requests.exceptions.HTTPError as e:
				if e.response.status_code != 404:
					raise
				else:
					with open(self.user.ffollows, 'a') as f:
						f.write('\n%s: deleted\n'%bulk[0])
		with open(self.user.ffollows, 'a') as f:
			for user in users:
				msg = ymsg if user['id'] in appreciated else nmsg
				f.write(msg+'\n'+json.dumps(hand_follow_man(user), indent=1, sort_keys=True))
			for id_ in list( deprecated - {user['id']for user in users}):
				f.write('\n%d: deleted\n'%id_)
		self.follow_ids = actual_follow_ids
		return True

	def handle_follows(self):
		"""
			What are we trying to do with these?
				1. Sync the ID list
				2. Print the follow info to the follow-feed
		"""
		# Do followers
		with open(self.user.ffollowerids, 'r') as f:
			self.follow_ids = set([int(i) for i in f.read().split()])
		self.sync_follow(get_followers_ids, ('Followed by ', 'Unfollowed by '))
		with open(self.user.ffollowerids, 'w') as f:
			f.writelines([str(i)+'\n' for i in list(self.follow_ids)])
		# Do friends
		with open(self.user.ffriendids, 'r') as f:
			self.follow_ids = set([int(i) for i in f.read().split()])
		self.sync_follow(get_friends_ids, ('Followed ', 'Unfollowed '))
		with open(self.user.ffriendids, 'w') as f:
			f.writelines([str(i)+'\n' for i in list(self.follow_ids)])

	def posts_worker(self, calling_pid, page_index=0, init=0):
		"""
			twitter
			The date is in Greenwich Mean Time, PST+8.
		"""
		def post_is_new(post):
			return post['id'] > self.reference_pid
		try:
			posts = get_posts(self.user.tid, calling_pid, init)
		except:
			errors.exception(self.user.name)
			self.failed = True
			return False
		if not posts: return False
		posts = [post for post in posts if post_is_new(post)]
		lowest_pid = posts[-1]['id']
		if posts:
			if len(posts) >= 200:
				t = self.safely_start_page(target=self.posts_worker, args=(lowest_pid, page_index+1))
				self.post_threads.append(t)
			if not page_index:
				self.marker_pid = posts[0]['id']
			posts = [handle_post(post) for post in posts]
			self.new_post_count += len(posts)
			self.post_pages[page_index] = create_temp(self.user.dusr, 'temp', posts, page_index)
			return True
		return False

	def handle_posts(self):
		self.reference_pid = self.user.reference_pid
		self.marker_pid = 0
		self.new_post_count = 0
		self.post_pages = {}
		self.post_threads = []
		r = self.posts_worker(self.reference_pid, init=1)
		if not r: return False
		for thread in self.post_threads:
			thread.join()
		if self.failed: return False
		write_pages(self.user.ffeed, self.post_pages)
		delete_temp_files(self.post_pages)
		output.info('%s: %d', self.user.name, self.new_post_count)
		self.user.reference_pid = self.marker_pid
		return True

	def run(self):
		"""Defining himself the operations assigned to the varying user state."""
		# What operations we do for varying user states.
		try:
			if self.dead() and not svc.raise_hell:
				return False
			self.examine_blog()
			if self.exam_success:
				if (self.start_time - self.user.ppd).days >= 4:
					self.pager()
				self.handle_posts()
				if self.heart() and svc.look_infoz:
					self.handle_follows()
					self.handle_favorites()
			self.close_settings()
		except requests.exceptions.ConnectionError as e:
			return False # No internet
		# except requests.exceptions.HTTPError as e:
		# 	errors
		except Exception:
			errors.exception(self.user.name)
			settings['users'][self.user.id]['fail_count'] += 1





#
#
# Worker
#
#






























def user_report(user_id, msg):
	msg = '%s %s' % (settings['users'][user_id]['name'], msg)
	try:
		settings['users'][user_id]['<3']
		errors.critical(msg)
	except:
		errors.error(msg)







































#
#
# Posts
#
#

def hand_follow_man(user):
	"""About: parse follow users"""
	desire = {'name','location','created_at','favourites_count','id','followers_count','protected','description','time_zone','statuses_count','friends_count','screen_name'}
	return {k:v for k,v in user.items() if k in desire}

def parse_info(info):
	foul = {'blocked_by','blocking','follow_request_sent','following','lang','profile_background_image_url_https','profile_image_url_https','status', 'has_extended_profile', 'id', 'utc_offset', 'is_translator'}
	return {k:v for k,v in info.items() if k not in foul}

def find_source(source):
	if 'iPhone' in source:
		return 'iPhone'
	if 'Web Client' in source:
		return 'Browser'
	if 'TweetDeck' in source:
		return 'TweetDeck'
	return None

def parse_entities(post):
	try:
		post['entities']
	except:
		return post
	for url in post['entities']['urls']:
		post['text'] = post['text'].replace(url['url'], url['expanded_url'])
	mens = post['entities']['user_mentions']
	post['mens'] = [{'id':men['id'],'screen_name':men['screen_name']} for men in mens] # He May be short Lived
	try:
		mems = post['extended_entities']['media']
		post['mems'] = [mem['media_url_https'] for mem in mems]
	except:
		pass
	return post

def rm(post):
	"""Remove null,false keys from post object."""
	return {k:v for k,v in post.items() if v}

def rma(post, bus):
	extras = ['contributors','coordinates','place','possibly_sensitive','source']
	unwanted_attributes = ['favorited','geo','id_str','in_reply_to_status_id_str','in_reply_to_user_id_str','lang','retweeted','truncated','user','extended_entities','quoted_status_id','quoted_status_id_str', 'is_quote_status', 'entities']
	for attribute_name in unwanted_attributes:
		try: del post[attribute_name]
		except: continue
	if bus:
		for at in extras:
			try: del post[at]
			except: continue
	return post

def handle_post(post, bus=0):
	# Get rid of nulls
	post = parse_entities(post)
	try:
		post['retweeted_status'] = handle_post(post['retweeted_status'], bus=1)
	except:
		pass
	try:
		post['quoted_status'] = handle_post(post['quoted_status'], bus=1)
	except:
		pass
	post = rma(post, bus)
	post = rm(post)
	try:
		post['source'] = find_source(post['source'])
	except:
		pass
	return post




#
#
# Posts
#
#








































#
#
# Network
#
#

"""
API notes:
'since_id' exclusive
'max_id' inclusive

default_cursor = '-1'
previous_cursor, next_cursor, previous_cursor_str and next_cursor_str
if next_cursor_str == '0':
	#done
"""

def find_tid(name):
	u = get_user(sn=name)
	return u['id']
	
def get_bulk_users(tids, count=100):
	"""If none of your lookup criteria can be satisfied by returning a user object, a HTTP 404 will be thrown.
	Rate limit is 180/15minutes"""
	url = 'users/lookup.json'
	params = {'include_entities':'false', 'user_id':tids}
	r = s.post(url=url, data=params)
	r.raise_for_status()
	return r.json()

def get_user(tid=0, sn=''):
	url = 'users/show.json'
	params = {}
	if tid:
		params['user_id'] = str(tid)
	else:
		params['screen_name'] = sn
	r = s.get(url=url, params=params)
	r.raise_for_status()
	return r.json()

def get_favorites(tid, pid=0, init=0, count=200):
	url = 'favorites/list.json'
	params = {'count':str(count), 'user_id':tid}
	if pid:
		if init:
			params['since_id'] = pid
		else:
			params['max_id'] = str(pid-1)
	r = s.get(url=url, params=params)
	r.raise_for_status()
	return r.json()

def get_followers(tid, cursor=-1, count=200):
	# Ordered by newest.
	url = 'followers/list.json'
	params = {'count':str(count), 'user_id':tid, 'cursor':str(cursor)}
	r = s.get(url=url, params=params)
	r.raise_for_status()
	return r.json()

def get_followers_ids(tid, cursor=-1, count=5000):
	""":return:dict :key:ids:type:list:value:int"""
	# Maybe use this to see if anything been removed. Download the complete list and look through it
	url = 'followers/ids.json'
	params = {'count':str(count), 'user_id':tid, 'cursor':str(cursor)}
	r = s.get(url=url, params=params)
	r.raise_for_status()
	return r.json()

def get_friends(tid, cursor=-1, count=200):
	# Ordered by newest.
	url = 'friends/list.json'
	params = {'count':str(count), 'user_id':tid, 'cursor':str(cursor)}
	r = s.get(url=url, params=params)
	r.raise_for_status()
	return r.json()

def get_friends_ids(tid, cursor=-1, count=5000):
	url = 'friends/ids.json'
	params = {'count':str(count), 'user_id':tid, 'cursor':str(cursor)}
	r = s.get(url=url, params=params)
	r.raise_for_status()
	return r.json()

def get_posts(tid, pid=0, init=0, count=200):
	url = 'statuses/user_timeline.json'
	params = {'count':count, 'user_id':tid, 'trim_user':'true', 'contributor_details':'true'}
	if pid:
		if init:
			params['since_id'] = pid
		else:
			params['max_id'] = pid-1
	r = s.get(url=url, params=params)
	r.raise_for_status()
	return r.json()

def get_html_feed(user_name):
	url = 'https://twitter.com/'+user_name
	r = requests.get(url=url)
	r.raise_for_status()
	return r.text

#
#
# Network
#
#
