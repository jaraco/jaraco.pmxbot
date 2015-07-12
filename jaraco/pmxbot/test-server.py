import cherrypy
import pmxbot

from jaraco.pmxbot import http

pmxbot.config['BitBucket channels'] = dict(default='default')

@classmethod
def send_to(cls, channel, *msgs):
	print("Message for", channel)
	for msg in msgs:
		print(msg)

http.Server.send_to = send_to

if __name__ == '__main__':
	http.Server.start(log_screen=True)
	cherrypy.engine.block()
