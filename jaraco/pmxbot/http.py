"""
HTTP API endpoint for the bot.
"""

import os
import json
import logging

from jaraco.util.itertools import always_iterable
import cherrypy
import pmxbot.core


log = logging.getLogger(__name__)

class Jenkins(object):
	"""
	Handle JSON notifications as sent from
	https://wiki.jenkins-ci.org/display/JENKINS/Notification+Plugin
	"""
	@cherrypy.expose
	@cherrypy.tools.json_in()
	def default(self, channel):
		payload = cherrypy.request.json
		Server.send_to(channel, *self.build_messages(**payload))

	def build_messages(self, name, url, build, **kwargs):
		log.info("Got build from Jenkins: {build}".format(**vars()))
		if not build.get('phase') == 'FINISHED':
			return
		tmpl = "Build {build[number]} {build[status]} ({build[full_url]})"
		yield tmpl.format(**vars())

class NewRelic(object):

	@cherrypy.expose
	def default(self, channel, **kwargs):
		for key, value in kwargs.items():
			handler = getattr(self, key, None)
			if not handler: continue
			value = json.loads(value)
			Server.send_to(channel, handler(**value))
		return "OK"

	def alert(self, **kwargs):
		return (
			"Alert! [{application_name} {severity}] {message} ({alert_url})"
			.format(**kwargs)
		)

class Kiln(object):

	@cherrypy.expose
	def default(self, channel, payload):
		payload = json.loads(payload)
		log.info("Received payload with %s", payload)
		Server.send_to(channel, *self.format(**payload))
		return "OK"

	def format(self, commits, pusher, repository, **kwargs):
		commit_s = 'commit' if len(commits) == 1 else 'commits'
		yield (
			"{pusher[fullName]} pushed {number} {what} "
			"to {repository[name]} "
			"({repository[url]}) :".format(
				number=len(commits), what=commit_s, **vars())
		)
		for commit in commits:
			yield commit['message'].splitlines()[0]

class BitBucket(Kiln):
	"""
	BitBucket support is very similar to Kiln
	"""

	def format(self, commits, canon_url, repository, user, **kwargs):
		if not commits:
			return
		commit_s = 'commit' if len(commits) == 1 else 'commits'
		yield (
			"{user} pushed {number} {what} "
			"to {repository[name]} "
			"({canon_url}{repository[absolute_url]}) :".format(
				number=len(commits), what=commit_s, **vars())
		)
		for commit in commits:
			yield commit['message'].splitlines()[0]

class FogBugz(object):
	@cherrypy.expose
	def trigger(self, **event):
		if event['CaseNumber']:
			return self.handle_case(event)
		return "OK"

	def handle_case(self, event):
		log.info("Got case update from FogBugz: %s", event)
		channel_spec = pmxbot.config.get('fogbugz channels', {})
		if event['EventType'] == 'CaseOpened':
			base = "https://yougov.fogbugz.com"
			message = "{PersonEditingName} opened {Title} ({base}/default.asp?{CaseNumber})"
			proj = event['ProjectName']
			default_channels = channel_spec.get('default', [])
			matching_channels = channel_spec.get(proj, default_channels)
			for channel in always_iterable(matching_channels):
				Server.send_to(channel, message.format(base=base, **event))


class Server(object):
	queue = []

	new_relic = NewRelic()
	kiln = Kiln()
	jenkins = Jenkins()
	fogbugz = FogBugz()
	bitbucket = BitBucket()

	@classmethod
	def send_to(cls, channel, *msgs):
		cls.queue.append(pmxbot.core.SwitchChannel(channel))
		cls.queue.extend(msgs)

	@cherrypy.expose
	def default(self, channel):
		lines = (line.rstrip() for line in cherrypy.request.body)
		self.send_to(channel, *lines)
		return 'Message sent'


@pmxbot.core.execdelay("startup", channel=None, howlong=0)
def startup(*args, **kwargs):
	if not pmxbot.config.get('web api', False):
		return
	config = {
		'global': {
			'server.socket_host': '::0',
			'server.socket_port': int(os.environ.get('PORT', 8080)),
			'environment': 'production',
			'log.screen': False,
		}
	}
	cherrypy.config.update(config)
	cherrypy.tree.mount(Server(), '', config)
	cherrypy.engine.start()
	pmxbot.core.FinalRegistry.at_exit(cherrypy.engine.stop)

@pmxbot.core.execdelay("http", channel=None, howlong=0.3, repeat=True)
def relay(conn, event):
	while Server.queue:
		yield Server.queue.pop(0)
