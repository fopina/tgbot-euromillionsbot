# coding=utf-8
from tgbot import plugintest
from tgbot.botapi import Update
from plugins.euromillions import EuromillionsPlugin

from requests.packages import urllib3
urllib3.disable_warnings()


class EuromillionsPluginTest(plugintest.PluginTestCase):
    def setUp(self):
        self.plugin = EuromillionsPlugin()
        self.bot = self.fake_bot('', plugins=[self.plugin])
        self.received_id = 1

    def test_last(self):
        self.plugin.save_data('results', key2='latest', obj={
            "date": "2005-01-01",
            "numbers": "hello",
            "stars": "world"
        })
        self.receive_message('/last')
        self.assertReplied(self.bot, u'''\
Latest results _2005-01-01_
\U0001F3BE
*hello*
\U00002B50
*world*''')

    def test_cron_populate(self):
        import mock
        import time

        def fake_get(*args, **kwargs):
            if 'params' in kwargs:
                year = kwargs['params']['result']
            else:
                year = time.gmtime().tm_year

            r = type('Test', (object,), {})()
            r.json = lambda: {
                "drawns": [
                    {
                        "date": "%d-01-01" % year,
                        "numbers": "10 19 38 43 46",
                        "stars": "1 11 %d" % year
                    }
                ]
            }
            return r

        with mock.patch(
                'time.gmtime',
                return_value=time.struct_time((2005, 1, 1, 20, 50, 36, 0, 18, 0))
        ):
            with mock.patch('requests.get', fake_get):
                self.plugin.cron_go('millions.populate')

        self.assertEqual(
            list(self.plugin.iter_data_key_keys('results')),
            [u'2004-01-01', u'2005-01-01', u'latest']
        )
        self.assertEqual(
            self.plugin.read_data('results', 'latest'),
            {
                "date": "2005-01-01",
                "numbers": "10 19 38 43 46",
                "stars": "1 11 2005"
            }
        )
        self.assertEqual(
            self.plugin.read_data('results', '2004-01-01'),
            {
                "numbers": "10 19 38 43 46",
                "stars": "1 11 2004"
            }
        )
        self.assertEqual(
            self.plugin.read_data('results', '2005-01-01'),
            {
                "numbers": "10 19 38 43 46",
                "stars": "1 11 2005"
            }
        )

    def test_cron_update(self):
        import mock
        import time

        def fake_get(*args, **kwargs):
            r = type('Test', (object,), {})()
            r.json = lambda: {
                "drawns": [
                    {
                        "date": "2005-01-01",
                        "numbers": "10 19 38 43 46",
                        "stars": "1 11"
                    }
                ]
            }
            return r

        # update on Monday (should do nothing)
        with mock.patch(
                'time.gmtime',
                return_value=time.struct_time((2005, 1, 1, 20, 50, 36, 0, 18, 0))
        ):
            with mock.patch('requests.get', fake_get):
                self.plugin.cron_go('millions.update')

        self.assertEqual(
            list(self.plugin.iter_data_key_keys('results')),
            []
        )

        # update on Tuesday (should update)
        with mock.patch(
                'time.gmtime',
                return_value=time.struct_time((2005, 1, 1, 20, 50, 36, 1, 18, 0))
        ):
            with mock.patch('requests.get', fake_get):
                self.plugin.cron_go('millions.update')

        self.assertEqual(
            list(self.plugin.iter_data_key_keys('results')),
            [u'latest']
        )
        self.assertEqual(
            self.plugin.read_data('results', 'latest'),
            {
                "date": "2005-01-01",
                "numbers": "10 19 38 43 46",
                "stars": "1 11"
            }
        )

    def receive_message(self, text, sender=None, chat=None):
        if sender is None:
            sender = {
                'id': 1,
                'first_name': 'John',
                'last_name': 'Doe',
            }

        if chat is None:
            chat = sender

        self.bot.process_update(
            Update.from_dict({
                'update_id': self.received_id,
                'message': {
                    'message_id': self.received_id,
                    'text': text,
                    'chat': chat,
                    'from': sender,
                }
            })
        )

        self.received_id += 1
