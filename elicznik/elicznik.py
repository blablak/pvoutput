# -*- coding: utf-8 -*-
"""Python """

import requests
import logging
import ssl
from urllib3 import poolmanager
from requests.adapters import HTTPAdapter
import pprint

FORMAT = '[%(asctime)-15s] [%(levelname)s] [%(filename)s %(levelno)s line] %(message)s'
logger = logging.getLogger(__file__)
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)



def elicznik(day, username, password, meter_id):
    payload = {
        'username': username,
        'password': password,
        'service': 'https://elicznik.tauron-dystrybucja.pl'
    }

    url = 'https://logowanie.tauron-dystrybucja.pl/login'
    charturl = 'https://elicznik.tauron-dystrybucja.pl/index/charts'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0'}

    class TLSAdapter(HTTPAdapter):
        def init_poolmanager(self, connections, maxsize, block=False):
            """Create and initialize the urllib3 PoolManager."""
            ctx = ssl.create_default_context()
            ctx.set_ciphers('DEFAULT@SECLEVEL=1')
            self.poolmanager = poolmanager.PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                ssl_version=ssl.PROTOCOL_TLS,
                ssl_context=ctx)

    session = requests.session()
    session.mount('https://', TLSAdapter())

    # should be call twice to correctly display
    p = session.request("POST", url, data=payload, headers=headers)
    p = session.request("POST", url, data=payload, headers=headers)

    chart = {
        # change timedelta to get data from another days (1 for yesterday)
        "dane[chartDay]": day.strftime('%d.%m.%Y'),
        "dane[checkWeather]":1,
        # "dane[chartDay]": "06.02.2021",
        "dane[paramType]": "day",
        "dane[smartNr]": meter_id,
        # comment if don't want generated energy data in JSON output:
        "dane[checkOZE]": "on"
    }

    logger.debug(chart)
    response = session.request("POST", charturl, data=chart, headers=headers)
    # pprint.pprint(response.text)
    json_data = response.json()
    #pprint.pprint(json_data)
    # show power usage per hours
    return_value = {}
    logger.debug(json_data["dane"]["chart"])
    logger.debug(json_data["dane"]["OZE"])
    for hour in json_data["dane"]["chart"]:
        logger.debug(f'Hour: {hour:0>2} - {json_data["dane"]["chart"][hour]["EC"]} kWh |  '
                   f'{json_data["dane"]["OZE"][hour]["EC"]} kWh')
        return_value[f'{hour:0>2}'] = {"used_power": int(float(json_data["dane"]["chart"][hour]["EC"]) * 1000),
                                       "export_power": int(float(json_data["dane"]["OZE"][hour]["EC"]) * 1000),
                                       "Zone":json_data["dane"]["OZE"][hour]["Zone"],
                                       "ZoneName":json_data["dane"]["OZE"][hour]["ZoneName"],
                                       }

    for weather in json_data["dane"]['weather']:
        hour = weather['Godzina']
        if hour == '0': continue
        return_value[f'{hour:0>2}']['TemperatureAir'] = weather['TemperatureAir']
        return_value[f'{hour:0>2}']['Cloudiness'] = weather['Cloudiness']
        return_value[f'{hour:0>2}']['Windspeed'] = weather['Windspeed']
        if hour == '23':
            hour = 24
            return_value[f'{hour:0>2}']['TemperatureAir'] = weather['TemperatureAir']
            return_value[f'{hour:0>2}']['Cloudiness'] = weather['Cloudiness']
            return_value[f'{hour:0>2}']['Windspeed'] = weather['Windspeed']

    pprint.pprint(return_value)

    return return_value

