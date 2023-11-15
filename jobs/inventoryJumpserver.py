#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import argparse
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from utils.getSettings import setting
from utils.jmsApi import jms_api
from utils.logger import logger
from utils.models import Actions, Jobs, Projects, Session


def get_inventory(refresh=False):
    # is_cache_stale()
    inventory = dict()
    hostvars = dict()
    try:
        jms = jms_api()
        jms_labels = jms.get_labels()
        with Session.begin() as session:
            jobs = dict()
            job_ids = session.query(Actions).all()
            for jid in job_ids:
                jobs[jid.jobs.job_name]= jid.jobs.job_id
            for job_name, job_id in jobs.items():
                inventory[job_name] = list()
                for action in session.query(Actions).filter(Actions.job_id==job_id).all():
                    # 获取动作标签，用于获取相应的主机列表
                    if action.label:
                        label = action.label + ":" + action.label
                    else:
                        label = None
                    # 允许项目为空
                    if action.projects:
                        project = action.projects.project
                        group = action.projects.group
                        proxy_domain = action.projects.proxy_domain
                        node_id = jms.get_project_id(project, group)
                    else:
                        node_id = None
                        proxy_domain = None
                    # 根据node_id和label获取主机列表
                    assets = jms.get_assets(node_id, label=label)
                    # 为每个主机设置变量
                    for asset in assets:
                        inventory[job_name].append(asset['hostname'])
                        jms_nodes = asset['nodes_display']
                        if proxy_domain is None:
                            s = jms_nodes[0].split("/")
                            if len(s) == 3:
                                project = s[2]
                                group = s[1]
                            else:
                                project = s[3]
                                group = s[2]
                            Project = session.query(Projects).filter(Projects.project == project, Projects.group == group).first()
                            Proxy_domain = Project.proxy_domain
                        hostvars[asset['hostname']] = {"ansible_ssh_host": asset['ip'], 
                                                        "proxy_domain": proxy_domain or Proxy_domain,
                                                        "asset_labels": [],
                                                        "jms_nodes": jms_nodes}
                        # 将jumpserver的标签加到ansible变量
                        for asset_label_id in asset['labels']:
                            for jms_label in jms_labels:
                                if asset_label_id == jms_label['id']:
                                    hostvars[asset['hostname']]['asset_labels'].append(jms_label['value'])
        inventory["_meta"] = {"hostvars": hostvars}
        return inventory
    except Exception as e:
        logger.error(e)

def get_host(host, refresh=False):
    inventory = get_inventory(refresh=refresh)
    result = inventory['_meta']['hostvars'][host]
    return result

def parse_args():
    parser = argparse.ArgumentParser(description='Dynamic get ansible inventory Module')
    parser.add_argument('--refresh', action='store_true',
                        help='Refresh cached information')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true',
                       help='List active servers')
    group.add_argument('--host', help='List details about the specific host')

    return parser.parse_args()


def main():
    args = parse_args()
    try:
        if args.list:
            output = get_inventory(refresh=args.refresh)
        elif args.host:
            output = get_host(args.host, refresh=args.refresh)
        print (json.dumps(output))
    except Exception as e:
        logger.error(e)
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
