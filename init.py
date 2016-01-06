# #/usr/bin/ python

"""
Don't import this.
It's an interface for the modules.
"""

import os, json, time, argparse, logging, signal, threading, socket, multiprocessing, shutil, errno
import logging.handlers
import tapi as tumblr
import twap as twitter
aleph = {'tumblr': tumblr, 'twitter': twitter}

def f_d_copy(src, dst):
	"""
	Copy files or directories
	"""
	try:
		shutil.copytree(src, dst)
	except OSError as exc:
		if exc.errno == errno.ENOTDIR:
			shutil.copy(src, dst)
		else: raise

class BigStuff(object):

	def __init__(self):
		self.huplock = threading.Lock()
		self.lock = threading.Lock() # lock needed to modify lists
		signal.signal(signal.SIGHUP, self.huphandler)

		self.directory_creation()
		self.open_lists()
		self.open_preferences()

	def debugging(self):
		if self.module_settings['args']['debug']:
			self.d_root = os.path.join(self.d_root, 'sandbox')
			new_fnsettings = self.f_settings + time.strftime("%Y-%m-%d %H:%M:%S")
			f_d_copy(self.f_settings, new_fnsettings)
			if self.module_settings['args']['nochange']:
				self.f_settings = new_fnsettings

	def directory_creation(self):
		# Instantiating path/file variables
		# self.d_root = os.path.dirname(os.path.realpath(__file__))
		self.d_root = os.path.join(os.path.expanduser('~'),'Documents','records')
		self.f_settings = os.path.join(self.d_root,'settings')
		self.f_stdout = os.path.join(self.d_root,'activity')
		self.f_stderr = os.path.join(self.d_root,'errors')

		# Instantiating paths/files
		if not os.path.exists(self.d_root):
			os.makedirs(self.d_root)
		if not os.path.exists(self.f_settings):
			"""
			A slightly more filled out example, using module preferences:
			default_settings = {"tumblr": {"cookie": "", "key": "", "recovery_list": {"example_user": "/119053342579/52q1ZQn0"}, "404_users": [], "empty_users": [], "code_broken": False, "user_list": {"example_user": {"fail_count": 0, pid": 119053342579, "tk": "52q1ZQn0", "pfd": "1990-04-12 17:07:11", "ppd": "2015-05-25 23:38:35"}}}, "twitter": {"empty_users": [], "404_users": [], "code_broken": False, "recovery_list": {"example_user": "/someuser/status/777178400601555825"}, "user_list": {"example_user": {"pid": 0, "ppd": "1990-04-12 17:07:11"}}}}
			"""
			default_settings = {"tumblr": {"cookie": "", "key": "", "recovery_list": {}, "empty_users": [], "404_users": [], "cookie_invalid": False, "code_broken": False, "user_list": {}}, "twitter": {"empty_users": [], "404_users": [], "code_broken": False, "recovery_list": {}, "user_list": {}}}
			with open(self.f_settings, 'w') as nctn:
				json.dump(default_settings, nctn)

	def run(self):
		self.debugging()
		
		for module in aleph:
			if self.module_settings['args'][module]['switch']:
				self.run_all = False
				break
			self.run_all = True
		while True:
			with self.huplock:
				p = multiprocessing.Process(target=self.run_loop)
				p.start()
				p.join()
			if self.module_settings['args']['wait_time']:
				time.sleep(self.module_settings['args']['wait_time'])
			else:
				return

	def run_loop(self):
		self.open_logging()
		self.open_lists()
		output.info('\n\n\n%s', time.strftime("%Y-%m-%d %H:%M:%S"))
		for module in aleph:
			mod = self.module_settings['args'][module]

			# Swtiches
			if self.run_all or mod['switch']:
				# Prepare the user list
				if mod['users']:
					if not isinstance(mod['users'], list):
						mod['users'] = [mod['users']]
				# else: mod['users'] = self.settings[module]['user_list']

				# Do the work
				try:
					svc = aleph[module].Service(self)
					svc.run(mod['users'])
				except:
					errors.exception('')
					continue
				self.write_lists()



	def open_logging(self):
		"""
		Note: SERVER can be any SMTP server. The TO and FROM headers are arbitrary. TO should be the address you want to receive mail at.
		"""
		logging.handlers.SMTPHandler.emit = emit # If your email needs SSL, do this
		global errors
		global output
		errors = logging.getLogger('errors')
		errors.setLevel(logging.WARNING)
		output = logging.getLogger('output')
		output.setLevel(logging.INFO)
		format = logging.Formatter('\n%(asctime)s\n%(levelname)s: %(funcName)s: %(message)s')

		# Might want to edit the doRollover method of RFH
		out = logging.handlers.RotatingFileHandler(filename=self.f_stdout, maxBytes=307200, backupCount=99)
		err = logging.handlers.RotatingFileHandler(filename=self.f_stderr, maxBytes=102400, backupCount=99)
		USERNAME = ''
		PASSWORD = ''
		SERVER = ('smtp.replaceme.org', 465) # 465:ssl, 587:standard
		FROM = 'me@thing.org'
		TO = ['me@thing.org']
		SUBJECT = 'critical tarch error'
		bad = logging.handlers.SMTPHandler(mailhost=SERVER, fromaddr=FROM, toaddrs=TO, subject=SUBJECT, credentials=(USERNAME, PASSWORD))
		out.setLevel(logging.INFO)
		err.setLevel(logging.WARNING)
		bad.setLevel(logging.CRITICAL)
		err.setFormatter(format)
		bad.setFormatter(format)
		output.addHandler(out)
		errors.addHandler(err)
		errors.addHandler(bad)

	def huphandler(self, signum, frame):
		with self.huplock:
			os._exit(0)

	def open_preferences(self):
		self.module_settings = {'plain': {'tumblr': {}, 'twitter': {}}, 'args': {'tumblr': {}, 'twitter': {}}}
	def close_preferences(self):
		pass
	def write_preferences(self):
		pass
	def open_lists(self):
		with open(self.f_settings, 'r') as nctn:
			self.settings = json.loads(nctn.read())
	def close_lists(self):
		pass
	def write_lists(self):
		with self.lock:
			with open(self.f_settings, 'w') as nctn:
				json.dump(self.settings, nctn)









