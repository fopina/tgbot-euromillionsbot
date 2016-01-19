# coding=utf-8
from tgbot import plugintest, pluginbase
from tgbot.botapi import Update, ReplyKeyboardMarkup
from plugins.intro import IntroPlugin


class PluginTest(plugintest.PluginTestCase):
    def setUp(self):
        self.bot = self.fake_bot('', plugins=[IntroPlugin()])
        self.received_id = 1

    def test_start_hello(self):
        self.receive_message('/start')
        self.assertReplied(self.bot, 'Hello!')

    def test_start_world_with_menu(self):
        def menu(chat):
            return ReplyKeyboardMarkup.create(keyboard=[['One']])

        self.bot = self.fake_bot(
            '',
            plugins=[IntroPlugin(intro_text='World!', start_menu_builder=menu)]
        )
        self.received_id = 1
        self.receive_message('/start')

        # TODO: update tgbotplug plugintest to allow validation of reply_markup
        self.assertReplied(self.bot, 'World!')

    def test_help(self):
        class TestPlugin(pluginbase.TGPluginBase):
            def list_commands(self):
                return (
                    pluginbase.TGCommandBase('shoot', None, 'method None breaks for sure'),
                )

        self.bot = self.fake_bot('', plugins=[IntroPlugin(), TestPlugin()])
        self.receive_message('/help')
        self.assertReplied(self.bot, u'''\
You can control me by sending these commands:

/shoot - method None breaks for sure
''')

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
