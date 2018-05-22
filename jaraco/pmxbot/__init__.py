import socket

from pmxbot.core import command


@command("resolv", doc="resolve a hostname")
def resolve(client, event, channel, nick, rest):
	return socket.getfqdn(rest)