def emit(self, record):
	"""
	Monkey-patch (overwrite) logging.handlers.SMTPHandler.emit with SMTP_SSL support.
	Necessary if you have a 465 SMTP server.
	Emit a record.
	Format the record and send it to the specified addressees.
	"""
	try:
		import smtplib
		from email.utils import formatdate
		port = self.mailport
		if not port:
			port = smtplib.SMTP_PORT
		smtp = smtplib.SMTP_SSL(self.mailhost, port, timeout=self._timeout)
		msg = self.format(record)
		msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (self.fromaddr, ", ".join(self.toaddrs), self.getSubject(record), formatdate(), msg)
		if self.username:
			smtp.ehlo()
			if self.secure:
				smtp.starttls(*self.secure)
				smtp.ehlo()
			smtp.login(self.username, self.password)
		smtp.sendmail(self.fromaddr, self.toaddrs, msg)
		smtp.quit()
	except (KeyboardInterrupt, SystemExit):
		raise
	except:
		self.handleError(record)






def get_lock(process_name):
	global lock_socket   # Without this our lock gets garbage collected
	lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
	try:
		lock_socket.bind('\0' + process_name)
	except socket.error:
		os._exit(0)
get_lock('FEN') # Will run only one instance




# if __name__ == '__main__':
# You need to add the args and add them to module_settings. You need to add the module to aleph
parser = argparse.ArgumentParser(description="Archiver")
parser.add_argument("-d", "--debug", help="Debugging sandbox", action="store_true")
parser.add_argument("-dn", "--nochange", help="Don't record changes to settings", action="store_true")
parser.add_argument("-t", "--tumblr", help="Run only Tumblr.", action="store_true")
parser.add_argument("-tw", "--twitter", help="Run only Twitter.", action="store_true")
parser.add_argument("--notes", help="Download the notes pages. Default=off.", action="store_true")
parser.add_argument("-b", "--wait", help="Time to wait in seconds.", type=int)
parser.add_argument("-tu", "--tumblrusers", help="Specify Tumblr user(s). String or list of strings.")
parser.add_argument("-wu", "--twitterusers", help="Specify Twitter user(s). String or list of strings.")
args = parser.parse_args()
top = BigStuff()
top.module_settings['args'] = {'tumblr': {'switch': args.tumblr, 'users': args.tumblrusers, 'notes': args.notes}, 'twitter': {'switch': args.twitter, 'users': args.twitterusers}, 'wait_time': args.wait, 'debug': args.debug, 'nochange':args.nochange}
top.run()

















































