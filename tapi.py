service = 'tumblr'

import socket, shutil, re, os, time, datetime, json, Queue, logging, threading, requests
from bs4 import BeautifulSoup as bsoup # This needs to be installed.


"""
Tumblr API client
Was previously tarch
"""

# How messed up is it that we don't have user identification. From the ID verification to the operation, the user could have changed. Wish we had simple primary keys to go by.



# directory
"""
/t
	/root_name
		user
		feed
		likes
		/notes
		/pages
		/changed name
			...?
		# /dumps
"""

# user storage














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
def make_host_name(name):
	return name+'.tumblr.com'
def test_net():
	try: return bool(socket.create_connection((socket.gethostbyname('www.google.com'), 80), 2))
	except: return False
def increment_filename(fn):
	if not os.path.exists(fn):
		return fn
	i = 1
	while os.path.exists( '%s_(%d)'% (fn, i)):
		i += 1
	return '%s_%d' % (fn, i)
def date_increment_filename(fn):
	date = time.strftime("%Y-%m-%d")
	new_fn = increment_filename( '%s_%s'%(fn, date) )
	os.rename(fn, new_fn)
	return open(fn, 'ab')
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
			for i in range(1, len(keys)+1):
				if not isinstance(getFromDict(obj, keys[:i]), dict):
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














































































# All looks good!

def _load_account():
	""" { 'id':0, 'name':'', 'host_name':'', 'cookie':'', 'tumkey':'', 'access':'', 'access_secret':'' } """
	global cookie
	global tumkey
	acc = settings['accounts'][0]
	cookie = acc['cookie']
	tumkey = acc['tumkey']
	return acc

def _load_api(acc):
	global host_name
	global api_key
	global s # session
	host_name = acc['host_name']
	api_key = acc['api_key']
	s = create_oauth(acc['access'], acc['access_secret'])

