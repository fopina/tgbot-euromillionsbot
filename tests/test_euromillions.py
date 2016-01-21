# coding=utf-8
from tgbot import plugintest
from tgbot.botapi import Update
from plugins.euromillions import EuromillionsPlugin

from requests.packages import urllib3
urllib3.disable_warnings()


class PluginTest(plugintest.PluginTestCase):
    def setUp(self):
        self.plugin = EuromillionsPlugin()
        self.bot = self.fake_bot('', plugins=[self.plugin], no_command=self.plugin)
        self.received_id = 1

    def test_last(self):
        self.receive_message('/last')
        self.assertReplied(self.bot, 'No results for `latest`...')

        self.plugin.save_data('results', key2='latest', obj={
            "date": "2005-01-01",
            "numbers": "hello",
            "stars": "world"
        })
        self.receive_message('/last')
        self.assertReplied(self.bot, u'''\
Latest Results for _2005-01-01_
\U0001F3BE
*hello*
\U00002B50
*world*''')

    def test_results(self):
        self.plugin.save_data('results', key2='2015-01-01', obj={
            "numbers": "hello",
            "stars": "world"
        })
        self.receive_message('/results')
        self.assertReplied(self.bot, u'''\
For which date?
Please use the format `YEAR-MM-DD`''')
        self.receive_message('invalid format')
        self.assertReplied(self.bot, u'Please *use* the format `YEAR-MM-DD`')
        self.receive_message('2015-01-02')
        self.assertReplied(self.bot, u'No results for `2015-01-02`...')
        self.receive_message('2999-01-02')
        self.assertReplied(self.bot, u'I cannot foretell the future (at the moment?) but give /random a try...')
        self.receive_message('/results 2015-01-01')
        self.assertReplied(self.bot, u'''\
Results for _2015-01-01_
\U0001F3BE
*hello*
\U00002B50
*world*''')

    def test_alerts(self):
        self.receive_message('/alerts')
        self.assertReplied(self.bot, u'Alerts disabled, use /alertson to enable them')
        self.receive_message('/alertson')
        self.assertReplied(self.bot, u'Alerts enabled')
        self.receive_message('/alertsoff')
        self.assertReplied(self.bot, u'Alerts disabled')

    def test_group_join(self):
        chat = {
            'type': 'group',
            'title': 'test',
            'id': -1
        }
        self.receive_message('', chat=chat, group_chat_created=True)
        self.assertReplied(self.bot, u'''\
Thanks for inviting me over!

Use /help to find out what I can do.''')

        self.clear_replies(self.bot)
        self.receive_message('', chat=chat, new_chat_participant={'id': 2, 'first_name': 'Paul'})
        self.assertRaisesRegexp(AssertionError, 'No replies', self.last_reply, self.bot)

        self.receive_message('', chat=chat, new_chat_participant=self.bot._bot_user.__dict__)
        self.assertReplied(self.bot, u'''\
Thanks for inviting me over!

Use /help to find out what I can do.''')

    def test_random(self):
        self.receive_message('/random')
        self.assertRegexpMatches(self.last_reply(self.bot), u'''\
Here's a random key for you!
\U0001f3be
\*\d+ \d+ \d+ \d+ \d+\*
\u2b50
\*\d+ \d+\*''')

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

        # enable alerts for the test user
        self.plugin.save_data('1', obj=True)

        # update on Monday (should do nothing)
        with mock.patch(
                'time.gmtime',
                return_value=time.struct_time((2005, 1, 1, 20, 50, 36, 0, 18, 0))
        ):
            with mock.patch('requests.get', fake_get):
                self.plugin.cron_go('millions.update')

        # assert latest was not set nor the test user received alert
        self.assertEqual(
            list(self.plugin.iter_data_key_keys('results')),
            []
        )
        self.assertRaisesRegexp(AssertionError, 'No replies', self.last_reply, self.bot)

        # update on Tuesday (should update)
        with mock.patch(
                'time.gmtime',
                return_value=time.struct_time((2005, 1, 1, 20, 50, 36, 1, 18, 0))
        ):
            with mock.patch('requests.get', fake_get):
                self.plugin.cron_go('millions.update')

        # assert latest was set and the test user received alert
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
        self.assertReplied(self.bot, u'''\
Latest Results for _2005-01-01_
\U0001F3BE
*10 19 38 43 46*
\U00002B50
*1 11*''')

        # new update without any changes should not trigger any reply
        self.clear_replies(self.bot)
        with mock.patch(
                'time.gmtime',
                return_value=time.struct_time((2005, 1, 1, 20, 50, 36, 1, 18, 0))
        ):
            with mock.patch('requests.get', fake_get):
                self.plugin.cron_go('millions.update')
        self.assertRaisesRegexp(AssertionError, 'No replies', self.last_reply, self.bot)

    def test_chat(self):
        self.plugin.save_data('results', key2='latest', obj={
            "date": "2005-01-01",
            "numbers": "hello",
            "stars": "world"
        })
        self.plugin.save_data('results', key2='2005-01-01', obj={
            "numbers": "hello",
            "stars": "world"
        })
        self.receive_message('Last Results')
        self.assertReplied(self.bot, u'''\
Latest Results for _2005-01-01_
\U0001F3BE
*hello*
\U00002B50
*world*''')
        self.receive_message('Enable Alerts')
        self.assertReplied(self.bot, u'Alerts enabled')
        self.receive_message('Disable Alerts')
        self.assertReplied(self.bot, u'Alerts disabled')
        self.receive_message('Previous Results')
        self.assertReplied(self.bot, u'Please enter the date in the format `YEAR-MM-DD`')
        self.receive_message('whatever')
        self.assertReplied(self.bot, u'Please *use* the format `YEAR-MM-DD`')
        self.receive_message('2005-01-02')
        self.assertReplied(self.bot, u'No results for `2005-01-02`...')
        self.receive_message('2005-01-01')
        self.assertReplied(self.bot, u'''\
Results for _2005-01-01_
\U0001F3BE
*hello*
\U00002B50
*world*''')
        self.receive_message('Random Key')
        self.assertRegexpMatches(self.last_reply(self.bot), u'''\
Here's a random key for you!
\U0001f3be
\*\d+ \d+ \d+ \d+ \d+\*
\u2b50
\*\d+ \d+\*''')

    def receive_message(self, text, sender=None, chat=None, group_chat_created=None, new_chat_participant=None):
        if sender is None:
            sender = {
                'id': 1,
                'first_name': 'John',
                'last_name': 'Doe',
            }

        if chat is None:
            chat = {'type': 'private'}
            chat.update(sender)

        self.bot.process_update(
            Update.from_dict({
                'update_id': self.received_id,
                'message': {
                    'message_id': self.received_id,
                    'text': text,
                    'chat': chat,
                    'from': sender,
                    'group_chat_created': group_chat_created,
                    'new_chat_participant': new_chat_participant
                }
            })
        )

        self.received_id += 1
