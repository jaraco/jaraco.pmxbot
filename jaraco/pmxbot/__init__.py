import socket

from pmxbot.core import command


@command("resolv", doc="resolve a hostname")  # type: ignore[misc] # pmxbot/pmxbot#113
def resolve(rest: str) -> str:
    """
    >>> resolve("localhost")
    '...'
    """
    return socket.getfqdn(rest)