def create_user(name):
	with top.lock:
		settings['users'].append({ 'id': len(settings['users']), 'active': True, 'root_name': name, 'name': name, 'host_name': name+'.tumblr.com', 'private': False, 'recovery': { 'pid': '', 'host': '' }, 'tumblelog_key': '', 'tumblelog_id': '', 'last_pid': 0, 'last_updated': 0, 'state': 'new', 'ppd': '1990-04-12 17:07:11', 'fail_count': 0, 'subdir': '', 'last_liked': 0, 'new_user': True })

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
		"""todo_list: is an optional list of usernames"""
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
		self.dsvc = os.path.join(top.d_root, 't')
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
		# Might want to implement another error check for % of failed threads.

	def new_user(self, name):
		# Not implementing any automatic creation here for now
		errors.warning('%s: this name is still active', name)

	def run(self, todo_list):
		if not test_net():
			return False
		if todo_list:
			todo_list = [test_input_name(name) for name in todo_list]
		else:
			todo_list = [user['id'] for user in settings['users']] # append `if user['active']` for only active users
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

	def __init__(self, user_id):
		self.id = user_id
		self._load_info()
		self._load_files()

	def force_new(self, name):
		svc.create_user(name)

	def new_user(self):
		if self.info.get('new_user', False):
			del self.info['new_user']
			if os.path.exists(self.dusr):
				self.dusr = increment_filename(self.dusr)
				settings['users'][self.id]['root_name'] = os.path.basename(self.dusr)
				self.info['root_name'] = os.path.basename(self.dusr)

	def _load_info(self):
		"""Load the user's stats from the settings object. Copy it and update it afterward. last pid grabbed, tumblelog key, previous paged date"""
		info = settings['users'][self.id].copy()
		# self.uid = info['uid'] # User Identification Number
		self.name = info['name']
		self.host_name = info['host_name']
		self.archive = 'http://%s/archive'%info['host_name']
		self.state = info['state']
		# self.tk = info['tumblelog_key']
		self.reference_pid = int(info['last_pid'])
		self.ppd = datetime.datetime.strptime(info['ppd'], '%Y-%m-%d %H:%M:%S')
		self.share_likes = info.get('likes', False)
		self.info = info

	def _load_files(self):
		self.dusr = os.path.join(svc.dsvc, self.info['root_name'])
		self.new_user()
		if self.info['subdir']:
			self.dusr = os.path.join(self.dusr, self.info['subdir'])
		self.ddump = os.path.join(self.dusr, 'dumps')
		self.dnotes = os.path.join(self.dusr, 'notes')
		self.dpages = os.path.join(self.dusr, 'pages')
		self.fuser = os.path.join(self.dusr, 'user')
		self.ffeed = os.path.join(self.dusr, 'feed')
		self.flikes = os.path.join(self.dusr, 'likes')
		dmake(self.dusr)
		dmake(self.ddump)
		dmake(self.dnotes)
		dmake(self.dpages)
		if not os.path.exists(self.fuser):
			with open(self.fuser, 'w') as nctn:
				nctn.write("""{"info": {"record": {}}, "theme": {"record": {}}}""")
		fmake(self.ffeed)
		fmake(self.flikes)

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
	"""Docstring"""
	def __init__(self, user_id):
		threading.Thread.__init__(self)
		self.user = User(user_id)
		self.heavy = not bool(self.user.info['last_pid'])
		self.string_time = time.strftime("%Y-%m-%d %H:%M:%S")
		self.start_time = datetime.datetime.strptime(self.string_time, '%Y-%m-%d %H:%M:%S')
		self.failed = False
		self.state = self.user.state
		self.exam_success = False

	def close_settings(self):
		if self.failed:
			self.user.info['fail_count'] += 1
			if self.user.info['fail_count'] > 5:
				svc.bork = True
		else:
			self.user.info['fail_count'] = 0 

		if self.user.info['state'] == '404':
			if self.state != '404':
				user_report(self.user.id, 'No longer 404')
		elif self.state == '404':
			user_report(self.user.id, 'IS DELETED!!')

		if self.user.info['state'] == 'empty':
			if self.state != 'empty':
				user_report(self.user.id, 'No longer empty')
		elif self.state == 'empty':
			user_report(self.user.id, 'IS EMPTY!!')

		self.user.info['state'] = self.state
		# self.user.info['tk'] = self.tk # We might need this for notes pages, but get_post API does give notes info so maybe collect whatever from there. But API posts expire upon deletion despite the data still being in the db and can still be accessed somehow like pre-patch. API doesn't give TK
		self.user.info['likes'] = self.user.share_likes
		self.user.info['last_pid'] = self.user.reference_pid
		self.user.info['ppd'] = str(self.user.ppd)
		settings['users'][self.user.id] = self.user.info
		top.write_lists()

	def safely_start_page(self, target, args):
		for _ in xrange(300):
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
		data = get_archive(self.user.host_name).encode('utf8')
		with open(f, 'w') as nctn:
			nctn.write(data)
		self.user.ppd = self.start_time

	def recover(self, result_name):
		"""docstring"""
		if result_name not in self.user.info['root_name']:
			self.user.info['subdir'] = result_name
		self.user.info['name'] = result_name
		self.user.info['host_name'] = self.user.info['host_name'].replace(self.user.name, result_name)
		user_report(self.user.id, 'changed URL to %s'%result_name)
		svc.recovery.append(self.user.id)

	def check_pulse(self):
		if not self.hope():
			try:
				self.create_hard_link()
			except:
				return False
		result_name = get_hard_link(self.user.info)
		main, new = living(self.user.host_name, result_name+'.tumblr.com')
		if main:
			if result_name == self.user.name:
				self.state = 'normal'
			else:
				svc.new_user(self.user.name)
		elif new:
			self.state = 'normal'
			self.recover(result_name)
		else:
			return False

	def dead(self):
		return self.state in ['404', 'empty']
	def hope(self):
		return bool(self.user.info['recovery']['pid'])
	# def bleak_plus(self):
	# 	return self.state in ['new', 'normal', 'empty']
	def happ(self):
		return self.state in ['new', 'normal']
	def healthy(self):
		return self.state == 'normal'
	def heart(self):
		return bool(self.user.info.get('<3', 0))

	def create_hard_link(self):
		"""A very important method. First contact with the blog."""
		posts = get_posts(self.user.host_name, limit=1)
		post = posts[0]
		pid, rk, post_type = str(post['id']), post['reblog_key'], post['type']
		draft_pid = create_draft(pid, rk, post_type)
		if draft_pid:
			self.user.info['recovery'] = {'host': settings['accounts'][0]['id'], 'pid': draft_pid}
			return True
		return False

	def manage_hard_link(self):
		result_name = get_hard_link(self.user.info)
		if result_name == self.user.name:
			return True
		else:
			if not result_name:
				self.state = '404'
			elif '-deactivated' in result_name:
				if living(result_name+'.tumblr.com'):
					self.recover(result_name)
				else:
					self.state = '404'
			elif result_name != self.user.name:
				self.recover(result_name)
			if living(self.user.host_name):
				svc.new_user(self.user.name)
			return False

	def check_user_identity(self):
		"""get_posts will raise an HTTPError and chl will raise indexerror if it gets an empty list of posts"""
		if not self.user.info['recovery']['pid']:
			try:
				self.create_hard_link()
			except requests.exceptions.HTTPError as e:
				if e.response.status_code != 404:
					raise
				self.state = '404'
			except IndexError:
				self.state = 'empty'
		if self.user.info['recovery']['pid']:
			r = self.manage_hard_link()
			if r:
				self.state = 'normal'
				return True
		return False

	def examine_blog(self):
		"""The only way to test user validity is to look at a draft post meta data."""
		r = self.check_user_identity()
		self.exam_success = bool(r)

	def posts_worker(self, calling_pid=0, page_index=0):
		"""
		since_id parameter for initial request. and max_id parameter for subsequent reqeuests. the undocumented limit cap may be 1000.
		post_id is post to get. 20 is the limit cap. offset is 
		The date is in Greenwich Mean Time, PST+8. The tooltip time is in OP's time zone.
		Data we want for feed:
			date, via, source?, note count, tags, html, reblog url, 
		"""
		def post_is_new(post):
			return post['id'] > self.reference_pid
		if self.failed:
			return False
		try:
			posts = get_posts(self.user.host_name, calling_pid)
		except:
			errors.exception(self.user.name)
			self.failed = True
			return False
		if not posts: return False
		lowest_pid = posts[-1]['id']
		posts = [post for post in posts if post_is_new(post)]
		if posts:
			# handle_dumps(json.dumps(posts))
			if lowest_pid > self.reference_pid:
				t = self.safely_start_page(target=self.posts_worker, args=(posts[-1]['id'], page_index+1))
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
		r = self.posts_worker()
		if not r:
			return False
		for thread in self.post_threads:
			thread.join()
		if self.failed:
			return False
		write_pages(self.user.ffeed, self.post_pages)
		delete_temp_files(self.post_pages)
		output.info('%s: %d', self.user.name, self.new_post_count)
		self.user.reference_pid = self.marker_pid

	def likes_worker(self, calling_timestamp, page_index=0, init=0):
		def post_is_new(post):
			return post['liked_timestamp'] > self.reference_like
		try:
			likes = get_likes(self.user.host_name, calling_timestamp, init)
		except:
			errors.exception(self.user.name)
			self.likes_pages[page_index] = create_temp(self.user.dusr, 'likestemp', ['FAILED', calling_timestamp, page_index], page_index)
			self.failed = True
			return False
		if not likes: return False
		lowest_timestamp = likes[-1]['liked_timestamp']
		likes = [post for post in likes if post_is_new(post)]
		if likes:
			if lowest_timestamp > self.reference_like:
				t = self.safely_start_page(target=self.likes_worker, args=(likes[-1]['timestamp'], page_index+1))
				self.likes_threads.append(t)
			if not page_index:
				self.marker_like = likes[0]['liked_timestamp']
			likes = [handle_post(post) for post in likes]
			self.new_likes_count += len(likes)
			self.likes_pages[page_index] = create_temp(self.user.dusr, 'likestemp', likes, page_index)
			return True
		return False
	def handle_likes(self):
		self.reference_like = self.user.info['last_liked']
		self.marker_like = 0
		self.new_likes_count = 0
		self.likes_pages = {}
		self.likes_threads = []
		r = self.likes_worker(self.reference_like, init=1)
		if not r:
			return False
		for thread in self.likes_threads:
			thread.join()
		write_pages(self.user.flikes, self.likes_pages)
		delete_temp_files(self.likes_pages)
		output.info('%s: %d new likes', self.user.name, self.new_likes_count)
		if not self.failed:
			self.user.info['last_liked'] = self.marker_like

	def handle_blog(self):
		self.user.share_likes = handle_blog(self.user.fuser, self.user.name, self.user.host_name, self.string_time)

	def run(self):
		# What operations we do for varying user states.
		try:
			if self.dead() and svc.raise_hell:
				self.check_pulse()
			if self.happ():
				self.examine_blog()
			if self.exam_success:
				if not self.user.info['private'] and (self.start_time - self.user.ppd).days >= 3:
					self.pager()
				try: # This try block is bad. causes problems. Should remove it.
					if svc.look_infoz:
						self.handle_blog()
					self.handle_posts()
				except Exception:
					self.failed = True
					errors.exception(self.user.name)
				if self.heart() and self.user.share_likes:
					self.handle_likes()
			self.close_settings()
		except requests.exceptions.ConnectionError as e:
			return False # No internet
		except Exception:
			errors.exception(self.user.name)
			settings['users'][self.user.id]['fail_count'] += 1






