import json
from unittest import mock

import cherrypy
from cherrypy.test import helper

from jaraco.pmxbot.http import Server


class ServerTest(helper.CPWebCase):

    def setUp(self):
        Server.queue.clear()

    def tearDown(self):
        Server.queue.clear()

    def test_send_to(self):
        Server.send_to('channel', 'msg1', 'msg2', 'msg3')
        assert Server.queue == ['#channel', 'msg1', 'msg2', 'msg3']

    def test_send_to_multiline(self):
        Server.send_to('channel', 'msg1\nmsg2', 'msg3')
        assert Server.queue == ['#channel', 'msg1', 'msg2', 'msg3']

    def test_send_to_multiple(self):
        Server.send_to('chan1', 'msg1')
        Server.send_to('chan2', 'msg2')
        Server.send_to('chan3', 'msg3\nmsg4')
        assert Server.queue == [
            '#chan1', 'msg1',
            '#chan2', 'msg2',
            '#chan3', 'msg3', 'msg4',
        ]


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
                'MySwarm1@host: encoding.py failed:\ntraceback',
                'MySwarm2@host: some other error...\nfat\ntraceback',
                'MySwarm3@host: bizarre bug;',  # no traceback
                '''MySwarm4@host: py3 stacktraces contain multiline tracebacks:
trackback1
trackback1
trackback1

traceback2
traceback2
traceback2
''',
            ])
        }
        self._post_json(payload)
        self.assertStatus('200 OK')
        self.assertBody('OK')
        assert mock_send_to.call_args_list == [
            mock.call(
                'chan1',
                ('VR: Scheduled uptests failed for MySwarm1@host: '
                 'encoding.py failed:'),
            ),
            mock.call(
                'chan1',
                ('VR: Scheduled uptests failed for MySwarm2@host: '
                 'some other error...'),
            ),
            mock.call(
                'chan1',
                ('VR: Scheduled uptests failed for MySwarm3@host: '
                 'bizarre bug;'),
            ),
            mock.call(
                'chan1',
                ('VR: Scheduled uptests failed for MySwarm4@host: '
                 'py3 stacktraces contain multiline tracebacks:'),
            ),
        ]
