import sys, re

"""
	About:
		You must authorize the application. https://api.tumblr.com/ Just fill that out.
		You must authorize an account. Use the access token and access token secret here.
		You can specify a blog name as long as it is owned by your account.
		You can only post text. HTML by default. You can embed images.
"""

DEFAULT = 'name'
accounts = {
	"name": {"id": 0, "access": "", "access_secret": "", "host_name": "", "api_key": ""}
}

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



class Post(object):
	def __init__(self, input_):
		self.input = input_
		self.result = 0
		self.kwargs = {}
	
	def run(self):
		self.parse_input()
		self.post()

	def matcher(self, string):
		key = string.group(2)
		value = string.group(4)
		try:
			self.kwargs[key] = value
		except:
			pass
		return string.group(5)

	def at(self, string):
		v = string.group(1)
		return '<a class="tumblelog">' + v + '</a>\xe2'

	def parse_input(self):
		output_ = re.sub(r'(^|\n)(title|blog|account|format|tags|state)(\:\s)(.+)(\n|$)', self.matcher, self.input)
		# output_ = re.sub(r'@(.+?)(\W|$)', self.at, output_)
		output_ = output_.replace('\n', '<br />').replace('\r', '').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;').replace('"', '\\"').replace('[[MORE]]', '</p><p>[[MORE]]</p><p>')
		output_ = '<p>' + output_ + '</p>'
		self.kwargs['body'] = output_
		try:
			acc = accounts[self.kwargs['account']]
		except KeyError as e:
			acc = accounts[DEFAULT]
		finally:
			ak = acc['access']
			aks = acc['access_secret']
			self.s = create_oauth(ak, aks)
		try:
			bl = self.kwargs['blog'] + '.tumblr.com'
		except KeyError as e:
			bl = acc['host_name']
		finally:
			self.host_name = bl
		self.params = {k:v for k,v in self.kwargs.items() if k in {'state','tags','title','body','format'}}

	def post(self):
		url = 'blog/%s/post' % self.host_name
		print(url)
		self.params['type'] = 'text'
		# self.params['native_inline_images'] = 'true'
		r = self.s.post(url=url, data=self.params)
		r.raise_for_status()
		self.result = 11

if __name__ == '__main__':
	input_ = sys.argv[1]
	p = Post(input_)
	p.run()
	sys.exit(p.result)
