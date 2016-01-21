# coding=utf-8
from tgbot import plugintest, pluginbase
from tgbot.botapi import ReplyKeyboardMarkup
from plugins.intro import IntroPlugin


class PluginTest(plugintest.PluginTestCase):
    def setUp(self):
        self.bot = self.fake_bot('', plugins=[IntroPlugin()])

    def test_start_hello(self):
        self.receive_message('/start')
        self.assertReplied('Hello!')

    def test_start_world_with_menu(self):
        def menu(chat):
            return ReplyKeyboardMarkup.create(keyboard=[['One']])

        self.bot = self.fake_bot(
            '',
            plugins=[IntroPlugin(intro_text='World!', start_menu_builder=menu)]
        )
        self.receive_message('/start')
        reply = self.pop_reply()
        self.assertEqual(reply[1]['text'], 'World!')
        self.assertEqual(reply[1]['reply_markup'], {'keyboard': [['One']]})

    def test_help(self):
        class TestPlugin(pluginbase.TGPluginBase):
            def list_commands(self):
                return (
                    pluginbase.TGCommandBase('shoot', None, 'method None breaks for sure'),
                )

        self.bot = self.fake_bot('', plugins=[IntroPlugin(), TestPlugin()])
        self.receive_message('/help')
        self.assertReplied(u'''\
You can control me by sending these commands:

/shoot - method None breaks for sure
''')
