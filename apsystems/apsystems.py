from bs4 import BeautifulSoup
from urllib import request, error
from pvoutput import PVOutput
from time import sleep
from astral import LocationInfo, sun
import datetime
from datetime import datetime, timedelta, date
from configparser import ConfigParser
import logging
import requests
import re
import json
from pprint import pprint
import pandas as pd
import time

FORMAT = '[%(asctime)-15s] [%(levelname)s] [%(filename)s %(levelno)s line] %(message)s'

_LOG = logging.getLogger('apsystems')
logging.basicConfig(format=FORMAT)
_LOG.setLevel(logging.DEBUG)



def timing(function):
    def wrap(*args, **kwargs):
        start_time = time.time()
        result = function(*args, **kwargs)
        end_time  = time.time()
        duration = (end_time- start_time)*1000.0
        f_name = function.__name__
        _LOG.info("{} took {:.3f} ms".format(f_name, duration))

        return result
    return wrap

def download(url):
    try:
        page = request.urlopen(url).read()
        return page
    except:
        return None


def download_retry(url):
    retries = 5
    while retries > 0:
        _LOG.debug(f"{url} {retries}")
        page = download(url)
        if page is None:
            retries -= 1
            sleep(10)
        else:
            return page
class apSystemsApi_old():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    apsystems_url = 'http://api.apsystemsema.com:8073/apsema/v1/ecu/getPowerInfo'

    ecu_id = '215000007344'
    def __init__(self,config=None):

        self.ecuip = cp["ecu"].get("ecuip") or "10.1.1.199"
        '''

        '''
        pass
    @timing
    def get_data(self, time_stamp: datetime = datetime.today()) -> pd.DataFrame:



        data = {
          'ecuId': self.ecu_id,
          'filter': 'power',
          'date': time_stamp.strftime("%Y%m%d")
        }

        response = requests.post(self.apsystems_url, headers=self.headers, data=data)


        if response.status_code != 200:
            try:
                response.raise_for_status()
            except Exception as e:
                msg = (
                    'Bad status code! Response content = {}. Exception = {}'
                        .format(response.content, e))
                _LOG.exception(msg)
                raise e.__class__(msg)
        ans = response.json()
        #ans['data']['power'] = json.loads(ans['data']['power'])
        power_data = json.loads(ans['data']['power'])
        time_data  = json.loads(ans['data']['time'])
        energy     = 0
        ans = {}
        time_start_s = 0
        for i in range(len(time_data)):
            power = int(power_data[i])
            time_d = time_data[i]
            time_actual = pd.Timestamp(time_stamp.strftime("%Y-%m-%d") + " " + time_d)


            time_pass = time_actual.timestamp() - time_start_s
            if time_start_s == 0:
                time_pass = 300
            time_start_s = time_actual.timestamp()
            energy += power*time_pass/3600
            ans[time_actual.round("5min")] = (power,energy)

        time_actual += pd.Timedelta(minutes=5)
        ans[time_actual.round("5min")] = (0, energy)
        #power = [ int (p) for p in json.loads(ans['data']['power'])]
        #time = [pd.Timestamp(time_stamp.strftime("%Y-%m-%d") +" "+ d ).round("5min") for d in json.loads(ans['data']['time'])]



        return ans



    @timing
    def get_data(self, time_stamp: datetime = datetime.today()) -> pd.DataFrame:

        data = {
            'ecuId': self.ecu_id,
            'filter': 'power',
            'date': time_stamp.strftime("%Y%m%d")
        }

        response = requests.post(self.apsystems_url, headers=self.headers, data=data)

        if response.status_code != 200:
            try:
                response.raise_for_status()
            except Exception as e:
                msg = (
                    'Bad status code! Response content = {}. Exception = {}'
                        .format(response.content, e))
                _LOG.exception(msg)
                raise e.__class__(msg)
        ans = response.json()
        # ans['data']['power'] = json.loads(ans['data']['power'])
        power_data = json.loads(ans['data']['power'])
        time_data = json.loads(ans['data']['time'])
        energy = 0
        ans = {}
        time_start_s = 0
        for i in range(len(time_data)):
            power = int(power_data[i])
            time_d = time_data[i]
            time_actual = pd.Timestamp(time_stamp.strftime("%Y-%m-%d") + " " + time_d)

            time_pass = time_actual.timestamp() - time_start_s
            if time_start_s == 0:
                time_pass = 300
            time_start_s = time_actual.timestamp()
            energy += power * time_pass / 3600
            ans[time_actual.round("5min")] = (power, energy)

        time_actual += pd.Timedelta(minutes=5)
        ans[time_actual.round("5min")] = (0, energy)
        # power = [ int (p) for p in json.loads(ans['data']['power'])]
        # time = [pd.Timestamp(time_stamp.strftime("%Y-%m-%d") +" "+ d ).round("5min") for d in json.loads(ans['data']['time'])]

        return ans


