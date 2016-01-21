# coding=utf-8
from tgbot.pluginbase import TGPluginBase, TGCommandBase
from tgbot.tgbot import ChatAction, ReplyKeyboardMarkup, ForceReply, ReplyKeyboardHide, Error, InlineQueryResultArticle
import requests
import random
from datetime import datetime


class EuromillionsPlugin(TGPluginBase):
    DATE_MASK = '%Y-%M-%d'
    INLINE_CACHE_TIME = 300

    def list_commands(self):
        return (
            TGCommandBase('last', self.last, 'last Euromillions results'),
            TGCommandBase('alerts', self.alerts, 'receive an alert when new results are announced'),
            TGCommandBase('results', self.results, 'Euromillions results for a specific date'),
            TGCommandBase('random', self.random, 'generate a random key'),
            TGCommandBase('alertson', self.alertson, '', printable=False),
            TGCommandBase('alertsoff', self.alertsoff, '', printable=False),
        )

    def build_menu(self, chat):
        if chat.type == 'private':
            return ReplyKeyboardMarkup.create(
                keyboard=[
                    ['Last Results'],
                    ['Previous Results'],
                    ['Random Key'],
                    ['Disable Alerts' if self.read_data(chat.id) else 'Enable Alerts'],
                ],
                resize_keyboard=True,
            )

    def chat(self, message, text):
        if (
            message.chat.type == 'group' and
            (
                message.group_chat_created or
                (
                    message.new_chat_participant and message.new_chat_participant.username == self.bot.username
                )
            )
        ):
            self.bot.send_message(
                message.chat.id,
                '''\
Thanks for inviting me over!

Use /help to find out what I can do.'''
            )
            return

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
            elif text == 'Random Key':
                self.random(message, text)
            elif text == 'Enable Alerts':
                self.alertson(message, text)
            elif text == 'Disable Alerts':
                self.alertsoff(message, text)
            elif text:
                res = 'Please *use* the format `YEAR-MM-DD`'
                try:
                    res = self._results(text)
                except:
                    pass
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

        try:
            self.bot.send_message(
                message.chat.id,
                self._results(text),
                parse_mode='Markdown'
            )
        except:
            m = self.bot.send_message(
                message.chat.id,
                'Please *use* the format `YEAR-MM-DD`',
                reply_to_message_id=message.message_id,
                reply_markup=ForceReply.create(selective=True),
                parse_mode='Markdown'
            ).wait()
            self.need_reply(self.results, message, out_message=m, selective=True)

    def _results(self, entry='latest'):
        if entry != 'latest':
            # let the parsing exception go...
            dt = datetime.strptime(entry, self.DATE_MASK)
            if dt > datetime.utcnow():
                return 'I cannot foretell the future (at the moment?) but give /random a try...'

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

    def random(self, message, text):
        numbers = map(str, random.sample(range(1, 51), 5))
        stars = map(str, random.sample(range(1, 12), 2))

        self.bot.send_message(
            message.chat.id,
            u'''\
Here's a random key for you!
\U0001F3BE
*%s*
\U00002B50
*%s*''' % (' '.join(numbers), ' '.join(stars)),
            parse_mode='Markdown'
        )

    def inline_query(self, inline_query):
        if not inline_query.query:
            results = [InlineQueryResultArticle('latest', 'Latest (%s)' % self.read_data('results', 'latest')['date'], self._results(), parse_mode='Markdown')]
            self.bot.answer_inline_query(inline_query.id, results, cache_time=self.INLINE_CACHE_TIME)
        else:
            results = []
            try:
                o = int(inline_query.offset)
            except:
                o = 0
            skip = o

            for x in self._lookup_results(inline_query.query):
                if skip:
                    skip -= 1
                    continue
                results.append(InlineQueryResultArticle(
                    x,
                    x % self.read_data('results', x),
                    self._results(x),
                    parse_mode='Markdown')
                )
                if len(results) >= 20:
                    break

            self.bot.answer_inline_query(
                inline_query.id,
                results,
                cache_time=self.INLINE_CACHE_TIME,
                next_offset=None if len(results) < 20 else o + 20
            )

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
        gmtime = time.gmtime()
        if gmtime.tm_wday not in [1, 4] or gmtime.tm_hour < 20:
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

    def _lookup_results(self, prefix):
        # re-implemented (instead of using iter_data_key_keys) for performance
        for d in self.bot.models.PluginData.select(self.bot.models.PluginData.k2).where(
            self.bot.models.PluginData.name == self.key_name,
            self.bot.models.PluginData.k1 == 'results',
            self.bot.models.PluginData.k2.startswith(prefix),
            self.bot.models.PluginData.data != None,  # noqa: do not change to "is not", peewee operator
        ).order_by(-self.bot.models.PluginData.k2):
            yield d.k2
