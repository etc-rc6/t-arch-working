"""Sublime Text plugin for post.py"""

import sublime, sublime_plugin, subprocess, time, json, os

MYPATH = os.path.dirname(os.path.abspath(__file__))
POST = os.path.join(MYPATH, 'post.py')

class WorkOrder(object):

	def __init__(self):
		self.wd = os.path.join(MYPATH, 'failures')

	def delete(self):
		open(self.wd, 'w').close()

	def open(self, vstring=None):
		self.todo_list = []
		# extraneous
		if not vstring:
			try:
				with open(self.wd, 'r') as nctn:
					self.todo_list = json.load(nctn)
				print('workorder: read failures')
			except: pass
		# /extraneous
		else:
			self.todo_list.append({'order':vstring})

	def close(self, failed):
		for value in failed:
			del value['obj']
		with open(self.wd, 'rw') as nctn:
			prev = json.load(nctn)
			prev += failed
			nctn.write(json.dumps(failed))





class TPostCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		self.post()

	def post(self, use_vstring=True):
		self.vstring = '' # "view" string
		if use_vstring:
			self.get_vstring()
		self.work_order = WorkOrder()
		self.work_order.open(self.vstring)
		for value in self.work_order.todo_list:
			p = subprocess.Popen(['python', POST, value['order']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			value['obj'] = p
			time.sleep(1)
		self.handle_threads()
		if self.failed:
			self.work_order.close(self.failed)

	def get_vstring(self):
		"""About: get all the selected regions or get whole open file"""
		if self.view.has_non_empty_selection_region():
			sels = self.view.sel()
			for x in sels:
				self.vstring += self.view.substr(x)
		else:
			self.vstring += self.view.substr(sublime.Region(0,self.view.size()))

	def handle_threads(self):
		self.failed = []
		for value in self.work_order.todo_list:
			print(value)
			value['obj'].wait()
			if value['obj'].returncode == 11:
				print('success')
			else:
				print (value['obj'].communicate()[1])
				self.failed.append(value)






class ClearBufferCommand(WorkOrder, sublime_plugin.ApplicationCommand):
	def run(self):
		self.delete()

class BufferOnlyCommand(TPostCommand):
	def run(self, edit):
		self.post(False)