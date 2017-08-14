import re

import twilio.rest
import pmxbot
from pmxbot.core import command


from_number = '+15712573984'


@command()
def send_text(rest):
	"""
	Send an SMS message: pass the phone number and message to send.
	"""
	account = pmxbot.config.twilio_account
	token = pmxbot.config.twilio_token
	number, _, msg = rest.partition(' ')
	number = parse_number(number)
	if not msg:
		return
	msg = msg.encode('ascii')[:160]
	client = twilio.rest.Client(username=account, password=token)
	client.messages.create(to=number, from_=from_number, body=msg)
	return "Sent {count} chars to {number}".format(
		count=len(msg),
		number=number,
	)


def parse_number(input_):
	"""
	Strip everything but digits and + sign; ensure it begins with a country
	code.

	>>> parse_number('5555551212')
	'+15555551212'
	>>> parse_number('12025551212')
	'+12025551212'
	>>> parse_number('+44')
	'+44'
	"""
	clean = ''.join(re.findall('[\d+]*', input_))
	if not clean.startswith('+'):
		clean = clean.lstrip('1')
		clean = '+1' + clean
	return clean
