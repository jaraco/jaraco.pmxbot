"""
HTTP API endpoint for the bot.
"""

import re
import os
import json
import logging
import codecs
import textwrap
import urllib.parse
from itertools import chain

import pkg_resources
from jaraco.itertools import always_iterable
import cherrypy
import pmxbot.core
import cherrypy_cors


log = logging.getLogger(__name__)


class ChannelSelector(object):
	@property
	def channel_spec_config(self):
		"""
		The config attribute in the pmxbot.config where channels are specified
		"""
		return '{self.__class__.__name__} channels'.format(**vars())

	def get_channels(self, key):
		spec = pmxbot.config.get(self.channel_spec_config, {})
		default_channels = spec.get('default', [])
		matching_channels = spec.get(key, default_channels)
		if isinstance(matching_channels, dict) and 'channels' in matching_channels:
			matching_channels = matching_channels['channels']
		return always_iterable(matching_channels)


class Jenkins(ChannelSelector):
	"""
	Handle JSON notifications as sent from
	https://wiki.jenkins-ci.org/display/JENKINS/Notification+Plugin
	"""

	# Notification plugin changed wording
	FINAL_PHASES = ['FINISHED', 'FINALIZED']

	@cherrypy.expose
	@cherrypy.tools.json_in()
	def default(self, channel=None):
		# retained for compatibility
		del channel
		payload = cherrypy.request.json
		job = payload['name']
		if self.display_message(**payload):
			for channel in self.get_channels(job):
				Server.send_to(channel, *self.build_messages(**payload))

	def display_message(self, name, url, build, **kwargs):
		"""
		Decides if message should be displayed based on its status and config.
		Mostly done to not display the SUCCESS statuses of periodic builds.
		Options are SUCCESS, UNSTABLE, FAILED, ABORTED, and CYCLE.
		"""
		channel_spec = pmxbot.config.get(self.channel_spec_config, {})
		job_spec = channel_spec.get(name, {})
		allowed_statuses = []
		if isinstance(job_spec, dict) and 'statuses' in job_spec:
			allowed_statuses = always_iterable(job_spec["statuses"])
		return not allowed_statuses or build.get('status') in allowed_statuses

	def build_messages(self, name, url, build, **kwargs):
		log.info("Got build from Jenkins: %s", build)
		if build.get('phase') not in self.FINAL_PHASES:
			return
		tmpl = "Build {build[number]} {build[status]} ({build[full_url]})"
		yield tmpl.format(**vars())


class NewRelic(object):

	@cherrypy.expose
	def default(self, channel, **kwargs):
		for key, value in kwargs.items():
			handler = getattr(self, key, None)
			if not handler:
				continue
			value = json.loads(value)
			Server.send_to(channel, handler(**value))
		return "OK"

	def alert(self, **kwargs):
		return (
			"Alert! [{application_name} {severity}] {message} ({alert_url})"
			.format(**kwargs)
		)