#
#
# Worker
#
#























































#
#
# Util
#
#


def create_temp(dusr, fn, posts, page_index):
	temp_name = os.path.join(dusr, '%s%d'%(fn, page_index))
	with open(temp_name, 'w') as nctn:
		nctn.write(json.dumps(list(reversed(posts)), indent=1, sort_keys=True).decode('unicode-escape').encode('utf8'))
	return temp_name

def correct_man(user_info):
	aidfu = user_info['recovery']['host']
	if aidfu != settings['accounts'][0]['id']:
		racc = settings['accounts'][aidfu]
		rs = create_oauth(access_token=racc['access_token'], access_token_secret=racc['access_token_secret'])
		return (racc['host_name'], rs)
	else:
		return (host_name, s)

def get_hard_link(user_info):
	pid = user_info['recovery']['pid']
	used_host, used_s = correct_man(user_info)
	r = get_draft(host=used_host, pid=pid, auth=used_s)
	result_name = r['reblogged_from_name']
	return result_name

def user_report(user_id, msg):
	msg = '%s %s' % (settings['users'][user_id]['name'], msg)
	try:
		settings['users'][user_id]['<3']
		errors.critical(msg)
	except:
		errors.error(msg)

def living(*host_names):
	"""n arguments in, n booleans out.
	Important. Raises requests.exceptions.HTTPError if unexpected HTTP status."""
	results = []
	for _host_name in host_names:
		try:
			get_posts(_host_name, limit=1)
		except requests.exceptions.HTTPError as e:
			if e.response.status_code != 404:
				raise
			results.append(False)
		else:
			results.append(True)
	if len(results) == 1:
		return results[0]
	return results











