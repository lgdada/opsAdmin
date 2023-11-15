import sys
import os
import re
from requests import request

sys.path.append(os.path.dirname(__file__))
from getSettings import setting
from logger import logger

config = setting.config

class dnsdb_api(object):
    def __init__(self,timeout=2):
        self.dnsdb_url = config.get("dnsdb", "dnsdb_url")
        self.timeout=timeout

    def _request(self, method, url , **kwargs):
        return request(method, url, timeout=self.timeout, **kwargs)

    def add_record(self,name,ip,record_type="A"):
        data = {
            "domain": name,
            "record": ip,
            "record_type": record_type,
            "ttl": 0
            }
        url = self.dnsdb_url+"/add_record"
        req = self._request('post',url,data=data)
        if req.status_code == 200:
            if req.json()["errcode"] == 0:
                logger.debug(f'add dnsdb record successful, {req.json()}')
            else:
                logger.warn(f'添加解析失败, url: {url}, data: {data}, reason: {req.json()}')
        else:
            raise Exception("request failed, url: %s, data: %s, reason: %s" % (url, data, req.text))
if __name__ == '__main__':
    dnsdb = dnsdb_api()
    dnsdb.add_record("", "")