class Kiln(ChannelSelector):

	@cherrypy.expose
	def default(self, payload):
		payload = json.loads(payload)
		log.info("Received payload with %s", payload)
		for channel in self.get_channels(payload['repository']['name']):
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
	Bitbucket has two models, the webhooks and the legacy POST service.
	Legacy POST support is very similar to Kiln, so let its default
	method handle that.
	"""

	@cherrypy.expose
	@cherrypy.tools.json_in(debug=True, force=False)
	def default(self, payload=None):
		if payload:
			return super(BitBucket, self).default(payload)

		payload = cherrypy.request.json
		log.info("Received Bitbucket webhook %s", payload)
		user = payload['actor']['display_name']
		canon_url = ''
		repository = dict(
			name=payload['repository']['name'],
			absolute_url=payload['repository']['links']['html']['href'],
		)
		commits = [
			change['new']['target']
			for change in payload['push']['changes']
			if change['new'] is not None
		]
		for channel in self.get_channels(payload['repository']['name']):
			messages = self.format(
				user=user,
				commits=commits,
				canon_url=canon_url,
				repository=repository,
			)
			Server.send_to(channel, *messages)

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


class FogbugzEventType(str):
	@property
	def action(self):
		"""
		For an EventType, return the action in lowercase,
		stripping the 'Case' prefix.
		"""
		_, _, action = self.partition('Case')
		return action.lower()


class FogBugz(ChannelSelector):
	handled_types = 'CaseOpened', 'CaseClosed'

	@cherrypy.expose
	def trigger(self, **event):
		if event['CaseNumber']:
			return self.handle_case(event)
		return "OK"

	def handle_case(self, event):
		log.info("Got case update from FogBugz: %s", event)

		if event['EventType'] not in self.handled_types:
			return

		event['EventType'] = FogbugzEventType(event['EventType'])

		base = "https://yougov.fogbugz.com"
		message = (
			"{PersonEditingName} {EventType.action} {Title} "
			"({base}/default.asp?{CaseNumber})"
		)
		proj = event['ProjectName']
		for channel in self.get_channels(proj):
			Server.send_to(channel, message.format(base=base, **event))


class Velociraptor(ChannelSelector):

	SWARM_DEPLOY_DONE_RE = re.compile(r'Swarm (.+) finished')

	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.tools.json_in()
	def default(self):
		event = cherrypy.request.json
		log.info("Received event with %s", event)
		self._validate_event(event)
		tags = set(event['tags'])

		if 'route' in tags:
			self._handle_route(event)
			return 'OK'
		elif {'swarm', 'deploy', 'done'} == tags:
			self._handle_swarm_deploy_done(event)
			return 'OK'
		elif {'scheduled', 'failed'} == tags:
			self._handle_scheduled_failed(event)
			return 'OK'
		else:
			log.info("Ignoring event")
			return 'IGNORED'

	def _handle_route(self, event):
		self._validate_event_route(event)

		swarm = event['title']
		app, sep, rest = swarm.partition('-')
		msg = "Routed {swarm}".format(**locals())
		self._broadcast(app, msg)

	def _handle_swarm_deploy_done(self, event):
		self._validate_event_swarm_deploy_done(event)

		title = event['title']
		match = self.SWARM_DEPLOY_DONE_RE.match(title)
		assert match is not None, 'Invalid title {}'.format(title)
		swarm = match.groups()[0]
		app, sep, rest = swarm.partition('-')
		msg = event['message']
		self._broadcast(app, msg)

	def _handle_scheduled_failed(self, event):
		self._validate_event_scheduled_failed(event)
		msg = event['message']

		def parse_msg():
			'''Parse this notification message.

			The message is a sequence of individual failures.
			Each failure starts with a "header",
			containing the appname, host, etc. and then a
			complex traceback, possibly spanninig multiple lines.

			We parse by looking for a line that looks like
			a header and accumulating traceback lines.
			We yield previous header and traceback as soon
			as we hit the following header.
			'''
			header_re = re.compile(
				r'(?P<appname>[a-zA-Z0-9_\-\.]+)'
				r'@(?P<hostname>[a-zA-Z0-9\.]+): '
				r'(?P<summary>[^\n]*)')
			gs, tb = {}, []
			for line in msg.splitlines():
				m = header_re.match(line)
				if m is not None:
					# This line looks like a header
					if gs:
						# Yield previous item
						yield gs, '\n'.join(tb)
					# Initialize accumulator
					gs, tb = m.groups(), []
				else:
					# This must be a traceback line
					tb.append(line)
			# Yield last failure, too
			if gs:
				yield gs, '\n'.join(tb)

		for msg_ in parse_msg():
			(swarm, hostname, reason), _traceback = msg_
			app, sep, rest = swarm.partition('-')
			text = (
				'Scheduled uptests failed for '
				'{swarm}@{hostname}: {reason}'
			).format(**locals())
			self._broadcast(app, text)

	def _broadcast(self, app, msg):
		channels = self.get_channels(app)
		if not channels:
			log.warning("No channels to send to.")
			return
		for channel in channels:
			log.info("Sending to %s", channel)
			Server.send_to(channel, 'VR: ' + msg)

	def _validate_event(self, event):
		if 'tags' not in event:
			raise cherrypy.HTTPError(400, 'Missing tags')

	def _validate_event_route(self, event):
		if 'title' not in event:
			raise cherrypy.HTTPError(400, 'Missing title')

	def _validate_event_swarm_deploy_done(self, event):
		if 'title' not in event:
			raise cherrypy.HTTPError(400, 'Missing title')
		if 'message' not in event:
			raise cherrypy.HTTPError(400, 'Missing message')

	def _validate_event_scheduled_failed(self, event):
		if 'message' not in event:
			raise cherrypy.HTTPError(400, 'Missing message')


def actually_decode():
	"""
	CherryPy decode tool doesn't actually decode anything unless the body
	is multipart. This tool is different and will decode the body.
	"""
	# assume UTF-8 and to hell with the specs
	dec = codecs.getincrementaldecoder('utf-8')()
	cherrypy.request.body = map(dec.decode, cherrypy.request.body)

adt = cherrypy.Tool('before_handler', actually_decode)
cherrypy.tools.actually_decode = adt


class Server(object):
	queue = []

	new_relic = NewRelic()
	kiln = Kiln()
	jenkins = Jenkins()
	fogbugz = FogBugz()
	bitbucket = BitBucket()
	velociraptor = Velociraptor()

	@classmethod
	def send_to(cls, channel, *msgs):
		cls.queue.append(pmxbot.core.SwitchChannel(channel))
		# We must send line-by-line, so split multiline messages
		lines = chain(*(msg.splitlines() for msg in msgs))
		cls.queue.extend(lines)

	@cherrypy.expose
	@cherrypy.tools.actually_decode()
	def default(self, channel):
		lines = (line.rstrip() for line in cherrypy.request.body)
		self.send_to(channel, *lines)
		return 'Message sent'

	@cherrypy.expose
	def bookmarklet(self):
		"""
		Render the bookmarklet for easy installation.
		"""
		return self.render_bookmarklet()

	@staticmethod
	def render_bookmarklet():
		"""
		>>> cherrypy.request.headers['Host'] = 'pmxbot.example.com'
		>>> bm = Server.render_bookmarklet()
		>>> 'pmxbot.example.com' in bm
		True
		>>> '%20' in bm
		True
		>>> 'href="javascript:' in bm
		True
		"""
		script = pkg_resources.resource_string(__name__, 'bookmarklet-min.js')
		script = script.decode('utf-8').strip()
		hostname = cherrypy.request.headers['Host']
		script = script.replace('ircbot.example.com', hostname)
		script_href = 'javascript:' + urllib.parse.quote(script)
		tmpl = textwrap.dedent("""
			<html>
			<head></head>
			<body>
				Here is your bookmarklet:
				<a href="{script_href}">Send to IRC</a>.
			</body>
			</html>
			""")
		return tmpl.format_map(locals())

	@classmethod
	def start(cls, log_screen=False):
		cherrypy_cors.install()
		config = {
			'global': {
				'server.socket_host': '::0',
				'server.socket_port': int(os.environ.get('PORT', 8080)),
				'environment': 'production',
				'log.screen': log_screen,
			},
			'/': {
				'cors.expose_public.on': True,
			},
		}
		cherrypy.config.update(config)
		cherrypy.tree.mount(cls(), '', config)
		cherrypy.engine.start()


@pmxbot.core.execdelay("startup", channel=None, howlong=0)
def startup(*args, **kwargs):
	if not pmxbot.config.get('web api', False):
		return
	Server.start()
	pmxbot.core.FinalRegistry.at_exit(cherrypy.engine.stop)


@pmxbot.core.execdelay("http", channel=None, howlong=0.3, repeat=True)
def relay(conn, event):
	while Server.queue:
		yield Server.queue.pop(0)
