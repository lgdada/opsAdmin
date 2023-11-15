#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import json
import os
import random
import string
import sys
import threading
import time

import yaml

sys.path.append(os.path.dirname(__file__))
from database import del_project_db, update_project_db
from dnsdbApi import dnsdb_api
from getSettings import setting
from jmsApi import jms_api
from logger import logger
from mutilThread import MyThread
from opstApi import opst_api

config = setting.config
opst = opst_api()

def create_project(file_path=None):
    if file_path:
        newProject_yaml = file_path
    else:
        newProject_yaml = setting.file_abspath(config.get('global','new_project'))
    with open(newProject_yaml, 'r') as f:
        newProject = yaml.safe_load(f)
    # 获取配置
    project_name = newProject['project_name']
    proxy_domain = newProject['proxy_domain']
    network_provider = newProject['network_provider']
    subnet_params = newProject['subnet_params']
    try:
        if opst.get_project(project_name):
            logger.warn(f'项目已存在，不能重复创建, {project_name}')
        else:
            logger.info(f"创建项目, {project_name}")
            project = opst.create_project(project_name)
            project_id = project['id']
            network_name = project['name'] + 'vpc'
            subnet_name = project['name'] + 'subnet'
            
            logger.info(f"创建网络, {network_name}")
            opst.create_network(name=network_name,
                                project_id=project_id,
                                provider=network_provider)
            # 子网参数
            subnet_params['network_name_or_id'] = network_name
            subnet_params['subnet_name'] = subnet_name
            subnet_params['tenant_id'] = project_id
            logger.info(f"创建子网, {subnet_name}")
            opst.create_subnet(**subnet_params)
    except Exception as e:
        logger.error(f'创建新项目失败, {e}')
        delete_project(project_name)
    else:
        update_project_db(project_name, proxy_domain)

def delete_project(project_name):
    network_name = project_name + 'vpc'
    logger.warn(f'删除网络, {network_name}')
    try:
        opst.delete_network(network_name)
    except ValueError as e:
        logger.warn(e)
    logger.warn(f'删除项目, {project_name}')
    try:
        opst.delete_project(project_name)
    except ValueError as e:
        logger.warn(e)
    else:
        del_project_db(project_name)

def server_is_exist(server_name):
    return opst.get_server(server_name) #bool

def create_server(semaphore, params, server_name):
    semaphore.acquire()
    logger.info(f"创建服务器, {server_name}")
    server = opst.create_server(**params, server_name=server_name)
    semaphore.release()
    return server

def get_inventory(host=None):
    inventory = dict()
    project_ids = list()
    hostvars = dict()
    server_list = list()
    for p in opst._list_projects().values():
        project_ids.append(p['id'])
    for i in project_ids:
        for server in opst._list_servers(project_id=i):
            hostvars[server['name']] = {"ansible_ssh_host":server['ip_addr']}
            server_list.append(server['name'])
    inventory['servers'] = {"hosts":server_list}
    inventory['_meta'] = {"hostvars":hostvars}
    if host:
        inventory = inventory['_meta']["hostvars"][host]
    print (json.dumps(inventory))