#
#
# Util
#
#


































#
#
# Blog
#
#


def parse_info(info):
	# desired = {'ask','ask_anon','ask_page_title','description','is_nsfw','name','title','likes'}
	unwanted = {'can_send_fan_mail','can_subscribe','followed','is_blocked_from_primary','posts','subscribed','updated','url'}
	return {k:v for k,v in info.items() if k not in unwanted}
def parse_indash(indash):
	unwanted = {'premium_partner','likes','uuid','asks','title','dashboard_url','avatar_url','description','is_group','anonymous_asks','cname','description_sanitized','name','url','customizable','can_send_messages','following','global_theme_params'}
	return {k:v for k,v in indash.items() if k not in unwanted}

def handle_blog(fuser, name, user_host_name, stime):
	with open(fuser, 'r') as nctn:
		record = json.load(nctn)
	info = get_blog_info(user_host_name)
	indash = get_indash_info(name)
	# self.last_updated = info['updated'] # Can't use these bc not classM
	# self.user.private = indash['is_private']
	share_likes = info['share_likes']
	info = parse_info(info)
	theme = indash['global_theme_params']
	indash = parse_indash(indash)
	info.update(indash)
	new_info, changes = compare_object(info, record['info']['record'])
	if changes:
		record['info']['record'] = new_info
		record['info'][stime] = changes
		output.info('%s: Updated info', name)
	new_theme, changes = compare_object(theme, record['theme']['record'])
	if changes:
		record['theme']['record'] = new_theme
		record['theme'][stime] = changes
		output.info('%s: Updated theme', name)
	with open(fuser, 'w') as nctn:
		nctn.write(json.dumps(record))
	return share_likes



