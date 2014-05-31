import json
import requests
import ssl
import getpass
import sys
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

START_URL = "https://wwws.mint.com/login.event?task=L"
LOGIN_PAGE = "https://wwws.mint.com/loginUserSubmit.xevent"
HEADERS = {"accept": "application/json"}
CONTROLLER_BASE = "https://wwws.mint.com/bundledServiceController.xevent?" +\
                  "legacy=false&token="


class MintHTTPSAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, **kwargs):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize,
                                       ssl_version=ssl.PROTOCOL_SSLv3,
                                       **kwargs)

class MintApi(object):
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.token = None
        self.request_id = "42"

    def login(self):
        data = {"username": self.email, "password": self.password,
                "task": "L", "browser": "firefox", "browserVersion": "27",
                "os": "linux"}
        self.session.mount('https://', MintHTTPSAdapter())
        if not self.session.get(START_URL).status_code == requests.codes.ok:
            raise Exception("Failed to load Mint main page '{}'"
                            .format(START_URL))
        response = self.session.post(LOGIN_PAGE, data=data, headers=HEADERS).text
        if "token" not in response:
            raise Exception("Mint.com login failed[1]")
        response = json.loads(response)
        if not response["sUser"]["token"]:
            raise Exception("Mint.com login failed[2]")
        self.token = response["sUser"]["token"]

    def get_accounts(self):
        data = {"input": json.dumps([
            {"args":
                {"types":
                    ["BANK",
                    "CREDIT",
                    "INVESTMENT",
                    "LOAN",
                    "MORTGAGE",
                    "OTHER_PROPERTY",
                    "REAL_ESTATE",
                    "VEHICLE",
                    "UNCLASSIFIED"]},
                "id": self.request_id,
                "service": "MintAccountService",
                "task": "getAccountsSortedByBalanceDescending"}])}
        response = self.session.post(CONTROLLER_BASE+self.token, data=data,
                                headers=HEADERS).text
        if self.request_id not in response:
            raise Exception("Could not parse account data: " + response)
        response = json.loads(response)
        accounts = response["response"][self.request_id]["response"]
        return accounts


def main():
    try:
        input = raw_input
    except NameError:
        pass
    if len(sys.argv) >= 3:
        email, password = sys.argv[1:]
    else:
        email = input("Mint email: ")
        password = getpass.getpass("Password: ")
    mint_api = MintApi(email, password)
    mint_api.login()
    accounts = mint_api.get_accounts()
    print(json.dumps(accounts, indent=2))

if __name__ == "__main__":
    main()
