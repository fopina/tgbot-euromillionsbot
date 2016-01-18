# coding=utf-8
from tgbot.pluginbase import TGPluginBase, TGCommandBase


class IntroPlugin(TGPluginBase):
    def __init__(self, intro_text='Hello!', markdown=False):
        super(IntroPlugin, self).__init__()
        self._text = intro_text
        self._use_markdown = markdown

    def list_commands(self):
        return (
            TGCommandBase('start', self.start, 'Introduction', printable=False),
        )

    def start(self, message, text):
        self.bot.send_message(
            message.chat.id,
            self._text,
            parse_mode='Markdown' if self._use_markdown else None
        )
