import json
import textwrap
from unittest import mock

import cherrypy
from cherrypy.test import helper

from jaraco.pmxbot.http import Server, Kiln


class ServerTest(helper.CPWebCase):

    def setUp(self):
        Server.queue.clear()

    def tearDown(self):
        Server.queue.clear()

    def test_send_to(self):
        Server.send_to('channel', 'msg1', 'msg2', 'msg3')
        assert Server.queue == ['channel', 'msg1', 'msg2', 'msg3']

    def test_send_to_multiline(self):
        Server.send_to('channel', 'msg1\nmsg2', 'msg3')
        assert Server.queue == ['channel', 'msg1', 'msg2', 'msg3']

    def test_send_to_multiple(self):
        Server.send_to('chan1', 'msg1')
        Server.send_to('chan2', 'msg2')
        Server.send_to('chan3', 'msg3\nmsg4')
        assert Server.queue == [
            'chan1', 'msg1',
            'chan2', 'msg2',
            'chan3', 'msg3', 'msg4',
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
        message = textwrap.dedent("""
            MySwarm1@host: encoding.py failed:
            traceback

            MySwarm2@host: some other error...
            fat
            traceback

            MySwarm3@host: bizarre bug;

            MySwarm4@host: py3 stacktraces contain multiline tracebacks:
            trackback1
            trackback1
            trackback1

            traceback2
            traceback2
            traceback2
            """)
        payload = {
            'tags': ['scheduled', 'failed'],
            'message': message,
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


class TestKiln:

    def setup(self):
        self.kiln = Kiln()

    def test_ciao(self):
        payload = {
            'commits': [
                {
                    'author': 'Ken Thomson <ken@unix.org>',
                    'branch': 'default',
                    'id': 'deadbeef',
                    'message': 'Nice commit',
                    'revision': 1234,
                    'tags': [],
                    'timestamp': '2017-03-03T09:57:29Z',
                    'url': 'https://yougov.kilnhg.com/Code/Repositories/A/repo/History/abcdefg'
                },
                {
                    'author': 'Ken Thomson <ken@unix.org>',
                    'branch': 'default',
                    'id': 'deadbeef',
                    'message': 'Another nice commit',
                    'revision': 1234,
                    'tags': ['my-branch'],
                    'timestamp': '2017-03-03T09:57:29Z',
                    'url': 'https://yougov.kilnhg.com/Code/Repositories/A/repo/History/abcdefg'
                },
            ],
            'pusher': {
                'accesstoken': False,
                'email': 'ken@unix.org',
                'fullName': 'ken'
            },
            'repository': {
                'central': True,
                'description': '',
                'id': 1234,
                'name': 'repo',
                'url': 'https://yougov.kilnhg.com/Code/Repositories/A/repo'
            },
            'timestamp': None
        }

        rows = list(self.kiln.format(**payload))
        assert rows == [
            'ken pushed 2 commits to repo (https://yougov.kilnhg.com/Code/Repositories/A/repo):',
            'Nice commit',
            '[my-branch] Another nice commit'
        ]
