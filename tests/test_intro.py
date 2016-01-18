# coding=utf-8
from tgbot import plugintest
from tgbot.botapi import Update
from plugins.intro import IntroPlugin


class IntroPluginTest(plugintest.PluginTestCase):
    def test_start_hello(self):
        self.bot = self.fake_bot(
            '',
            plugins=[IntroPlugin()]
        )
        self.received_id = 1
        self.receive_message('/start')
        self.assertReplied(self.bot, 'Hello!')

    def test_start_world(self):
        self.bot = self.fake_bot(
            '',
            plugins=[IntroPlugin(intro_text='World!')]
        )
        self.received_id = 1
        self.receive_message('/start')
        self.assertReplied(self.bot, 'World!')

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