# notes and shi

"""Problem: doesnt record later modifications to posts."""
"""Solution: we only need to check the first page. so we check the page against the reference page. record changes, then overwrite it. set [-1] anchor. set postid as key in safe dict, on each pass, create test dict and cross reference the id keys with contents"""

"""Problem: large loads take long time to compile output. LOTS of 429. Holds output in memory, 
	1 thread for every page, 400+ threads"""
"""solutions: we have a user thread and page child threads, """

"""Corrected Problems: out of order. ignores 429 HTTP. excepts on empty search. doesnt decode html. separate http connections. urlopen hangs"""

# Note: Anything in ROOT/USER/feed/pages without post-id filename prefix, is from another downloading app

"""5.7.15 log: /archive has data removed. now we open /post for required data, /archive(per group) -> /post -> /fetch (per post)
if 404 in /post, then use domain/post/pid, copy 301 location and request again, if continued error, then sys.exit()
"""
""" For big loads. they get the wait flag set then theyre done linearly from the main func with start flag in queue.
flag set in directory_creating. thread holds til main sends signal to continue.
this should work for many big load threads, theyll wait their turn. 
normal operation sends signal to main to wait for join, heavy operation sends signal to skip

"""

"""NOTES: twitte broke because i try to go to knext page and cant bc id changed to pisition
twitt may be more broke than that, im not getting posts i should, new ones. yep that was bc the id is from original post date not repost date, its kinda messy now, the check goes like this: {('higher id' OR higher on page index) AND Not In 'pre existing list'}. the pre existing list is a huge collection of all archived postid's, generated by REGEX!!!! on runtime everytime. so for every post we're running this huge operation. if were going to do that huge op then thats all we really  n eed to tdo. 

tarh goes slow bc 429 wait in hangprevention, and the load of grabbing /post in front of /fetch
25 /archive and still no /fetch, the /post 429's are probably climbing all over each other
we could try going thro the archive, collecting THAT data with therads. then """

"""Problems 5.21.15: exception when date saved is without microseconds.
						has been poorly corrected with try/except
running tarch with url arg will hang forever bc heavy flag. fixed
"""

"""linux.
add daemon functionality, add login functionality, top.stdoutq to file, correct the filename usage;use the proper os functions
the notes files are too numerous, we need to combine them into collections delimited by #postid\n\n 
we need a graph function that goes thru live /notes pages and gets likes/replies and does statistics/networking tasks on the data 
that func is called periodically
script or something checks the process every 10 minutes and restarts if not found and restarts every 4 hours
got a problem with writing to files across threads"""

"""
NOte:
potential places for the code to break:
Tumblr.py
page_tasks, post_tasks, fetch_posts
Twitter.py
page_tasks, post_tasks, secondary
"""


"""
june 6
add feature to add users to recovery_list upon notecount and tk;
"""