#
#
# Blog
#
#































#
#
# Posts
#
#


def handle_readmore(text_body, text_body_attrs):
	body_html = bsoup(text_body)
	readmores = body_html.findAll('a', class_='read_more')	
	try:
		for flag in readmores:
			user_host_name, pid = re.search(r'\://([^/]+)/post/(\d+)', flag['href']).groups()
			print user_host_name, pid
			try:
				post = get_post(user_host_name, pid)
			except:
				continue
			replacement = bsoup( post[text_body_attrs[post['type']]] )
			replacement.find('html').unwrap()
			replacement.find('body').unwrap()
			flag.replace_with(replacement)
		return str(body_html)
	except:
		errors.exception('Readmore fail:\n%s', text_body)
		return text_body

def handle_post(post):
	"""Note: because we have so many unwanted I think it's faster to iterate the post."""
	text_body_attrs = {'answer': 'answer', 'photo': 'caption', 'chat': 'body', 'text': 'body', 'video': 'caption', 'audio': 'caption', 'link': 'description', 'quote': 'source'}
	unwanted = {'blog_name', 'can_reply', 'followed', 'liked', 'format', 'timestamp', 'id', 'highlighted', 'recommended_color', 'recommended_source', 'short_url', 'slug', 'summary', 'state', 'reblogged_from_id', 'reblogged_from_name', 'reblogged_from_title', 'reblogged_root_id', 'reblogged_root_name', 'reblogged_root_title', 'reblog', 'trail', 'can_send_in_message', 'thumbnail_height','thumbnail_url','thumbnail_width','video_type','player','reblogged_from_can_message','reblogged_from_following','reblogged_from_uuid','reblogged_root_can_message','reblogged_root_following','reblogged_root_uuid','source_title', 'embed', 'is_external', 'image_permalink', 'html5_capable', 'body_abstract'}
	#dialogue (probably extraneous)
	post = {k:v for k,v in post.items() if k not in unwanted}
	post[text_body_attrs[post['type']]] = handle_readmore(post[text_body_attrs[post['type']]], text_body_attrs)
	if post.get('photos', None):
		post['photos'] = [photo['original_size']['url'] for photo in post['photos']]
	return post




#
#
# Posts
#
#






































#
#
# Networking
#
#




def get_archive(user_host_name):
	url = 'http://'+user_host_name+'/archive'
	headers = get_headers({'Host': user_host_name})
	r = requests.get(url=url, headers=headers)
	r.raise_for_status()
	return r.text

def get_indash_info(name):
	url = 'https://www.tumblr.com/svc/indash_blog/posts'
	params = {'tumblelog_name_or_id':name, 'limit':1, 'offset':0}
	headers = get_headers()
	r = requests.get(url, params=params, headers=headers)
	r.raise_for_status()
	return r.json()['response']['tumblelog']

def get_blog_info(user_host_name):
	url = 'blog/%s/info'%user_host_name
	params = {'api_key':api_key}
	r = s.get(url=url, params=params)
	r.raise_for_status()
	return r.json()['response']['blog']

def get_draft(host, pid, auth=None):
	url = 'blog/%s/posts/draft'%host
	params = {'before_id':pid+1, 'limit':'1', 'reblog_info':'true'}
	if auth:
		_func = auth.get
	else:
		_func = s.get
	r = _func(url=url, params=params)
	r.raise_for_status()
	return r.json()['response']['posts'][0]

def get_likes(user_host_name, timestamp, init=0, limit=100):
	url = 'blog/%s/likes'%user_host_name
	params = {'api_key':api_key, 'limit':limit}
	if init:
		params['after'] = timestamp
	else:
		params['before'] = timestamp
	r = s.get(url=url, params=params)
	r.raise_for_status()
	return r.json()['response']['liked_posts']

