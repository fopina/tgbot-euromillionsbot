# coding=utf-8
from tgbot.pluginbase import TGPluginBase, TGCommandBase
from tgbot.tgbot import ChatAction, ReplyKeyboardMarkup, ForceReply, ReplyKeyboardHide, Error
import requests
import re


class EuromillionsPlugin(TGPluginBase):
    DATE_RE = re.compile(r'\d{4}-\d\d-\d\d')

    def list_commands(self):
        return (
            TGCommandBase('last', self.last, 'Last Euromillions results'),
            TGCommandBase('alerts', self.alerts, 'Receive an alert when new results are announced'),
            TGCommandBase('results', self.results, 'Euromillions results for specific date'),
            TGCommandBase('alertson', self.alertson, '', printable=False),
            TGCommandBase('alertsoff', self.alertsoff, '', printable=False),
        )

    def build_menu(self, chat):
        if chat.type == 'private':
            return ReplyKeyboardMarkup.create(
                keyboard=[
                    ['Last Results'],
                    ['Previous Results'],
                    ['Disable Alerts' if self.read_data(chat.id) else 'Enable Alerts'],
                ],
                resize_keyboard=True,
            )

    def chat(self, message, text):
        if message.chat.type == 'private':
            if text == 'Last Results':
                self._last(message.chat)
            elif text == 'Previous Results':
                self.bot.send_message(
                    message.chat.id,
                    'Please enter the date in the format `YEAR-MM-DD`',
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardHide.create()
                )
            elif text == 'Enable Alerts':
                self.alertson(message, text)
            elif text == 'Disable Alerts':
                self.alertsoff(message, text)
            elif text:
                res = 'Please *use* the format `YEAR-MM-DD`'
                if self.DATE_RE.match(text):
                    res = self._results(text)
                self.bot.send_message(
                    message.chat.id,
                    res,
                    parse_mode='Markdown',
                    reply_markup=self.build_menu(message.chat)
                )

    def results(self, message, text):
        self.bot.send_chat_action(message.chat.id, ChatAction.TEXT)
        if not text:
            m = self.bot.send_message(
                message.chat.id,
                'For which date?\nPlease use the format `YEAR-MM-DD`',
                reply_to_message_id=message.message_id,
                reply_markup=ForceReply.create(selective=True),
                parse_mode='Markdown'
            ).wait()
            self.need_reply(self.results, message, out_message=m, selective=True)
            return

        if not self.DATE_RE.match(text):
            m = self.bot.send_message(
                message.chat.id,
                'Please *use* the format `YEAR-MM-DD`',
                reply_to_message_id=message.message_id,
                reply_markup=ForceReply.create(selective=True),
                parse_mode='Markdown'
            ).wait()
            self.need_reply(self.results, message, out_message=m, selective=True)
            return

        self.bot.send_message(
            message.chat.id,
            self._results(text),
            parse_mode='Markdown'
        ).wait()

    def _results(self, entry='latest'):
        d = self.read_data('results', entry)

        if not d:
            return 'No results for `%s`...' % entry

        dt = entry
        if dt == 'latest':
            dt = d['date']

        return u'''\
%sResults for _%s_
\U0001F3BE
*%s*
\U00002B50
*%s*''' % (
            'Latest ' if entry == 'latest' else '',
            dt,
            d['numbers'],
            d['stars']
        )

    def last(self, message, text):
        return self._last(message.chat.id)

    def _last(self, chat):
        self.bot.send_chat_action(chat, ChatAction.TEXT)
        return self.bot.send_message(
            chat,
            self._results(),
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
                if isinstance(r, Error):  # pragma: no cover
                    if r.error_code == 403:
                        print '%s blocked bot' % chat
                        self.save_data(chat, obj=False)
                    else:
                        print 'Error for', chat, ': ', r
                time_taken = time.time() - time_start
                if time_taken < 0.5:  # pragma: no cover
                    time.sleep(0.5 - time_taken)
