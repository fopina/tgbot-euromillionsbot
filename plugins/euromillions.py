# coding=utf-8
from tgbot.pluginbase import TGPluginBase, TGCommandBase
from tgbot.tgbot import ChatAction
import requests


class EuromillionsPlugin(TGPluginBase):
    def list_commands(self):
        return (
            TGCommandBase('last', self.last, 'Last Euromillions result'),
            TGCommandBase('alertson', self.alertson, '', printable=False),
            TGCommandBase('alertsoff', self.alertsoff, '', printable=False),
        )

    def last(self, message, text):
        return self._last(message.chat.id)

    def _last(self, chat):
        self.bot.send_chat_action(chat, ChatAction.TEXT)
        d = self.read_data('results', 'latest')
        if d:
            return self.bot.send_message(
                chat,
                u'''\
Latest results _%s_
\U0001F3BE
*%s*
\U00002B50
*%s*''' % (d['date'], d['numbers'], d['stars']),
                parse_mode='Markdown'
            ).wait()

    def alertson(self, message, text):
        self.save_data(message.chat.id, obj=True)
        self.bot.send_message(message.chat.id, 'Alerts enabled')

    def alertsoff(self, message, text):
        self.save_data(message.chat.id, obj=False)
        self.bot.send_message(message.chat.id, 'Alerts disabled')

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
        old = self.read_data('results', 'latest')
        self.save_data('results', key2='latest', obj=d)

        if old == d:
            return

        for chat in self.iter_data_keys():
            if chat == 'results':
                continue
            if self.read_data(chat):
                print "Sending message to %s" % chat
                time_start = time.time()
                r = self._last(chat)
                time_taken = time.time() - time_start
                if time_taken < 0.5:  # pragma: no cover
                    time.sleep(0.5 - time_taken)
