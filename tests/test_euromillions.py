# coding=utf-8
from tgbot import plugintest
from plugins.euromillions import EuromillionsPlugin

from requests.packages import urllib3
urllib3.disable_warnings()


class PluginTest(plugintest.PluginTestCase):
    def setUp(self):
        self.plugin = EuromillionsPlugin()
        self.bot = self.fake_bot(
            '',
            plugins=[self.plugin],
            inline_query=self.plugin,
            no_command=self.plugin
        )

    def test_last(self):
        self.receive_message('/last')
        self.assertReplied('No results for `latest`...')

        self.plugin.save_data('results', key2='latest', obj={
            "date": "2005-01-01",
            "numbers": "hello",
            "stars": "world"
        })
        self.receive_message('/last')
        self.assertReplied(u'''\
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
        self.assertReplied(u'''\
For which date?
Please use the format `YEAR-MM-DD`''')
        self.receive_message('invalid format')
        self.assertReplied(u'Please *use* the format `YEAR-MM-DD`')
        self.receive_message('2015-01-02')
        self.assertReplied(u'No results for `2015-01-02`...')
        self.receive_message('2999-01-02')
        self.assertReplied(u'I cannot foretell the future (at the moment?) but give /random a try...')
        self.receive_message('/results 2015-01-01')
        self.assertReplied(u'''\
Results for _2015-01-01_
\U0001F3BE
*hello*
\U00002B50
*world*''')

    def test_alerts(self):
        self.receive_message('/alerts')
        self.assertReplied(u'Alerts disabled, use /alertson to enable them')
        self.receive_message('/alertson')
        self.assertReplied(u'Alerts enabled')
        self.receive_message('/alertsoff')
        self.assertReplied(u'Alerts disabled')

    def test_group_join(self):
        chat = {
            'type': 'group',
            'title': 'test',
            'id': -1
        }
        self.receive_message('', chat=chat, group_chat_created=True)
        self.assertReplied(u'''\
Thanks for inviting me over!

Use /help to find out what I can do.''')

        self.receive_message('', chat=chat, new_chat_participant={'id': 2, 'first_name': 'Paul'})
        self.assertNoReplies()

        self.receive_message('', chat=chat, new_chat_participant=self.bot._bot_user.__dict__)
        self.assertReplied(u'''\
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
        self.assertReplied(u'''\
Latest Results for _2005-01-01_
\U0001F3BE
*10 19 38 43 46*
\U00002B50
*1 11*''')

        # new update without any changes should not trigger any reply
        self.clear_queues()
        with mock.patch(
                'time.gmtime',
                return_value=time.struct_time((2005, 1, 1, 20, 50, 36, 1, 18, 0))
        ):
            with mock.patch('requests.get', fake_get):
                self.plugin.cron_go('millions.update')
        self.assertNoReplies()

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
        self.assertReplied(u'''\
Latest Results for _2005-01-01_
\U0001F3BE
*hello*
\U00002B50
*world*''')
        self.receive_message('Enable Alerts')
        self.assertReplied(u'Alerts enabled')
        self.receive_message('Disable Alerts')
        self.assertReplied(u'Alerts disabled')
        self.receive_message('Previous Results')
        self.assertReplied(u'Please enter the date in the format `YEAR-MM-DD`')
        self.receive_message('whatever')
        self.assertReplied(u'Please *use* the format `YEAR-MM-DD`')
        self.receive_message('2005-01-02')
        self.assertReplied(u'No results for `2005-01-02`...')
        self.receive_message('2005-01-01')
        self.assertReplied(u'''\
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

    def test_inline(self):
        for m in xrange(13):
            for d in xrange(1, 29, 3):
                self.plugin.save_data('results', key2='2005-%02d-%02d' % (m, d), obj={
                    "numbers": "hello",
                    "stars": "2005-%02d-%02d" % (m, d)
                })

        self.plugin.save_data('results', key2='latest', obj={
            "date": "2005-12-28",
            "numbers": "hello",
            "stars": "2005-12-28"
        })

        self.receive_inline('')
        results = self.pop_reply()[1]['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], u'Latest (2005-12-28)')
        self.assertEqual(results[0]['message_text'], u'''\
Latest Results for _2005-12-28_
\U0001F3BE
*hello*
\U00002B50
*2005-12-28*''')

        self.receive_inline('2')
        reply = self.pop_reply()[1]
        results = reply['results']
        self.assertEqual(len(results), 20)
        self.assertEqual(reply['next_offset'], 20)
        self.assertEqual(results[0]['title'], u'2005-12-28')

        self.receive_inline('2', offset=20)
        reply = self.pop_reply()[1]
        results = reply['results']
        self.assertEqual(len(results), 20)
        self.assertEqual(reply['next_offset'], 40)
        self.assertEqual(results[0]['title'], u'2005-10-28')

        self.receive_inline('2005-01')
        reply = self.pop_reply()[1]
        results = reply['results']
        self.assertEqual(len(results), 10)
        self.assertNotIn('next_offset', reply)
        self.assertEqual(results[0]['title'], u'2005-01-28')
