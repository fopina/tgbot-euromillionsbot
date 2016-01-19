#!/usr/bin/env python
# coding=utf-8

import tgbot
from plugins import euromillions, intro
import argparse
from requests.packages import urllib3
urllib3.disable_warnings()


def setup(db_url=None, token=None):
    mp = euromillions.EuromillionsPlugin()
    tg = tgbot.TGBot(
        token,
        plugins=[
            mp,
            intro.IntroPlugin(
                intro_text='''\
_Do not forget to rate me!_
https://telegram.me/storebot?start=euromillionsbot
            ''',
                markdown=True,
                start_menu_builder=mp.build_menu,
            ),
        ],
        no_command=mp,
        db_url=db_url,
    )
    return tg


def openshift_app():
    import os

    bot = setup(
        db_url='postgresql://%s:%s/%s' % (
            os.environ['OPENSHIFT_POSTGRESQL_DB_HOST'],
            os.environ['OPENSHIFT_POSTGRESQL_DB_PORT'],
            os.environ['PGDATABASE']
        ),
        token=os.environ['TGTOKEN']
    )
    bot.set_webhook('https://%s/update/%s' % (os.environ['OPENSHIFT_APP_DNS'], bot.token))

    from tgbot.webserver import wsgi_app
    return wsgi_app([bot])


def main():
    parser = build_parser()
    args = parser.parse_args()

    tg = setup(db_url=args.db_url, token=args.token)

    if args.list:
        tg.print_commands()
        return

    if args.create_db:
        tg.setup_db()
        print 'DB created'
        return

    if args.cron is not None:
        for p in tg._plugins:
            if hasattr(p, 'cron_go'):
                p.cron_go(*args.cron)
        return

    if args.webhook is None:
        tg.run(polling_time=args.polling)
    else:
        tg.run_web(args.webhook[0], host='0.0.0.0', port=int(args.webhook[1]))


def build_parser():
    parser = argparse.ArgumentParser(description='Run EuromillionsBot')

    parser.add_argument('--polling', '-p', dest='polling', type=float, default=2,
                        help='interval (in seconds) to check for message updates')
    parser.add_argument('--db_url', '-d', dest='db_url', default='sqlite:///millionsbot.sqlite3',
                        help='URL for database (default is sqlite:///millionsbot.sqlite3)')
    parser.add_argument('--list', '-l', dest='list', action='store_const',
                        const=True, default=False,
                        help='plugin method to be used for non-command messages (ex: plugins.simsimi.SimsimiPlugin.simsimi)')
    parser.add_argument('--webhook', '-w', dest='webhook', nargs=2, metavar=('hook_url', 'port'),
                        help='use webhooks (instead of polling) - requires bottle')
    parser.add_argument('--create_db', dest='create_db', action='store_const',
                        const=True, default=False,
                        help='setup database')
    parser.add_argument('--token', '-t', dest='token',
                        help='token provided by @BotFather')
    parser.add_argument('--cron', dest='cron', nargs=2, metavar=('action', 'param'),
                        help='trigger cron ACTION with PARAM parameter and quit')

    return parser


if __name__ == '__main__':
    main()
