# coding=utf-8
from tgbot.pluginbase import TGPluginBase, TGCommandBase
from tgbot.tgbot import ChatAction, ReplyKeyboardMarkup
import requests


class EuromillionsPlugin(TGPluginBase):
    def list_commands(self):
        return (
            TGCommandBase('last', self.last, 'Last Euromillions result'),
            TGCommandBase('alerts', self.alerts, 'Result alerts'),
            TGCommandBase('alertson', self.alertson, '', printable=False),
            TGCommandBase('alertsoff', self.alertsoff, '', printable=False),
        )

    def build_menu(self, chat):
        if chat.type == 'private':
            return ReplyKeyboardMarkup.create(
                keyboard=[
                    ['Last Results'],
                    ['Disable Alerts' if self.read_data(chat.id) else 'Enable Alerts'],
                ],
                resize_keyboard=True,
            )
        else:
            return None

    def chat(self, message, text):
        if message.chat.type != 'private':
            return
        if text == 'Last Results':
            self._last(message.chat)
        elif text == 'Enable Alerts':
            self.alertson(message, text)
        elif text == 'Disable Alerts':
            self.alertsoff(message, text)

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

    def alerts(self, message, text):
        alerts = self.read_data(message.chat.id)
        self.bot.send_message(
            message.chat.id,
            'Alerts enabled, use /alertsoff to disable them' if alerts else 'Alerts disabled, use /alertson to enable them'
        )

    def alertson(self, message, text):
        self.save_data(message.chat.id, obj=True)
        self.bot.send_message(message.chat.id, 'Alerts enabled', reply_markup=self.build_menu(message.chat))

    def alertsoff(self, message, text):
        self.save_data(message.chat.id, obj=False)
        self.bot.send_message(message.chat.id, 'Alerts disabled', reply_markup=self.build_menu(message.chat))

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

        if old == d:
            return

        self.save_data('results', key2='latest', obj=d)

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
