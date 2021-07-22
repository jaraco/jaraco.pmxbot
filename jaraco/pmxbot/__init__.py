import socket

from pmxbot.core import command


@command("resolv", doc="resolve a hostname")
def resolve(rest):
    """
    >>> resolve("localhost")
    '...'
    """
    return socket.getfqdn(rest)
