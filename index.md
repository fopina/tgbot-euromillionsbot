---
layout: index
---

This is a friendly Telegram bot that lets you check Euromillions results and receive alerts when new ones are announced, feel free to contact [@EuromillionsBot](http://telegram.me/euromillionsbot).

[![Build Status](https://travis-ci.org/fopina/tgbot-euromillionsbot.svg?branch=master)](https://travis-ci.org/fopina/tgbot-euromillionsbot) [![Coverage Status](https://coveralls.io/repos/fopina/tgbot-euromillionsbot/badge.svg?branch=master&service=github)](https://coveralls.io/github/fopina/tgbot-euromillionsbot?branch=master)

EuromillionsBot was a developed using [TGBotPlug](http://fopina.github.io/tgbotplug).

This repository is ready for openshift (as the bot is running there), so you can easily host your own:

* Register in [OpenShift](https://www.openshift.com)  
* Install [rhc](https://developers.openshift.com/en/managing-client-tools.html), the command line tool  
* Run `rhc setup` to configure it  
* Talk to [@BotFather](http://telegram.me/botfather) to register your bot  
* And finally run these commands (replacing `<YOUR_BOT_TOKEN>` with the token provided by @BotFather)

    ```
    rhc app-create millionsbot python-2.7 postgresql-9.2 cron-1.4 --from-code https://github.com/fopina/tgbot-euromillionsbot/
    cd millionsbot
    rhc env-set TGTOKEN=<YOUR_BOT_TOKEN>
    rhc ssh -- 'app-root/repo/millionsbot.py --db_url="postgresql://$OPENSHIFT_POSTGRESQL_DB_HOST:$OPENSHIFT_POSTGRESQL_DB_PORT/$PGDATABASE" --create_db'
    rhc app-restart
    ```

Have fun!
