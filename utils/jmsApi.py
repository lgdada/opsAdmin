# -*- coding: utf-8 -*-
'''
1、资产分组：组-项目
2、创建应用组（中间有不存在的节点，自动创建）
3、获取组id
4、添加资产到应用组，标签绑定负责人
5、移除资产
6、添加用户到开发组，添加公钥，发送邮件给该人（需要先web登录）
7、用户授权，以用户名创建授权规则，添加相应应用组，给app和tomcat权限
'''
import json
import os
import sys
import time
from datetime import datetime
from  requests import request

from httpsig.requests_auth import HTTPSignatureAuth

sys.path.append(os.path.dirname(__file__))
from getSettings import setting
from logger import logger


class jms_api():
    def __init__(self, admin_user="root", system_user=[], project_group=None, project=None, timeout=2):
        self.headers = {
            'Accept': 'application/json',
            'Date': time.asctime(time.localtime())
        }
        # get config
        self.config = setting.config
        self.AccessKeyID = self.config.get('jumpserver', 'AccessKeyID')
        self.AccessKeySecret = self.config.get('jumpserver', 'AccessKeySecret')
        self.jms_url = self.config.get('jumpserver', 'jms_url')
        self.gitlab_url = self.config.get('gitlab', 'gitlab_url')
        self.gitlab_token = self.config.get('gitlab', 'gitlab_token')

        # set connection auth
        self.auth = HTTPSignatureAuth(key_id=self.AccessKeyID, secret=self.AccessKeySecret,
                    algorithm='hmac-sha256',
                    headers=['(request-target)', 'accept', 'date', 'host'])

        # get init value
        self.admin_user = admin_user
        self.system_user = system_user
        self.project_group = project_group
        self.project = project
        
        self.timeout=timeout
        self.project_id = None
        self.admin_user_id = None

    def _request(self, method, url , **kwargs):
        return request(method, url, auth=self.auth, headers=self.headers, timeout=self.timeout, **kwargs)

    def _request_raise(self, req, url, **kwargs):
        raise Exception("request failed, url: %s, %s, reason: %s, others: %s" % (url, req.status_code, req.reason, kwargs))

    # 获取管理用户id
    def get_admin_user_id(self, admin_user):
        params={'username': admin_user}
        url = self.jms_url + '/assets/admin-users/'
        req = self._request('get',url, params=params)
        if req.status_code == 200:
            if req.text == "[]":
                raise Exception(f"admin_user has not been created yet, {locals()}")
            else:
                admin_user_id = req.json()[0]["id"]
                return admin_user_id
        else:
            self._request_raise(req, url, params=params)


    # 获取系统用户id
    def get_system_user_id(self, system_user=[]):
        system_user_id = []
        url = self.jms_url + '/assets/system-users/'
        for user in system_user:
            params={'username': user}
            req = self._request('get', url, params=params)
            if req.status_code == 200:
                if req.text == "[]":
                    raise Exception(f"system_user has not been created yet, {locals()}")
                else:
                    system_user_id.append(req.json()[0]["id"])
                    return system_user_id
            else:
                self._request_raise(req, url, params=params)

    # 获取项目组id defult/xxx
    def get_project_group_id(self, project_group):
        url = self.jms_url + '/assets/nodes/children/'
        req = self._request('get', url)
        if req.status_code == 200:
            for r in req.json():
                if r.get("value") == project_group:
                    return r.get("id")
            raise Exception(f"project group has not been created yet, {locals()}")
        else:
            self._request_raise(req, url, project_group=project_group)


    # 获取项目id
    def get_project_id(self, project, project_group=None):
        if project_group is None:
            project_group = self.project_group
        project_group_id = self.get_project_group_id(project_group)

        url = self.jms_url + '/assets/nodes/' + project_group_id + '/children/'        
        req = self._request('get', url)
        if req.status_code == 200:
            for r in req.json():
                if r.get("value") == project:
                    return r.get("id")
            raise ValueError(f"project is not in the project group, {locals()}")
        else:
            self._request_raise(req, url, project=project)
    
    #获取项目列表
    def get_project_list(self):
        url = self.jms_url + '/assets/nodes/'
        req = self._request('get', url)
        if req.status_code == 200:
            return req.json()
        raise Exception("get project list error")

    # 创建项目
    def create_project(self, project, project_group=None):
        if project_group is None:
            project_group = self.project_group
        project_group_id = self.get_project_group_id(project_group)
        try:
            if self.get_project_id(project, project_group):
                raise Exception(f"project is already in the project team, {locals()}")
        except ValueError as e:
            logger.debug(e)

        url = self.jms_url + '/assets/nodes/' + project_group_id + '/children/'
        data = {
            'value': project
        }
        req = self._request('post', url, data=data)
        if req.status_code == 201:
            logger.debug(f"create project successful, {req.text}")
            return req.json()["id"]
        else:
            self._request_raise(req, url, data=data)


    # 添加资产
    def add_asset(self, hostname, ip, project_group=None, project=None, label=None):          
        if project is None:
            project = self.project
        if project_group is None:
            project_group = self.project_group
        if self.project_id is None:
            self.project_id = self.get_project_id(project, project_group)
        if self.admin_user_id is None:
            self.admin_user_id = self.get_admin_user_id(self.admin_user)
        if label:
            label_id = self.get_label(label=label)
        else:
            label_id = None
        url = self.jms_url + '/assets/assets/'
        data = {
            "hostname": hostname,
            "ip": ip,
            # "protocol": "ssh",
            # "port": 22,
            'protocols': [ "ssh/22" ],
            "admin_user": self.admin_user_id,
            "is_active": True,
            "platform": "Linux",
            "nodes": [self.project_id],
            "labels": [label_id]
            }
        req = self._request('post', url, data=data)
        if req.status_code == 201:
            logger.debug(f"add asset successful, {req.text}")
            return req.json()
        else:
            logger.error(f"add asset failed, {req.text}, {locals()}")
            return False

    def get_assets(self, node_id=None, label=None, hostname=None):
        params = {'label': label,
                  'node': node_id,
                  'hostname':hostname}
        url = self.jms_url + '/assets/assets/'
        req = self._request('get',url, params=params)
        if req.status_code == 200:
            return req.json()
        else:
            self._request_raise(req, url, params=params)

    def get_label(self, label):
        params = {'name': label}
        url = self.jms_url + '/assets/labels/'
        req = self._request('get',url, params=params)
        if req.status_code == 200:
            if req.text == "[]":
                raise Exception(f"label {label} has not been created yet, {locals()}")
            else:
                label_id = req.json()[0]["id"]
                return label_id
        else:
            self._request_raise(req, url, params=params)

    def get_labels(self):
        url = self.jms_url + '/assets/labels/'
        req = self._request('get',url)
        if req.status_code == 200:
            return req.json()
        else:
            self._request_raise(req, url)

    # 获取普通用户id
    def get_user_id(self, user_name):
        params = {'username': user_name}
        url = self.jms_url + '/users/users/'
        req = self._request('get' ,url, params=params)
        if req.status_code == 200:
            if req.text == "[]":
                raise Exception(f"user has not been created yet, {locals()}")
            else:
                return req.json()[0]["id"]
        else:
            self._request_raise(req, url, params=params)
    
    # 添加用户key
    def add_user_key(self, user_name, pub_key):
        user_id = self.get_user_id(user_name)        
        if pub_key is not None:
            user_key = pub_key
        else:
            gitlab_headers = {'PRIVATE-TOKEN': self.gitlab_token}
            url = self.gitlab_url + "/users/"
            gitlab_params = {'username': user_name}
            # 获取用户gitlab_id
            gitlab_id = None
            try:
                req = request('get', url, headers=gitlab_headers, timeout=self.timeout, params=gitlab_params)
                if req.status_code == 200 and req.text != "[]":
                    gitlab_id = req.json()[0]["id"]
            except Exception as e:
                print(str(e))
            
            if gitlab_id is None:
                print (f"用户[{user_name}]在gitlab上不存在")
                return False
            
            # 获取用户gitlab_key
            url = self.gitlab_url + "/users/" + str(gitlab_id) + "/keys"
            gitlab_key = None
            try:
                req = request('get', url, headers=gitlab_headers, timeout=self.timeout)
                if req.status_code == 200 and req.text != "[]":
                    gitlab_key = sorted(req.json(), key=lambda x: x['created_at'])[-1]['key']
            except Exception as e:
                print(str(e))
            
            if gitlab_key is None:
                print (f"用户[{user_name}]在gitlab上没有配置秘钥")
                return False
            else:
                user_key = gitlab_key
            
        # 导入用户秘钥到jumpserver
        url = self.jms_url + f"/users/users/{user_id}/pubkey/update/"
        data = {
            "public_key": user_key
        }
        try:
            req = self._request('put',url, data=data)
            if req.status_code == 200:
                print (f"用户[{user_name}]，公钥[{user_key}]上传成功！")
                return True
            else:
                return False
        except Exception as e:
            print(str(e))


    def get_policy_id(self, policy_name):
        params = {'name': policy_name}
        url = self.jms_url + '/perms/asset-permissions/'
        try:
            req = self._request('get',url, params=params)
            if req.status_code == 200 and req.text != "[]":
                policy_id = req.json()[0]["id"]
                return policy_id
            else:
                return None
        except Exception as e:
            print(str(e))

    def create_policy(self, policy_name, system_user=[]):
        if system_user == []:
            system_user = self.system_user
        system_user_id = self.get_system_user_id(system_user)
        
        url = self.jms_url + '/perms/asset-permissions/'
        data = {
            "name": policy_name,
            "system_users": system_user_id
        }
        try:
            req = self._request('post',url, data=data)
            if req.status_code == 201:
                policy_id = req.json()["id"]
                return policy_id
            else:
                print (f"创建策略失败，[{req.text}]")
                return False
        except Exception as e:
            print(str(e))


    # 用户授权
    def update_policy(self, user_name, policy_name, project=None, project_group=None, system_user=[]):
        policy_id = self.get_policy_id(policy_name)
        user_id = self.get_user_id(user_name)
        if project is None:
            project = self.project
        if project_group is None:
            project_group = self.project_group
        project_id = self.get_project_id(project, project_group)

        if system_user == []:
            system_user = self.system_user
        system_user_id = self.get_system_user_id(system_user)

        url = self.jms_url + f"/perms/asset-permissions/{policy_id}/"
        data = {
            "name": policy_name,
            "users": [user_id],
            "nodes": [project_id],
            "system_users": [system_user_id],
            "is_valid": True
        }
        try:
            req = self._request('put',url, data=data)
            if req.status_code == 200:
                # policy_id = req.json()["id"]
                # return policy_id
                print (req.text)
            else:
                print (f"更新策略失败，[{req.text}]")
                return False
        except Exception as e:
            print(str(e))


if __name__ == '__main__':
    # print (time.asctime(time.localtime()))
    # print (add_assets("test_host", "1.1.1.1", "test", "龙盈", "ntt"))
    # print (get_node(node_name="运维服务"))
    # get_system_user(system_user="root")
    try:
        jms = jms_api()
        print (jms.get_assets(label="nginx:nginx"))
    except Exception as e:
        logger.error(e)
    # newjms.add_user_key(user_name="gaoliang")
    # print (newjms.create_policy("gaoliang", ["root","app"]))
    # print (newjms.update_policy("gaoliang", "gaoliang", "盈盈医疗", "美业", ["root","app"]))
    # config = configparser.ConfigParser()
    # config.read(config_file, encoding="utf-8")
    # print (config.sections())
