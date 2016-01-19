# coding=utf-8
from tgbot.pluginbase import TGPluginBase, TGCommandBase


class IntroPlugin(TGPluginBase):
    def __init__(self, intro_text='Hello!', markdown=False, start_menu_builder=None):
        super(IntroPlugin, self).__init__()
        self._text = intro_text
        self._use_markdown = markdown
        self._start_menu_builder = start_menu_builder

    def list_commands(self):
        return (
            TGCommandBase('start', self.start, 'introduction', printable=False),
            TGCommandBase('help', self.help, 'help', printable=False),
        )

    def help(self, message, text):
        msg = 'You can control me by sending these commands:\n\n'

        cmds = self.bot.list_commands()
        for ck in cmds:
            if ck.printable:
                msg += '/%s\n' % ck

        self.bot.send_message(message.chat.id, msg)

    def start(self, message, text):
        keyb = None

        if self._start_menu_builder:
            keyb = self._start_menu_builder(message.chat)

        self.bot.send_message(
            message.chat.id,
            self._text,
            parse_mode='Markdown' if self._use_markdown else None,
            reply_markup=keyb
        )
