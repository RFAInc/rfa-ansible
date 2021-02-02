###############################
### Author: Andy Escolastico
### Date: 01/26/2021
###############################

import requests
import json
import argparse
import re
import warnings
import sys

try:
    from creds import orion_creds
except:
    pass


class OrionInventory(object):
    def __init__(self):
        self.read_cli_args()
        if self.args.list:
            self.inventory = self.collect_inventory()
        elif self.args.host:
            self.inventory = self.empty_inventory()
        else:
            self.inventory = self.empty_inventory()
        print(json.dumps(self.inventory))
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action = 'store_true')
        parser.add_argument('--host', action = 'store')
        parser.add_argument('--server', action = 'store')
        parser.add_argument('--username', action = 'store')
        parser.add_argument('--password', action = 'store')
        self.args = parser.parse_args()
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}        
    @staticmethod
    def normalize_inventory(item):
        item = (re.sub('[^A-Za-z0-9]+', '_', item)).upper()
        return item
    def validate_credentials(self):
        if self.args.server and self.args.username and self.args.password:
            self.server = self.args.server
            self.username = self.args.username
            self.password = self.args.password
        elif "creds.orion_creds" in sys.modules:
            if orion_creds.server and orion_creds.username and orion_creds.password:
                self.server = orion_creds.server
                self.username = orion_creds.username
                self.password = orion_creds.password
            else:
                sys.exit("[ERROR] No creds found. Please provide credentials either by passing the script arguments or by populating a 'creds/orion_creds.py' file")
        else:
            sys.exit("[ERROR] No creds found. Please provide credentials either by passing the script arguments or by populating a 'creds/orion_creds.py' file")
    def collect_inventory(self):
        self.validate_credentials()
        server = self.server
        username = self.username
        password = self.password
        url = "https://" + server + ":17778/SolarWinds/InformationService/v3/Json/Query"
        query = "SELECT n.IPAddress, p.CWID, p.CustomerName FROM Orion.Nodes AS n JOIN Orion.NodesCustomProperties AS p on n.NodeID = p.NodeID WHERE n.Status!= 9"
        params = "query=" + query
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')
        response = requests.get(url, params=params, verify=False, auth=(username, password))
        data = (response.json())["results"]
        inv = {
            'all': {
                'hosts': [],
                'vars': {},
            },
            '_meta': {
                'hostvars': {}
            },
            'ungrouped': {
                'hosts': []
            }
        }
        # inv = {
        #     '_meta': {
        #         'hostvars': {}
        #     },
        #     'all': {
        #         'children': [],
        #     },
        #     'ungrouped': {
        #         'hosts': []
        #     }
        # }
        for i in data:
            ip = i["IPAddress"]
            cwmid = i["CWID"]
            customer = self.normalize_inventory(i["CustomerName"])
            # add host to all group
            inv['all']['hosts'].append(ip)
            if customer is None:
                inv['ungrouped']['hosts'].append(ip)
            # create client group if not exist
            elif customer not in inv:
                inv[customer] = {
                    'hosts': [ip],
                    'vars': {
                        'CWM_RECID': cwmid
                    }
                }
            # append ip if client group exists
            else:
                inv[customer]['hosts'].append(ip)
        return inv
OrionInventory()