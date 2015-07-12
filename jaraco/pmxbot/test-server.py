import cherrypy
import pmxbot

from jaraco.pmxbot import http


@classmethod
def send_to(cls, channel, *msgs):
	print("Message for", channel)
	for msg in msgs:
		print(msg)


if __name__ == '__main__':
	pmxbot.config['BitBucket channels'] = dict(default='default')
	http.Server.send_to = send_to
	http.Server.start(log_screen=True)
	cherrypy.engine.block()
