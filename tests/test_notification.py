import pytest
import pmxbot
from jaraco.collections import ItemsAsAttributes

from jaraco.pmxbot import notification


@pytest.fixture
def twilio_test_credentials(monkeypatch):
	class ConfigDict(ItemsAsAttributes, dict):
		pass

	monkeypatch.setattr(pmxbot, 'config', ConfigDict(), raising=False)
	monkeypatch.setitem(
		pmxbot.config, 'twilio_account', 'ACa3ea172f6b198b5f030c160518460f19',
	)
	monkeypatch.setitem(
		pmxbot.config, 'twilio_token', 'd011e427bff04fdf56987aeb77aadeb4',
	)


def test_send_text(twilio_test_credentials):
	res = notification.send_text(rest='+15555551212 <3 pmxbot')
	assert res == 'Sent 9 chars to +15555551212'