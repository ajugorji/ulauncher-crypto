# -*- coding: utf-8 -*-

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction

import os
import json
import urllib2
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
time = datetime.now()
last_currency = ''
cached_rate = None


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


class CryptoPriceExtension(Extension):

    def __init__(self):
        super(CryptoPriceExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        global time
        global cached_rate
        global last_currency
        # Results to display
        items = []
        # Preferred currency
        symbol = ('USD', '$')
        # Current script directory
        script_dir = os.path.dirname(os.path.realpath(__file__))

        # set defaults and override if we get a matching query
        amount = 1
        currency = 'btc'
        bad_call = False

        # parse query
        query = event.get_argument() if event.get_argument() else None
        if query:
            args = query.split()
            if len(args) > 0:
                currency = args[0]
            if len(args) > 1 and is_number(args[1]):
                amount = float(args[1])

        api_info = ('Cryptocompare', 'https://min-api.cryptocompare.com/data/price?fsym={0}&tsyms={1}'.format(currency.upper(), symbol[0]))
        try:
            # check ticker validity, new currency, cache timeout
            delta = datetime.now() - time
            if currency != last_currency or delta.total_seconds() > 60:
                # formulate request
                req = urllib2.Request(api_info[1], headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'})
                res = urllib2.urlopen(req).read()
                data = json.loads(res)
                # successful api call
                if "USD" in data:
                    rate = float(data["USD"])
                    cached_rate = rate
                # unsuccessful - try again
                else:
                    bad_call = True
                # update time and last_currency
                last_currency = currency
                time = datetime.now()
            else:
                rate = cached_rate
                if not cached_rate:
                    return

            if bad_call:
                items.append(ExtensionResultItem(icon='images/icon.png',
                                                 name='Ticker {0} not found.'.format(currency.upper()),
                                                 description='Sorry!'
                                                 ))
            else:
                icon_path = 'images/icons/{0}.png'.format(currency.lower())
                if not os.path.isfile(os.path.join(script_dir, icon_path)):
                    icon_path = 'images/icon.png'
                items.append(ExtensionResultItem(icon=icon_path,
                                                 name='{}{:.3f}'.format(symbol[1], rate*amount),
                                                 description='{}'.format(api_info[0].format(currency, symbol[0])),
                                                 on_enter=CopyToClipboardAction(str(rate*amount))))

        except Exception as e:
            logger.debug('Exception occurred: {}'.format(str(e)))

        return RenderResultListAction(items)


if __name__ == '__main__':
    CryptoPriceExtension().run()