def get_post(user_host_name, pid, notes_flag='false'):
	url = "blog/%s/posts" % user_host_name
	params = {'api_key':api_key, 'id':pid, 'reblog_info':'true', 'notes_info':notes_flag}
	r = s.get(url=url, params=params)
	r.raise_for_status()
	return r.json()['response']['posts'][0]

def get_posts(user_host_name, pid=0, limit=100, notes_flag='false'):
	url = "blog/%s/posts" % user_host_name
	params = {'api_key':api_key, 'limit':limit, 'reblog_info':'true', 'notes_info':notes_flag}
	if pid:
		params['before_id'] = pid
	r = s.get(url=url, params=params)
	r.raise_for_status()
	return r.json()['response']['posts']

def create_draft(pid, rk, post_type):
	url = 'blog/%s/post/reblog' % host_name
	params = {'type':post_type, 'state':'draft', 'id':pid, 'reblog_key':rk}
	r = s.post(url=url, data=params)
	r.raise_for_status()
	return r.json()['response']['id']



#
#
# API network
#
#


















































#
#
# Networking
#
#

user_agent = ''


def create_oauth(access_token, access_token_secret):
	"""Usage: session.get(url), session.post(url, body=None, json=None, **kwargs)"""
	from rauth import OAuth1Service
	tumblr = OAuth1Service(
		name='tumblr',
		consumer_key='',
		consumer_secret='',
		request_token_url='https://www.tumblr.com/oauth/request_token',
		access_token_url='https://www.tumblr.com/oauth/access_token',
		authorize_url='https://www.tumblr.com/oauth/authorize',
		base_url='https://api.tumblr.com/v2/')
	session = tumblr.get_session((access_token, access_token_secret))
	return session

"""Get it's info from Service. Or svc can just set globals"""
def get_headers(*arg):
	headers = {
		'Host' : 'www.tumblr.com', 
		'User-Agent' : user_agent, 
		'Accept' : 'application/json, text/javascript, */*; q=0.01', 
		'Accept-Language' : 'en-US,en;q=0.5', 
		'Accept-Encoding' :  'identity',
		'x-tumblr-form-key' : tumkey,
		'X-Requested-With' : 'XMLHttpRequest', 
		'Referer' : 'https://www.tumblr.com/dashboard',
		'Cookie' : cookie, 
		'DNT' : '1', 
		'Connection' : 'keep-alive', 
		'Pragma' : 'no-cache', 
		'Cache-Control' : 'no-cache'
	}
	if arg:
		kwargs = arg[0]
		for key in kwargs:
			headers[key] = kwargs[key]
		for key in headers:
			if not headers[key]:
				del headers[key]
	return headers





def login():
	"""About: All that's required is a username and a password."""
	pass

# def authenticate():
# 	"""The target account must be on the stack so include the -na {account name/id} argument. Cookie/key required."""
# 	"""This function needs work. Add in feature to automatically go to the URL with the appropriate cookie/key and get the verifier."""
# 	"""This function must be called from the terminal. To authenticate a new account with the API. Follow steps, access keys will be added to storage."""
# 	from rauth import OAuth1Service
# 	tumblr = OAuth1Service(
# 		name='tumblr',
# 		consumer_key='',
# 		consumer_secret='',
# 		request_token_url='https://www.tumblr.com/oauth/request_token',
# 		access_token_url='https://www.tumblr.com/oauth/access_token',
# 		authorize_url='https://www.tumblr.com/oauth/authorize',
# 		base_url='https://api.tumblr.com/v2/')
# 	request_token, request_token_secret = tumblr.get_request_token()
# 	errors.info('request_token: %s, request_token_secret: %s', request_token, request_token_secret)
# 	authorize_url = tumblr.get_authorize_url(request_token)
# 	verifier = raw_input('Visit this URL in your browser: ' + authorize_url)
# 	session = tumblr.get_auth_session(request_token, request_token_secret, method='POST', data={'oauth_verifier': verifier})
# 	errors.info('access_token: %s, access_token_secret: %s', session.access_token, session.access_token_secret)
# 	settings
