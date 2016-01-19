# coding=utf-8

from tgbot import plugintest, webserver, botapi
import webtest
import millionsbot


class FakeTelegramBotRPCRequest(botapi.TelegramBotRPCRequest):
    # TODO - improve this and add it to tgbot.plugintest
    QUEUE = []

    def _async_call(self):
        FakeTelegramBotRPCRequest.QUEUE.append((self.api_method, self.params))
        if self.api_method == 'getMe':
            result = {
                'id': 9999999,
                'first_name': 'Test',
                'last_name': 'Bot',
                'username': 'test_bot'
            }
        else:
            result = {}

        if self.on_result is None:
            self.result = result
        else:
            self.result = self.on_result(result)

        if self.on_success is not None:
            self.on_success(self.result)

    # overriding run() to prevent actual async calls to be able to assert async message sending
    def run(self):
        self._async_call()
        return self

    # same as above
    def wait(self):
        if self.error is not None:
            return self.error
        return self.result


class WebTest(plugintest.PluginTestCase):
    def setUp(self):
        botapi.TelegramBotRPCRequest = FakeTelegramBotRPCRequest
        FakeTelegramBotRPCRequest.QUEUE = []
        self.bot = millionsbot.setup('sqlite:///:memory:', '123')
        self.bot.setup_db()
        self.webapp = webtest.TestApp(webserver.wsgi_app([self.bot]))
        self.received_id = 1

    def test_ping(self):
        self.assertEqual(self.webapp.get('/ping/').text, '<b>Pong!</b>')

    def test_update_invalid_token(self):
        with self.assertRaisesRegexp(webtest.app.AppError, 'Bad response: 404 Not Found'):
            self.webapp.post_json('/update/invalid', params=self.build_update('hello'))

    def test_start(self):
        self.assertEqual(len(FakeTelegramBotRPCRequest.QUEUE), 0)
        self.webapp.post_json('/update/123', params=self.build_update(u'/start'))
        self.assertTrue(len(FakeTelegramBotRPCRequest.QUEUE))
        self.assertEqual(FakeTelegramBotRPCRequest.QUEUE[-1][0], 'sendMessage')
        self.assertEqual(
            FakeTelegramBotRPCRequest.QUEUE[-1][1]['reply_markup'],
            '{"resize_keyboard": true, "keyboard": [["Last Results"], ["Previous Results"], ["Enable Alerts"]]}'
        )

    def test_help(self):
        self.assertEqual(len(FakeTelegramBotRPCRequest.QUEUE), 0)
        self.webapp.post_json('/update/123', params=self.build_update(u'/help'))
        self.assertTrue(len(FakeTelegramBotRPCRequest.QUEUE))
        self.assertEqual(FakeTelegramBotRPCRequest.QUEUE[-1][0], 'sendMessage')
        self.assertEqual(FakeTelegramBotRPCRequest.QUEUE[-1][1]['text'], '''\
You can control me by sending these commands:

/last - last Euromillions results
/alerts - receive an alert when new results are announced
/results - euromillions results for a specific date
''')

    def build_update(self, text, sender=None, chat=None, reply_to_message_id=None):
        if sender is None:
            sender = {
                'id': 1,
                'first_name': 'John',
                'last_name': 'Doe',
            }

        if chat is None:
            chat = {'type': 'private'}
            chat.update(sender)

        reply_to_message = None

        if reply_to_message_id is not None:
            reply_to_message = {
                'message_id': reply_to_message_id,
                'chat': chat,
            }

        update = {
            'update_id': self.received_id,
            'message': {
                'message_id': self.received_id,
                'text': text,
                'chat': chat,
                'from': sender,
                'reply_to_message': reply_to_message,
            }
        }

        self.received_id += 1

        return update
