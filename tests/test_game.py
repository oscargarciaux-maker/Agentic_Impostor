import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import server

class GameTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch = patch.object(server, 'DATA', Path(self.tmp.name))
        self.patch.start()
        server.state = dict(id='test', status='playing', round=1, rounds=3,
            roles=['civil','impostor','civil','civil'], word='playa', messages=[], votes=[],
            engine='Simulación local', deadline=None, error=None)
    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()
    def test_private_views_and_public_state(self):
        self.assertIsNone(server.agent_view(1)['word'])
        self.assertEqual(server.agent_view(0)['word'], 'playa')
        self.assertNotIn('roles', server.agent_view(0))
        self.assertNotIn('roles', server.public())
        self.assertNotIn('word', server.public())
    def test_complete_autonomous_game_and_ledger(self):
        with patch.dict('os.environ', {'AGENT_TURN_SECONDS':'0'}), patch('server.os.getenv', side_effect=lambda k,d=None: '0' if k=='AGENT_TURN_SECONDS' else d):
            server.run_game()
        self.assertEqual(server.state['status'], 'finished')
        self.assertIn(len(server.state['messages']), (12, 21))
        self.assertIn(len(server.state['votes']), (4, 7))
        for v in server.state['votes']:
            self.assertNotEqual(v['name'], v['target'])
        saved=json.loads((Path(self.tmp.name)/'test.json').read_text())
        self.assertEqual(saved['roles'].count('impostor'),1)
        self.assertEqual(saved['status'],'finished')
    def test_engine_failure_is_visible(self):
        with patch('server.decide', side_effect=RuntimeError('private error')):
            server.run_game()
        self.assertEqual(server.state['status'], 'error')
        self.assertNotIn('private error', server.public()['error'])

    def test_wrong_expulsion_continues_without_eliminated_player(self):
        calls=[]
        def decision(i, voting=False):
            calls.append((server.state['cycle'], i, voting))
            if voting:
                # First cycle eliminates Bruno (civil), second eliminates Leo (impostor).
                target = 'Bruno' if server.state['cycle']==1 else 'Leo'
                if server.NAMES[i]==target: target='Mateo'
                return {'name':server.NAMES[i], 'target':target, 'reason':'test'}
            return {'name':server.NAMES[i], 'text':'pista', 'round':server.state['round']}
        with patch('server.decide', side_effect=decision), patch('server.time.sleep'):
            server.run_game()
        self.assertEqual(server.state['status'],'finished')
        self.assertEqual(server.state['winner'],'civiles')
        self.assertEqual(server.state['eliminated_players'],['Bruno','Leo'])
        self.assertTrue(any(c[0]==2 for c in calls))
        self.assertFalse(any(c[0]==2 and c[1]==0 for c in calls))

    def test_fixed_order_and_no_repeated_clues(self):
        server.state['word']='brújula'
        with patch.dict('os.environ', {'AGENT_TURN_SECONDS':'0'}, clear=True):
            server.run_game()
        messages=server.state['messages']
        self.assertEqual([m['name'] for m in messages[:12]],server.NAMES*3)
        words=[server.normalized(m['text']) for m in messages]
        self.assertEqual(len(words),len(set(words)))
        self.assertTrue(all(len(m['text'].split())==1 for m in messages))

    def test_api_repeated_word_is_retried_before_publication(self):
        server.state['messages']=[{'name':'Mateo','text':'Nórte','round':1}]
        with patch.dict('os.environ', {'AGENT_API_KEY':'test-only'}), patch('server.model_action',side_effect=[{'text':'norte'},{'text':'aguja'}]) as api:
            action=server.decide(0)
        self.assertEqual(action['text'],'aguja')
        self.assertEqual(api.call_count,2)
        self.assertEqual(len(server.state['messages']),1)

    def test_api_request_uses_economical_model_and_tracks_usage(self):
        from unittest.mock import MagicMock
        reply=MagicMock()
        reply.__enter__.return_value.read.return_value=json.dumps({'choices':[{'message':{'content':'{"text":"aguja"}'}}], 'usage':{'prompt_tokens':90,'completion_tokens':12}}).encode()
        with patch.dict('os.environ', {'AGENT_API_KEY':'test-only'}, clear=True), patch('server.urllib.request.urlopen',return_value=reply) as http:
            server.model_action(server.agent_view(0),False)
        payload=json.loads(http.call_args.args[0].data)
        self.assertEqual(payload['model'],'gpt-5-nano')
        self.assertEqual(payload['reasoning_effort'],'minimal')
        self.assertEqual(payload['max_completion_tokens'],256)
        self.assertEqual(server.state['usage']['calls'],1)
        self.assertEqual(server.state['usage']['prompt_tokens'],90)

    def test_api_budget_blocks_request(self):
        server.state['usage']={'calls':server.MAX_API_CALLS}
        with patch.dict('os.environ', {'AGENT_API_KEY':'test-only'}), patch('server.urllib.request.urlopen') as http:
            with self.assertRaises(RuntimeError):server.model_action(server.agent_view(0),False)
        http.assert_not_called()
