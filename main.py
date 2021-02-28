
import elicznik
import yaml
#from astral import LocationInfo, sun
#import datetime
from datetime import datetime, timedelta, date
from configparser import ConfigParser
import logging
import time
from pprint import pprint

from pvoutput import PVOutput

FORMAT = '[%(asctime)-15s] [%(levelname)s] [%(filename)s %(levelno)s line] %(message)s'

_LOG = logging.getLogger('pvoutput')
logging.basicConfig(format=FORMAT)
_LOG.setLevel(logging.DEBUG)

def test():
    from datetime import date
    import pandas as pd
    import matplotlib.dates as mdates
    from pvoutput import PVOutput

    API_KEY = "44fbec43fa3cd73bb4c803451b2010c907a06b97"
    SYSTEM_ID = 81585

    pv = PVOutput( API_KEY, SYSTEM_ID)

class pvOutput(PVOutput):

    def add_batch_status(self,batch_data=None, net_data=False):
        """
        https://pvoutput.org/help.html#api-addbatchstatus The Add Batch Status service adds up to 30 statuses in a single
        request :param profile_data: :param key: :param sid: :param net_data: batch net data with the n=1 flag. :return:
        DEBUG:urllib3.connectionpool:Starting new HTTP connection (1): pvoutput.org:80
        DEBUG:urllib3.connectionpool:http://pvoutput.org:80 "POST /service/r2/addbatchstatus.jsp HTTP/1.1" 200 305 INFO:
        'http://pvoutput.org/service/r2/addbatchstatus.jsp' 200 POST OK: '20210217,22:30,1;20210217,22:35,....,23:55,1'
        INFO: 'http://pvoutput.org/service/r2/addbatchstatus.jsp' 200 POST OK
        """


        batch_max = 90

        url = 'http://pvoutput.org/service/r2/addbatchstatus.jsp'

        # REST API post
        i = 0
        while i < len(batch_data):
            # batch max
            this_batch = batch_data[i:(i + batch_max)]
            i += batch_max
            # batch:
            batch_payload = {
                'data': ';'.join(this_batch),  # batch readings
                # 'c1':1, # cumulative
            }
            if net_data:
                batch_payload["n"] = '1'
            _LOG.debug("batch_payload: " + str(batch_payload))
            self._api_query(service='addbatchstatus', api_params=batch_payload)
            # Send request
            time.sleep(3)

        return True
class mainClass:
    def __init__(self,config = None):
        cp = ConfigParser()
        if config is not None:
            cp.read(config)

        now = datetime.today()
        _LOG.debug("Now: " + now.strftime("%Y%m%d"))
        yesterday = now - timedelta(days=1)
        _LOG.debug("Yesterday: " + yesterday.strftime("%Y%m%d"))

        API_KEY = ""
        SYSTEM_ID = 

        pv = pvOutput(API_KEY, SYSTEM_ID)
        #print(pv.rate_limit_info())
        #pv_status = pv.get_status(SYSTEM_ID, date=yesterday)
        #pv_status.to_excel("output.xlsx")
       # print(pv.rate_limit_info())
        elicznik_data = elicznik.elicznik(yesterday,username = cp['elicznik'].get('username'),password=cp['elicznik'].get('password'),meter_id=cp['elicznik'].get('meter_id'))
        #pprint(elicznik_data)
        #pv  = pv_status.to_dict()
        #pprint(pv)
        #print (pv_status.keys() )
        net_data_to_send = []
        for id in sorted(elicznik_data):
            #record = pv_status.loc[id]
            rec = []
            d = yesterday.strftime("%Y%m%d")
            t = f"{id}:00"
            single_net_data_to_send = [d,
                                       t,
                                       "-1",
                                       f"{elicznik_data[id]['export_power']}",  #Power Exported
                                       "-1",
                                       f"{elicznik_data[id]['used_power']}" #Power Imported used_power
                                       #"0"
                                       ]
            #record = record.to_dict()
            net_data_to_send.append(','.join(single_net_data_to_send))
            #pprint(id)
        pv.add_batch_status(net_data_to_send,net_data=True)
        #   print(pv[id])

def main():
    pv = mainClass('config.ini')

if __name__ == '__main__':
    #test()
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
