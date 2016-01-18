# coding=utf-8
from tgbot.pluginbase import TGPluginBase, TGCommandBase
from tgbot.tgbot import ChatAction
import requests


class EuromillionsPlugin(TGPluginBase):
    def list_commands(self):
        return (
            TGCommandBase('last', self.last, 'Last Euromillions result'),
        )

    def last(self, message, text):
        self.bot.send_chat_action(message.chat.id, ChatAction.TEXT)
        self.bot.send_message(message.chat.id, 'test')

    def cron_go(self, action, *args):
        if action == 'millions.populate':
            return self.cron_populate()
        elif action == 'millions.update':
            return self.cron_update()

    def cron_populate(self):
        import time
        for year in xrange(2004, time.gmtime().tm_year + 1):
            print 'Year:', year
            r = requests.get('https://nunofcguerreiro.com/api-euromillions-json', params={'result': year})
            for d in r.json()['drawns']:
                dt = d['date']
                del(d['date'])
                self.save_data('results', key2=dt, obj=d)
        r = requests.get('https://nunofcguerreiro.com/api-euromillions-json')
        d = r.json()['drawns'][0]
        self.save_data('results', 'latest', obj=d)

    def cron_update(self):
        import time

        # do nothing if not Tuesday nor Friday
        wday = time.gmtime().tm_wday
        if wday not in [1, 4]:
            return

        r = requests.get('https://nunofcguerreiro.com/api-euromillions-json')
        d = r.json()['drawns'][0]
        self.save_data('results', 'latest', obj=d)
