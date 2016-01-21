# coding=utf-8

from tgbot import plugintest, webserver
import webtest
import millionsbot


class WebTest(plugintest.PluginTestCase):
    def setUp(self):
        self.bot = self.prepare_bot(bot=millionsbot.setup('sqlite:///:memory:', '123'))
        self.bot.setup_db()
        self.webapp = webtest.TestApp(webserver.wsgi_app([self.bot]))
        self.received_id = 1

    def test_start(self):
        self.webapp.post_json('/update/123', params=self.build_message(u'/start'))
        reply = self.pop_reply()
        self.assertEqual(reply[0], 'sendMessage')
        self.assertEqual(
            reply[1]['reply_markup'],
            {'resize_keyboard': True, 'keyboard': [['Last Results'], ['Previous Results'], ['Random Key'], ['Enable Alerts']]}
        )

    def test_help(self):
        self.webapp.post_json('/update/123', params=self.build_message(u'/help'))
        self.assertReplied('''\
You can control me by sending these commands:

/last - last Euromillions results
/alerts - receive an alert when new results are announced
/results - Euromillions results for a specific date
/random - generate a random key
''')
