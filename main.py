
import elicznik
import yaml
#from astral import LocationInfo, sun
#import datetime
from datetime import datetime, timedelta, date
from configparser import ConfigParser
import logging


FORMAT = '[%(asctime)-15s] [%(levelname)s] [%(filename)s %(levelno)s line] %(message)s'
logger = logging.getLogger(__file__)
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)

class pvOutputOrg:
    def __init__(self,config = None):
        cp = ConfigParser()
        if config is not None:
            cp.read(config)

        now = datetime.today()
        logger.debug("Now: " + now.strftime("%Y%m%d"))
        yesterday = now - timedelta(days=1)
        logger.debug("Yesterday: " + yesterday.strftime("%Y%m%d"))

        elicznik.elicznik(yesterday,username = cp['elicznik'].get('username'),password=cp['elicznik'].get('password'),meter_id=cp['elicznik'].get('meter_id'))

def main():
    pv = pvOutputOrg('config.ini')

if __name__ == '__main__':
   main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
