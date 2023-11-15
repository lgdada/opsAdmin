#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import argparse
import os
import sys

import ldap3
import pyzabbix

sys.path.append(os.path.dirname(__file__))
from getSettings import setting
from logger import logger

config = setting.config

ldap_host = config.get('ldap', 'ldap_host')
ldap_user = config.get('ldap', 'ldap_user')
ldap_pass = config.get('ldap', 'ldap_pass')
ldap_base = config.get('ldap', 'ldap_base')
ldap_attributes = config.get('ldap', 'ldap_attributes').split(',')

zabbix_url = config.get('zabbix', 'zabbix_url')
zabbix_user = config.get('zabbix', 'zabbix_user')
zabbix_pass = config.get('zabbix', 'zabbix_pass')

class LDAP(object):
    def __init__(self,host=None,base=None,user=None,password=None):
        if not host:
            self.host = ldap_host
        if not base:
            self.base = ldap_base
        if not user:
            self.user = ldap_user
        if not password:
            self.password = ldap_pass
        try:
            self.ldap_server = ldap3.Server(self.host)
            self.conn = ldap3.Connection(self.ldap_server, user=self.user, password=self.password, auto_bind=True)
        except Exception as e:
            logger.error(f"{e}, {locals()}")

    def getAttributes(self,username):
        try:
            ldap_filter = f"(sAMAccountName={username})"
            res = self.conn.search(search_base=self.base, search_filter=ldap_filter,attributes=ldap_attributes)
            if res is True:
                return self.conn.response[0]["attributes"]
            else:
                raise Exception(f"Error! User \"{username}\" getAttributes None!!")
        except Exception as e:
            logger.error(f"{e}, {locals()}")

class ZABBIX(object):
    def __init__(self,url=None,user=None,password=None):
        if not url:
            self.url = zabbix_url
        if not user:
            self.user = zabbix_user
        if not password:
            self.password = zabbix_pass
        try:
            self.zapi = pyzabbix.ZabbixAPI(self.url)
            self.zapi.login(user=self.user, password=self.password)
            self.zapi.session.verify = False
            self.zapi.timeout = 5.1
        except Exception as e:
            logger.error(f"{e}, {locals()}")

    def getUsergroupId(self,usergroupname):
        try:
            res = self.zapi.usergroup.get()
            for r in res:
                if r['name'] == usergroupname:
                    usergroupid = r['usrgrpid']
            return usergroupid
        except Exception as e:
            logger.error(f"{e}, {locals()}")

    def getRoleId(self,rolename):
        try:
            res = self.zapi.role.get()
            for r in res:
                if r['name'] == rolename:
                    roleid = r['roleid']
            return roleid
        except Exception as e:
            logger.error(f"{e}, {locals()}")

    def createUser(self,user,mail,displayName,usergroupid,roleid):
        try:
            alias = user
            medias = [{"mediatypeid": "1","sendto": [mail]}]
            name = displayName
            usrgrps = [{"usrgrpid": usergroupid}]
            res = self.zapi.user.create(alias=alias,medias=medias,name=name,usrgrps=usrgrps,roleid=roleid)
            return res
        except Exception as e:
            logger.error(f"{e}, {locals()}")


if __name__ == '__main__':
    ldapApi = LDAP()
    zabbixApi = ZABBIX()
    zabbixUsergroupName = "Ldap_users"
    zabbixRoleName = "Guest role"

    parser = argparse.ArgumentParser(description='Search user in ldap, and create new user in zabbix.')
    parser.add_argument("str",type=str,nargs='+',help="input user's ldap name one or more.")
    args = parser.parse_args()
    for ldapUser in args.str:
        try:
            # use ldap api
            l_result = ldapApi.getAttributes(ldapUser)
            ldapMail = l_result['mail']
            ldapDisplayName = l_result['displayName']
            # use zabbix api
            zabbixUsergroupId = zabbixApi.getUsergroupId(zabbixUsergroupName)
            zabbixRoleId = zabbixApi.getRoleId(zabbixRoleName)
            z_result = zabbixApi.createUser(ldapUser,ldapMail,ldapDisplayName,zabbixUsergroupId,zabbixRoleId)
            print (ldapUser,z_result)
        except Exception as e:
            logger.error(e)
