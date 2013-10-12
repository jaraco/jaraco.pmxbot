"""
HTTP API endpoint for the bot.
"""

import os
import json

import cherrypy
import pmxbot.core


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
		Server.send_to(channel, self.format(**payload))
		return "OK"

	def format(self, commits, pusher, repository, **kwargs):
		return (
			"{pusher[fullName]} pushed {n_commits} commits "
			"to {repository[name]} "
			"({repository[url]})".format(
				n_commits=len(commits), **vars())
		)


class Server(object):
	queue = []

	new_relic = NewRelic()
	kiln = Kiln()

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
