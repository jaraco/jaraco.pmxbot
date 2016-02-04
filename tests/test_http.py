import json
from unittest import mock

import cherrypy
from cherrypy.test import helper

from jaraco.pmxbot.http import Server


class VelociraptorTest(helper.CPWebCase):

    @staticmethod
    def setup_server():
        cherrypy.tree.mount(Server())

    @property
    def server(self):
        return cherrypy.tree.apps[''].root

    def _get(self, **kwargs):
        return self.getPage("/velociraptor", **kwargs)

    def _post_json(self, data):

        body = json.dumps(data)
        kwargs = {
            'method': 'POST',
            'headers': [
                ('Content-Type', 'application/json'),
                ('Content-Length', str(len(body))),
            ],
            'body': body,
        }
        return self.getPage("/velociraptor", **kwargs)

    def test_only_post(self):
        self._get()
        self.assertStatus('405 Method Not Allowed')

    def test_event_invalid(self):
        for payload in [
                {},  # no tags
                {'tags': ['route']},  # no title
                {'tags': ['swarm', 'deploy', 'done']},  # no title
                {'tags': ['scheduled', 'failed']},  # no message
        ]:
            self._post_json(payload)
            self.assertStatus('400 Bad Request')

    def test_event_unknown(self):
        payload = {
            'tags': ['unknown'],
        }
        self._post_json(payload)
        self.assertStatus('200 OK')
        self.assertBody('IGNORED')

    @mock.patch('jaraco.pmxbot.http.Server.send_to')
    @mock.patch('jaraco.pmxbot.http.ChannelSelector.get_channels')
    def test_event_route(self, mock_get_channels, mock_send_to):
        mock_get_channels.return_value = ['chan1', 'chan2']
        payload = {
            'tags': ['route'],
            'title': 'My Swarm',
        }
        self._post_json(payload)
        self.assertStatus('200 OK')
        self.assertBody('OK')
        mock_send_to.assert_has_calls([
            mock.call('chan1', 'VR: Routed My Swarm'),
            mock.call('chan2', 'VR: Routed My Swarm'),
        ])

    @mock.patch('jaraco.pmxbot.http.Server.send_to')
    @mock.patch('jaraco.pmxbot.http.ChannelSelector.get_channels')
    def test_event_swarm_deploy_done(self, mock_get_channels, mock_send_to):
        mock_get_channels.return_value = ['chan1', 'chan2']
        payload = {
            'tags': ['swarm', 'deploy', 'done'],
            'title': 'Swarm MySwarm finished',
            'message': 'Swarm MySwarm finished',
        }
        self._post_json(payload)
        self.assertStatus('200 OK')
        self.assertBody('OK')
        mock_send_to.assert_has_calls([
            mock.call('chan1', 'VR: Swarm MySwarm finished'),
            mock.call('chan2', 'VR: Swarm MySwarm finished'),
        ])

    @mock.patch('jaraco.pmxbot.http.Server.send_to')
    @mock.patch('jaraco.pmxbot.http.ChannelSelector.get_channels')
    def test_event_scheduled_failed(self, mock_get_channels, mock_send_to):
        mock_get_channels.return_value = ['chan1']
        payload = {
            'tags': ['scheduled', 'failed'],
            'message': '\n\n'.join([
                'MySwarm1: encoding.py failed\ntraceback',
                'MySwarm2: some other error\nfat\ntraceback',
                'MySwarm3: bizarre bug',  # no traceback
            ])
        }
        self._post_json(payload)
        self.assertStatus('200 OK')
        self.assertBody('OK')
        mock_send_to.assert_has_calls([
            mock.call(
                'chan1',
                ('VR: Scheduled uptests failed for MySwarm1: '
                 'encoding.py failed\ntraceback'),
            ),
            mock.call(
                'chan1',
                ('VR: Scheduled uptests failed for MySwarm2: '
                 'some other error\nfat\ntraceback'),
            ),
            mock.call(
                'chan1',
                ('VR: Scheduled uptests failed for MySwarm3: '
                 'bizarre bug\n'),
            ),
        ])