def batch_create_servers(item, batch=4):
    jms_assets = {}
    servers = []
    newServers_yaml = setting.file_abspath(config.get('global','new_servers'))
    with open(newServers_yaml, 'r') as f:
        newServers = yaml.safe_load(f)
    try:
        if newServers[item]:
            # get config
            server_params = {
                'image_name': newServers[item]['image'],
                'flavor_name': newServers[item]['flavor'],
                'project_name': newServers[item]['project'],
                'network_name': newServers[item]['network'] or newServers[item]['project'] + 'vpc'
            }
            is_jms = newServers[item]['push_jms']
            if is_jms:
                jms_group = newServers[item]['jms_group']
                jms_project = newServers[item]['jms_project']
                jms_label = newServers[item]['jms_label']
                jms = jms_api(project_group=jms_group, project=jms_project)
                # just for check jms config is not none
                jms.get_project_id(project=jms_project)
            # 线程池
            semaphore = threading.BoundedSemaphore(batch)
            t_jobs = []
            for server_name in newServers[item]['servers']:
                if server_is_exist(server_name) is None:
                    t = MyThread(create_server,args=(semaphore, server_params, server_name))
                    t_jobs.append(t)
                    t.start()
                    time.sleep(1)
                else:
                    logger.warn(f'server already exists, skip!, {server_name}')
            for t in t_jobs:
                t.join()
                server = t.get_result()
                jms_params = {
                    'hostname': server['name'],
                    'ip': server['accessIPv4'],
                    'label': jms_label
                }
                servers.append({'hostname': server['name'], 'ip': server['accessIPv4']})
                if is_jms:
                    logger.info(f'推送到jumpserver, {jms_params}')
                    jms.add_asset(**jms_params)
            project_id = opst.get_project(name_or_id=newServers[item]['project']).id
            opst._list_servers(project_id=project_id, refresh=True)
            logger.info('refresh subnet cache successful')
        else:
            logger.warn(f'please confirm the {newServers_yaml} has {item} item')
    except Exception as e:
        logger.error(e)
    finally:
        if is_jms:
            jms_assets['jms_group'] = jms_group
            jms_assets['jms_project'] = jms_project
            jms_assets['servers'] = servers
            salt = ''.join(random.sample(string.ascii_letters + string.digits, 6))
            tmp_assets_yaml = '/tmp/' + salt + '.yaml'
            with open(tmp_assets_yaml, 'w') as f:
                yaml.dump(jms_assets, f, allow_unicode=True)
            logger.info(f'write jms_assets in file, {tmp_assets_yaml}')


def add_assets_by_manaul(jms_assets_yaml):
    try:
        if os.path.exists(jms_assets_yaml):
            with open(jms_assets_yaml, 'r') as f:
                jms_assets = yaml.safe_load(f)
            jms_group = jms_assets['jms_group']
            jms_project = jms_assets['jms_project']
            jms = jms_api(project_group=jms_group, project=jms_project)
            # just for check jms config is not none
            jms.get_project_id(project=jms_project)
            for server in jms_assets['servers']:
                logger.info(f'推送到jumpserver, {server}')
                jms.add_asset(hostname=server['hostname'], ip=server['ip'])
        else:
            logger.warn(f'jms_assets_yaml file {jms_assets_yaml} not exists')
    except Exception as e:
        logger.error(e)


def print_opst_resource(resource, refresh=False, **kwargs):
    try:
        if resource == 'opst_project':
            opst.print_projects(refresh=refresh,**kwargs)
        if resource == 'opst_flavor':
            opst.print_flavors(refresh=refresh,**kwargs)
        if resource == 'opst_image':
            opst.print_images(refresh=refresh,**kwargs)
        if resource == 'opst_network':
            opst.print_networks(refresh=refresh,**kwargs)
        if resource == 'opst_subnet':
            opst.print_subnets(refresh=refresh,**kwargs)
        if resource == 'opst_server':
            opst.print_servers(refresh=refresh,**kwargs)
    except Exception as e:
        logger.error(e)

def add_dnsdb_records(name, ip, file_path=None, manual=None):
    try:
        dnsdb = dnsdb_api()
        if manual:
            logger.info(f'添加解析到dnsdb, {name, ip}')
            dnsdb.add_record(name, ip)
        elif file_path:
            newRecords_yaml = file_path
        else:
            newRecords_yaml = setting.file_abspath(config.get('global','new_records'))
        with open(newRecords_yaml, 'r') as f:
            new_records = yaml.safe_load(f)
        for record_name in new_records:
            name = record_name
            ip = new_records[record_name]
            logger.info(f'添加解析到dnsdb, {name, ip}')
            dnsdb.add_record(name, ip)
            time.sleep(0.5)
    except Exception as e:
        logger.error(e)

if __name__ == "__main__":
    opst = opst_api()
    jms = jms_api()
    opst = opst_api(cloud_name='prod_sh_1')
    refresh = True
    create_project(opst)
    batch_create_servers(opst, 'vms')
    opst.print_servers(refresh=refresh)
    print (opst.get_server('123'))
    add_assets_by_manaul("/tmp/xfsiDN.yaml")