class apSystemsApi:
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    def __init__(self, ecuip = '10.1.1.199'):

        self.ecuip = ecuip
        self.url = f'http://{self.ecuip}/index.php/home'
        self.url_realtime = f'http://{self.ecuip}/index.php/realtimedata'
        self.url_power = f'http://{self.ecuip}/index.php/realtimedata/old_power_graph'
        self.bs = None
        self.ecudata = {}
        self.lastexportresult = None
        self.installpoint = LocationInfo("Glogoczow", "Poland", timezone= "Europe/Warsaw",
                                         latitude= 51.145811,
                                         longitude= 00.644786)
        self.get_data_now()


    def get_data_now(self):
        self.bs = BeautifulSoup(download_retry(self.url), 'html.parser')
        home_table = self.bs.find("table").find_all("tr")
        for row in home_table:
            value = row.find("td").text.strip()
            if value.endswith("kWh"):
                value = int(float(value[:-3]) * 1000)
            elif value.endswith("kW"):
                value = int(float(value[:-2]) * 1000)
            elif value.endswith("W"):
                value = int(value[:-1])
            elif value.endswith("Wh"):
                value = int(value[:-2])
            self.ecudata[row.find("th").text.replace(" ", "_").lower()] = value
        # {'ecu_id': '1111111', 'lifetime_generation': 11010, 'last_system_power': 15, 'generation_of_current_day': 8610, 'last_connection_to_website': '2020-01-15 18:50:17', 'number_of_inverters': '2', 'last_number_of_inverters_online': '2', 'current_software_version': 'C2.1', 'current_time_zone': 'Europe/Warsaw', 'ecu_eth0_mac_address': '10:97:1B:01:00:00', 'ecu_wlan0_mac_address': '10:12:48:76:56:A5'}

    def get_extended_data(self):
        html = b'<!DOCTYPE html>\r\n<html>\r\n  <head>\r\n    <meta charset="utf-8">\r\n    <!-- \xe5\x85\xbc\xe5\xae\xb9IE -->\r\n    <meta http-equiv="X-UA-Compatible" content="IE=edge">\r\n    <!-- \xe6\x94\xaf\xe6\x8c\x81\xe5\x9b\xbd\xe4\xba\xa7\xe6\xb5\x8f\xe8\xa7\x88\xe5\x99\xa8\xe9\xab\x98\xe9\x80\x9f\xe6\xa8\xa1\xe5\xbc\x8f -->\r\n    <meta name="renderer" content="webkit">\r\n    <!-- \xe5\x93\x8d\xe5\xba\x94\xe5\xbc\x8f\xe5\xb8\x83\xe5\xb1\x80 -->\r\n    <meta name="viewport" content="width=device-width, initial-scale=1">   \r\n\r\n    <title>Altenergy Power Control Software</title>\r\n    <link type="image/x-icon" href="http://10.1.1.199/resources/images/favicon.ico" rel="shortcut icon">    \r\n    <link href="http://10.1.1.199/resources/css/bootstrap.min.css" rel="stylesheet">\r\n    <link href="http://10.1.1.199/resources/css/ecu-style.css" rel="stylesheet">\r\n    <link href="http://10.1.1.199/resources/css/bootstrapValidator.css" rel="stylesheet">    \r\n    <!--[if lt IE 8]>\r\n      <link href="http://10.1.1.199/resources/css/bootstrap-ie7.css" rel="stylesheet">\r\n    <![endif]-->\r\n    \r\n    <script src="http://10.1.1.199/resources/js/jquery-1.8.2.min.js"></script>\r\n    <script src="http://10.1.1.199/resources/js/bootstrap.min.js"></script>\r\n    <script src="http://10.1.1.199/resources/js/bootstrapValidator.min.js"></script>    \r\n    <!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->\r\n    <!-- WARNING: Respond.js doesn"t work if you view the page via file:// -->\r\n    <!--[if lt IE 9]>\r\n      <script src="js/html5shiv.min.js"></script>\r\n      <script src="js/respond.min.js"></script>\r\n    <![endif]-->    \r\n  </head>\r\n\r\n  <body>\r\n    <!-- \xe9\xa1\xb6\xe9\x83\xa8\xe5\xaf\xbc\xe8\x88\xaa\xe6\xa0\x8f -->\r\n    <header>\r\n      <div class="navbar navbar-default navbar-top">\r\n        <div class="container">\r\n          <div class="navbar-header">\r\n            <button class="navbar-toggle" data-target="#navbar-header" data-toggle="collapse" type="button">\r\n              <span class="icon-bar"></span>\r\n              <span class="icon-bar"></span>\r\n              <span class="icon-bar"></span>\r\n            </button>\r\n            <a class="navbar-brand" href="http://www.altenergy-power.com">\r\n              <img src="http://10.1.1.199/resources/images/logo.png">\r\n            </a>\r\n          </div>\r\n          <div class="navbar-collapse collapse" id="navbar-header">\r\n            <ul class="nav navbar-nav navbar-title">\r\n              <li><a id="ecu_title">ENERGY COMMUNICATION UNIT</a></li>\r\n            </ul>\r\n            <ul class="nav navbar-nav navbar-right">\r\n              <a class="btn chlang" id="english" >English</a>|\r\n              <a class="btn chlang" id="chinese" >Chinese</a>\r\n            </ul>\r\n          </div>\r\n        </div>\r\n      </div>     \r\n    </header><!-- \xe8\x8f\x9c\xe5\x8d\x95\xe5\xaf\xbc\xe8\x88\xaa\xe6\xa0\x8f -->\r\n<nav>\r\n    <div class="navbar navbar-default navbar-menu">\r\n        <div class="container">\r\n                    <p class="navbar-menu-title">Real Time Data</p>     \r\n            <div class="navbar-header">            \r\n                <button class="navbar-toggle" data-target="#navbar-menu" data-toggle="collapse" type="button">\r\n                    <span class="icon-bar"></span>\r\n                    <span class="icon-bar"></span>\r\n                    <span class="icon-bar"></span>\r\n                    <span class="icon-bar"></span>                </button>\r\n            </div>\r\n            \r\n            <div class="navbar-collapse collapse" id="navbar-menu">\r\n                <ul class="nav navbar-nav ">\r\n                    <li><a href="http://10.1.1.199/index.php/home">Home</a></li>\r\n                    <li><a href="http://10.1.1.199/index.php/realtimedata" class="active">Real Time Data</a><span> </span></li>                    \r\n                    <li><a href="http://10.1.1.199/index.php/management">Administration</a><span> </span></li>\r\n                  \r\n                   \r\n                    <li><a href="http://10.1.1.199/index.php/meter/meter_power_graph">Advanced</a><span> </span></li>\r\n                   \r\n                </ul>\r\n            </div>\r\n        </div>\r\n    </div>\r\n</nav>\r\n        \r\n<section>\r\n    <div class="container container-main">\r\n        <!-- \xe4\xbe\xa7\xe8\xbe\xb9\xe5\xaf\xbc\xe8\x88\xaa\xe6\xa0\x8f -->\r\n        <aside class="col-md-3 col-md-push-9">\r\n            <div class="list-group">\r\n                  \r\n                              \t\t\t   \r\n                   <a href="http://10.1.1.199/index.php/realtimedata" class="list-group-item active">Real Time Data</a>\r\n                  \t   \r\n                  \r\n                              \t\t\t   \r\n                   <a href="http://10.1.1.199/index.php/realtimedata/power_graph" class="list-group-item ">Power</a>\r\n                  \t   \r\n                  \r\n                              \t\t\t   \r\n                   <a href="http://10.1.1.199/index.php/realtimedata/energy_graph" class="list-group-item ">Energy</a>\r\n                  \t   \r\n                                            </div>\r\n        </aside>\r\n        \r\n        <!-- \xe6\xad\xa3\xe6\x96\x87 -->\r\n        <article class="col-md-9 col-md-pull-3">\r\n            <div class="panel panel-default">\r\n                <div class="panel-heading">\r\n                    Real Time Data                                        <d class="btn-group pull-right visible-xs">\r\n                        <button type="button" class="btn btn-info btn-xs dropdown-toggle" data-toggle="dropdown">More <span class="caret"></span></button>\r\n                        <ul class="dropdown-menu" role="menu">\r\n                                   \r\n                                                                   <a href="http://10.1.1.199/index.php/realtimedata" class="list-group-item active">Real Time Data</a>\r\n                                \r\n                                   \r\n                                                                   <a href="http://10.1.1.199/index.php/realtimedata/power_graph" class="list-group-item ">Power</a>\r\n                                \r\n                                   \r\n                                                                   <a href="http://10.1.1.199/index.php/realtimedata/energy_graph" class="list-group-item ">Energy</a>\r\n                                \r\n                               \r\n                        </ul>\r\n                    </div>\r\n                                    </div>\r\n                                \r\n                <div class="panel-body">\r\n<!-- \xe8\xae\xbe\xe7\xbd\xae\xe7\xbb\x93\xe6\x9e\x9c\xe6\x98\xbe\xe7\xa4\xba\xe6\xa1\x86 -->\r\n<div class="alert alert-success" id="result"></div>\r\n<div class="btn-group col-sm-12" >\r\n\t\r\n\t\t\r\n\t\t\t\r\n\t\t\t<button title="Note: When working in service mode, the data refreshing will be quick, convinient for service at site, and the data will NOT be sent to EMA at this mode, after 30 minutes, service mode will quit automatically." class=" btn btn-primary" type="button" onclick="change_polling(1)" >Working In Normal Mode,Press To Enter Service Mode</button>\t\t\t\r\n\t\r\n</div>\r\n<br>\r\n<div id="note" hidden="hidden">Note: When working in service mode, the data refreshing will be quick, convinient for service at site, and the data will NOT be sent to EMA at this mode, after 30 minutes, service mode will quit automatically.</div>\r\n\r\n<div class="table-responsive">\r\n  <table class="table table-condensed table-bordered">\r\n    <thead>\r\n      <tr>\r\n        <th scope="col">Inverter ID</th>\r\n        <th scope="col">Current Power</th>\r\n        <th scope="col">Grid Frequency</th>\r\n        <th scope="col">Grid Voltage</th>\r\n        <th scope="col">Temperature</th>\r\n        <th scope="col">Reporting Time</th>\r\n      </tr>\r\n    </thead>\r\n    <tbody>\r\n        <div>\r\n            <tr class=\'active\'>\r\n        <td>801000040522-1 </td>\r\n        <td> 19 W </td>\r\n        <td rowspan=4 style=\'vertical-align: middle;\'> 50.0 Hz </td>\r\n        <td> 235 V </td>\r\n        <td rowspan=4 style=\'vertical-align: middle;\'> 11 &#176;C </td>\r\n        <td rowspan=4 style=\'vertical-align: middle;\'> 2021-03-06 16:34:07\n </td>\r\n      </tr>\r\n            <tr class=\'active\'>\r\n        <td>801000040522-2 </td>\r\n        <td> 18 W </td>\r\n        <td> 235 V </td>\r\n      </tr>\r\n            <tr class=\'active\'>\r\n        <td>801000040522-3 </td>\r\n        <td> 24 W </td>\r\n        <td> 235 V </td>\r\n      </tr>\r\n            <tr class=\'active\'>\r\n        <td>801000040522-4 </td>\r\n        <td> 21 W </td>\r\n        <td> 235 V </td>\r\n      </tr>\r\n          </div>\r\n        <div>\r\n            <tr >\r\n        <td>801000039665-1 </td>\r\n        <td> 19 W </td>\r\n        <td rowspan=4 style=\'vertical-align: middle;\'> 50.0 Hz </td>\r\n        <td> 236 V </td>\r\n        <td rowspan=4 style=\'vertical-align: middle;\'> 11 &#176;C </td>\r\n        <td rowspan=4 style=\'vertical-align: middle;\'> 2021-03-06 16:34:07\n </td>\r\n      </tr>\r\n            <tr >\r\n        <td>801000039665-2 </td>\r\n        <td> 18 W </td>\r\n        <td> 236 V </td>\r\n      </tr>\r\n            <tr >\r\n        <td>801000039665-3 </td>\r\n        <td> 25 W </td>\r\n        <td> 236 V </td>\r\n      </tr>\r\n            <tr >\r\n        <td>801000039665-4 </td>\r\n        <td> 22 W </td>\r\n        <td> 236 V </td>\r\n      </tr>\r\n          </div>\r\n        <div>\r\n            <tr class=\'active\'>\r\n        <td>801000040498-1 </td>\r\n        <td> 19 W </td>\r\n        <td rowspan=4 style=\'vertical-align: middle;\'> 50.0 Hz </td>\r\n        <td> 233 V </td>\r\n        <td rowspan=4 style=\'vertical-align: middle;\'> 10 &#176;C </td>\r\n        <td rowspan=4 style=\'vertical-align: middle;\'> 2021-03-06 16:34:07\n </td>\r\n      </tr>\r\n            <tr class=\'active\'>\r\n        <td>801000040498-2 </td>\r\n        <td> 16 W </td>\r\n        <td> 233 V </td>\r\n      </tr>\r\n            <tr class=\'active\'>\r\n        <td>801000040498-3 </td>\r\n        <td> 23 W </td>\r\n        <td> 233 V </td>\r\n      </tr>\r\n            <tr class=\'active\'>\r\n        <td>801000040498-4 </td>\r\n        <td> 26 W </td>\r\n        <td> 233 V </td>\r\n      </tr>\r\n          </div>\r\n        <div>\r\n            <tr >\r\n        <td>801000040199-1 </td>\r\n        <td> 18 W </td>\r\n        <td rowspan=4 style=\'vertical-align: middle;\'> 50.0 Hz </td>\r\n        <td> 235 V </td>\r\n        <td rowspan=4 style=\'vertical-align: middle;\'> 11 &#176;C </td>\r\n        <td rowspan=4 style=\'vertical-align: middle;\'> 2021-03-06 16:34:07\n </td>\r\n      </tr>\r\n            <tr >\r\n        <td>801000040199-2 </td>\r\n        <td> 19 W </td>\r\n        <td> 235 V </td>\r\n      </tr>\r\n            <tr >\r\n        <td>801000040199-3 </td>\r\n        <td> 21 W </td>\r\n        <td> 235 V </td>\r\n      </tr>\r\n            <tr >\r\n        <td>801000040199-4 </td>\r\n        <td> 25 W </td>\r\n        <td> 235 V </td>\r\n      </tr>\r\n          </div>\r\n        </tbody>\r\n  </table>\r\n</div>\r\n\r\n<script>\r\n \r\n\r\nfunction change_polling(polling_value){\r\n// \tif(document.getElementById("poll").checked)\r\n// \t{\r\n// \t\tconsole.log("checked");\r\n// \t\tpolling_value = 1;\r\n// \t}\r\n// \telse\r\n// \t{\r\n// \t\tconsole.log("no checked");\r\n// \t\tpolling_value = 0;\r\n// \t}\r\n    $.ajax({\r\n        url : "http://10.1.1.199/index.php/management/set_polling_conf",\r\n        type : "post",\r\n            dataType : "json",\r\n        data: "polling_value="+polling_value,\r\n        success : function(Results){\r\n              $("#result").text(Results.message);\r\n                if(Results.value == 0){\r\n                    $("#result").removeClass().addClass("alert alert-success");\r\n                    setTimeout(\'$("#result").fadeToggle("slow")\', 3000);\r\n                }\r\n                else{\r\n                    $("#result").removeClass().addClass("alert alert-warning");\r\n                }\r\n                $("#result").fadeToggle("slow");\r\n                window.scrollTo(0,0);//\xe9\xa1\xb5\xe9\x9d\xa2\xe7\xbd\xae\xe9\xa1\xb6 \r\n                location.reload();//\xe5\x88\xb7\xe6\x96\xb0\xe9\xa1\xb5\xe9\x9d\xa2\r\n            },\r\n            error : function() { alert("Error"); }\r\n        })\r\n}\r\n</script>\r\n            </div>\r\n          </div>\r\n    \t</article>\r\n      </div>\r\n    </section>\r\n    <footer class="footer">&copy; 2015 Altenergy Power System Inc.</footer>\r\n    <script>\r\n        /* \xe6\x8c\x87\xe5\xae\x9a5\xe5\x88\x86\xe9\x92\x9f\xe5\x88\xb7\xe6\x96\xb0\xe4\xb8\x80\xe6\xac\xa1 */\r\n        function myrefresh() {\r\n            window.location.reload();\r\n        }\r\n        setTimeout(\'myrefresh()\',300000); \r\n         \t\r\n    /* \xe5\x88\x87\xe6\x8d\xa2\xe8\xaf\xad\xe8\xa8\x80 */\r\n        $(".chlang").click(function(){\r\n            $.ajax({\r\n                url : "http://10.1.1.199/index.php/management/set_language",\r\n                type : "post",\r\n                dataType : "json",\r\n                data: "language=" + $(this).attr("id"),\r\n            })\r\n            setTimeout("location.reload();",500);//\xe5\x88\xb7\xe6\x96\xb0\xe9\xa1\xb5\xe9\x9d\xa2\r\n        });\r\n    </script>\r\n    </body>\r\n</html>'

        #html = download_retry(self.url_realtime)
        #print(html)

        bs = BeautifulSoup(html, 'html.parser')
        data_table = bs.find('tbody').find_all('tr')
        volts_l = []
        temp_l = []
        power_l = []
        all_data = {}
        inverter_date = {}
        all_data = {}
        for t in data_table:
            power_l = []
            for tt in t.find_all("td"):
                try:
                    id = re.findall("\d{12}-\d", tt.text.strip())[0]
                except IndexError:
                    pass
                if "W" in tt.text:
                    power = float(tt.text.strip()[:-1].strip())
                    power_l.append(power)
                elif "V" in tt.text:
                    volts = float(tt.text.strip()[:-1].strip())
                    volts_l.append(volts)
                elif "°C" in tt.text:
                    temp = float(tt.text.strip()[:-2].strip())
                    temp_l.append(temp)
            try:
                all_data[id] = {
                    "Power": power,
                    "Grid_Voltage": volts,
                    "Temperature": temp
                }
            except UnboundLocalError:
                pass

            inverter_id = id[:-2]
            if inverter_id not in inverter_date:
                inverter_date[inverter_id] = {
                    "Power": 0,
                    "Grid_Voltage": 0,
                    "Temperature": -273
                }
            try:
                inverter_date[inverter_id]["Power"] += power
                inverter_date[inverter_id]["Grid_Voltage"] = max(inverter_date[inverter_id]["Grid_Voltage"],volts)
                inverter_date[inverter_id]["Temperature"] = max(inverter_date[inverter_id]["Temperature"], temp)
            except UnboundLocalError:
                pass
        try:
            self.ecudata['max_volts'] = max(volts_l)
            self.ecudata['max_temp'] = max(temp_l)
        except ValueError:
            self.ecudata['max_volts'] = 0
            self.ecudata['max_temp'] = "N/A"

        self.ecudata['all_data'] = all_data
        self.ecudata['inverter_date'] = inverter_date
        # °C
    def get_power(self):
        return self.ecudata["last_system_power"]

    def export_status_data_to_pvoutput(self, whenlight=True):
        if whenlight:
            rightnow = datetime.datetime.utcnow()
            dusk = sun.dusk(self.installpoint.observer, date=datetime.datetime.utcnow())
            dawn = sun.dawn(self.installpoint.observer, date=datetime.datetime.utcnow())
            if not (rightnow > dawn.replace(tzinfo=None) and rightnow < dusk.replace(tzinfo=None) + datetime.timedelta(
                    hours=1)):
                return False
        self.pv = PVOutput(apikey=self.pvoutputkey, systemid=int(self.pvoutputsystemid))
        data_to_send = {
            "c1": 1,
            "v1": self.ecudata["generation_of_current_day"],
            "v2": self.ecudata["last_system_power"]
        }
        if "max_temp" in self.ecudata:
            data_to_send["v5"] = self.ecudata["max_temp"]
        if "max_volts" in self.ecudata:
            data_to_send["v6"] = self.ecudata["max_volts"]
        result = self.pv.addstatus(data=data_to_send)
        return result

    @timing
    def get_data(self, time_stamp: datetime = datetime.today()) -> pd.DataFrame:

        data = {
            'date': time_stamp.strftime("%Y-%m-%d")
        }

        response = requests.post(self.url_power, headers=self.headers, data=data)

        if response.status_code != 200:
            try:
                response.raise_for_status()
            except Exception as e:
                msg = (
                    'Bad status code! Response content = {}. Exception = {}'
                        .format(response.content, e))
                _LOG.exception(msg)
                raise e.__class__(msg)
        ans = {}
        energy = 0
        time_start_s = 0
        res = response.json()
        for record in res['power']:
            #print(record)


            time_actual = pd.Timestamp.fromtimestamp(record["time"]/1000)  # ,tz="Europe/Warsaw",tz="Europe/Warsaw"
            power =  record["each_system_power"]


            time_pass = time_actual.timestamp() - time_start_s
            if time_start_s == 0:
                time_pass = 300
            time_start_s = time_actual.timestamp()
            energy += power * time_pass / 3600
            ans[time_actual.round("5min")] = (power, energy)
        time_actual += pd.Timedelta(minutes=5)
        ans[time_actual.round("5min")] = (0, energy)
        return ans
        return
def main():
    api = apSystemsApi()
    ans = api.get_data()
    pprint (ans)


if __name__ == '__main__':
    main()
