# coding=utf-8
from tgbot.pluginbase import TGPluginBase, TGCommandBase
from tgbot.tgbot import ChatAction


class EuromillionsPlugin(TGPluginBase):
    def list_commands(self):
        return (
            TGCommandBase('last', self.last, 'Last Euromillions result'),
        )

    def last(self, message, text):
        self.bot.send_chat_action(message.chat.id, ChatAction.TEXT)
        self.bot.send_message(message.chat.id, 'test')
