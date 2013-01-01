"""
HTTP API endpoint for the bot.
"""

import os

import cherrypy
import pmxbot.core

class Server(object):
	queue = []

	@cherrypy.expose
	def default(self, channel):
		self.queue.append(pmxbot.core.SwitchChannel(channel))
		self.queue.extend(line.rstrip()
			for line in cherrypy.request.body)
		return 'Message sent'

@pmxbot.core.execdelay("startup", channel=None, howlong=0)
def startup(*args, **kwargs):
	if not pmxbot.config.get('web api', False):
		return
	config = {
		'global': {
			'server.socket_host': '::0',
			'server.socket_port': os.environ.get('PORT', 8080),
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
