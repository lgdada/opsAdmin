#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import json
import os
import sys
from datetime import datetime

from openstack import enable_logging, connect as opsdk
import pandas as pd

sys.path.append(os.path.dirname(__file__))
from getSettings import setting
from logger import logger

config = setting.config

cloud_file = setting.file_abspath(config.get('openstack', 'cloud_file'))
cache_path = setting.file_abspath(config.get('openstack', 'cache_path'))
debug_file = setting.file_abspath(config.get('openstack', 'debug_file'))

os.environ['OS_CLIENT_CONFIG_FILE'] = cloud_file
if config.getboolean('openstack', 'cloud_debug'):
    enable_logging(debug=True, path=debug_file)


# pandas 输出格式
pd.set_option('expand_frame_repr', False)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('expand_frame_repr', False)
# 行首居中
pd.set_option('colheader_justify', 'center')
#显示所有列
pd.set_option('display.max_columns', None)
#显示所有行
pd.set_option('display.max_rows', None)
#设置value的显示长度为100，默认为50
pd.set_option('max_colwidth',100)


class opst_api(object):
    def __init__(self, cloud_name=None):
        if not cloud_name:
            cloud_name = config.get('openstack', 'cloud_name')
        self.conn = opsdk(cloud=cloud_name, load_envvars=True, load_yaml_config=False)
        self.update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _get_cache_path(self):
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)
        return cache_path

    def _read_cache_file(self, cache_file):
        with open(cache_file, 'r') as f:
            data = f.read()
            data = json.loads(data)
            self.update_time = datetime.fromtimestamp(os.path.getmtime(cache_file)).strftime('%Y-%m-%d %H:%M:%S')
        return data

    def _write_cache_file(self, data, cache_file):
        with open(cache_file, 'w') as f:
            json.dump(data, f, ensure_ascii=False,sort_keys=True, indent=4)
        return True

############# projects #############

    def _list_projects(self, refresh=False):
        projects = {}
        cache_file = os.path.join(self._get_cache_path(), 'projects')
        if refresh or not os.path.exists(cache_file):
            for p in self.conn.identity.projects():
                p_dict = p.to_dict()
                projects[p_dict['name']]= p_dict
            self._write_cache_file(projects, cache_file)
        else:
            projects = self._read_cache_file(cache_file)        
        return projects

    def _print_projects(self, projects, project_name=None):
        columns = ['name','id']
        data = []
        ps = []
        if project_name and project_name in projects:
            ps = [projects[project_name]]
        else:
            ps = projects.values()
        for p in ps:
            data.append([p['name'], p['id']])
        df = pd.core.frame.DataFrame(data, columns=columns)
        df = df[df.name != "admin"]
        df = df[df.name != "service"]
        df = df.sort_values(by=['name']).reset_index(drop=True)
        df.index=df.index + 1
        print (f'projects list: (updatetime: {self.update_time})')
        print (df)

    def get_project(self, name_or_id):
        return self.conn.get_project(name_or_id=name_or_id)

    def print_projects(self, refresh=False, project_name=None):
        projects = self._list_projects(refresh=refresh)
        self._print_projects(projects,project_name)
        
    def delete_project(self, name_or_id):
        result = self.conn.delete_project(name_or_id=name_or_id)
        if not result:
            raise ValueError(f'the project has not been create yet, {locals()}')
        logger.debug(f'delete project successful, {locals()}')
        self._list_projects(refresh=True)
        logger.debug(f'refresh project cache successful')
        return True

    def create_project(self, project_name, proxy_domain=None):
        params = {
            'name': project_name,
        }
        params['domain_id'] = self.conn.get_domain('default')['id']
        project = self.conn.create_project(**params)
        logger.debug(f"create project successful, {json.dumps(project)}")

        # 授权
        self.grant_role(project_name=project_name)
                
        # 放通安全策略
        security_group = self.get_security_group(security_group_name='default', project_id=project['id'])
        rule_params = {
            'secgroup_name_or_id': security_group['id'],
            'direction': 'ingress',
            'ethertype': 'IPv4'
        }
        security_group_rule = self.create_security_group_rule(**rule_params)
        logger.debug(f'create security group rule successful, {json.dumps(security_group_rule)}')
        
        # 更新project缓存
        self._list_projects(refresh=True)
        logger.debug(f'refresh projects cache successful')
        return project

    def grant_role(self, project_name, role='admin', wait=True):
        '''授权给admin'''
        user_id = self.conn.current_user_id
        params = {
            'name_or_id': role,
            'user': user_id,
            'project': project_name,
            'wait': wait
        }
        result = self.conn.grant_role(**params)
        if not result:
            raise Exception(f'grant role to admin failed, {locals()}')
        logger.debug(f"grant role to admin successful, {locals()}")
        return result # bool
        

    def create_security_group_rule(self, **params):
        return self.conn.create_security_group_rule(**params)


    def get_security_group(self, security_group_name, project_id):
        '''有且仅返回一个组id'''
        filters = {
            'tenant_id': project_id
        }
        security_group = self.conn.get_security_group(name_or_id=security_group_name,filters=filters)
        if security_group:
            return security_group
        else:
            raise Exception(f'project security group not exists, {locals()}')

############# flavors #############

    def _list_flavors(self, refresh=False):
        flavors = {}
        cache_file = os.path.join(self._get_cache_path(), 'flavors')
        if refresh or not os.path.exists(cache_file):
            for f in self.conn.compute.flavors():
                f_dict = f.to_dict()
                flavors[f_dict['name']] = f_dict
            self._write_cache_file(flavors,cache_file)
        else:
            flavors = self._read_cache_file(cache_file)
        return flavors

    def _print_flavors(self, flavors, flavor_name=None):
        columns = ['name','disk', 'ram', 'vcpus', 'is_public','is_disabled', 'id', 'extra_specs', 'description']
        data = []
        fs = []
        if flavor_name and flavor_name in flavors:
            fs = [flavors[flavor_name]]
        else:
            fs = flavors.values()
        for f in fs:
            data.append([f['name'], f['disk'], f['ram'], f['vcpus'], f['is_public'], f['is_disabled'], f['id'], f['extra_specs'], f['description']])
        
        df = pd.core.frame.DataFrame(data, columns=columns)
        df = df.sort_values(by=['name', 'ram']).reset_index(drop=True)
        df.index = df.index + 1
        df['disk'] = df['disk'].astype('str') + ' GB'
        df['ram'] = df['ram'].div(1024).astype('int32').astype('str') + ' GB'
        df['vcpus'] = df['vcpus'].astype('str') + ' C'
        print (f'flavors list: (updatetime: {self.update_time})')
        print (df)

    def print_flavors(self, refresh=False,flavor_name=None):
        flavors = self._list_flavors(refresh=refresh)
        self._print_flavors(flavors,flavor_name)


############# images #############
    def _list_images(self, refresh=False):
        images = {}
        cache_file = os.path.join(self._get_cache_path(), 'images')
        if refresh or not os.path.exists(cache_file):
            for i in self.conn.compute.images():
                i_dict = i.to_dict()
                images[i_dict['name']] = i_dict
            self._write_cache_file(images, cache_file)
        else:
            images = self._read_cache_file(cache_file)
        return images

    def _print_images(self, images, image_name=None):
        columns = ['name','size', 'id', 'status', 'created_at', 'updated_at']
        data = []
        ims = []
        if image_name and image_name in images:
            ims = [images[image_name]]
        else:
            ims = images.values()
        for i in ims:
            data.append([i['name'], i['size'], i['id'], i['status'], i['created_at'], i['updated_at']])
        df = pd.core.frame.DataFrame(data, columns=columns)
        df['size'] = df['size'].div(1024).div(1024).astype('int32').astype('str') + ' MB'
        df = df.sort_values(by=['name']).reset_index(drop=True)
        df.index = df.index + 1
        print (f'images list: (updatetime: {self.update_time})')
        print (df)

    def print_images(self, refresh=False, image_name=None):
        images = self._list_images(refresh=refresh)
        self._print_images(images, image_name)

############# networks #############

    def _list_networks(self, refresh=False):
        networks = {}
        projects = self._list_projects(refresh=refresh)
        subnets = self._list_subnets(refresh=refresh)
        cache_file = os.path.join(self._get_cache_path(), 'networks')
        if refresh or not os.path.exists(cache_file):
            for n in self.conn.network.networks():
                n_dict = n.to_dict()
                for p in projects.values():
                    if p['id'] == n_dict['project_id']:
                        n_dict['project_name'] = p['name']
                        break
                n_dict['subnets_name'] = []
                for sid in n_dict['subnet_ids']:
                    for s in subnets.values():
                        if s['id'] == sid:
                            n_dict['subnets_name'].append(s['name'])
                            break
                networks[n_dict['name']] = n_dict
            self._write_cache_file(networks, cache_file)
        else:
            networks = self._read_cache_file(cache_file)
        return networks

    def _print_networks(self, networks, network_name=None):
        columns = ['name','id','type', 'physical', 'segmentation_id', 'project_name', 'subnets_name','is_shared','status']
        data = []
        ns = []
        if network_name and network_name in networks:
            ns = [networks[network_name]]
        else:
            ns = networks.values()
        for n in ns:
            data.append([n['name'], n['id'], n['provider_network_type'], n['provider_physical_network'], 
                        n['provider_segmentation_id'], n['project_name'],
                        n['subnets_name'], n['is_shared'], n['status']])
        df = pd.core.frame.DataFrame(data, columns=columns)
        df.fillna(0, inplace=True)
        df['segmentation_id'] = df['segmentation_id'].astype('int32')
        df = df.sort_values(by=['name']).reset_index(drop=True)
        df.index = df.index + 1
        print (f'networks list: (updatetime: {self.update_time})')
        print (df)

    def print_networks(self, refresh=False, network_name=None):
        networks = self._list_networks(refresh=refresh)
        self._print_networks(networks, network_name)


    def create_network(self, name, project_id, shared=False, provider=None, external=True):
        network =  self.conn.create_network(name=name, project_id=project_id, 
                                        shared=shared, provider=provider, 
                                        external=external)
        logger.debug(f'create network successful, {json.dumps(network)}')
        # 更新网络缓存
        self._list_networks(refresh=True)
        logger.debug(f'refresh network cache successful')
        return network  # Munch

    def delete_network(self, name_or_id):
        result = self.conn.delete_network(name_or_id)
        # 失败返回 false
        if not result:
            raise ValueError(f'the network has not been create yet, {locals()}')
        logger.debug(f'delete network successful, {locals()}')
        self._list_networks(refresh=True)
        logger.debug(f'refresh network cache successful')
        return True

############# subnets #############

    def _list_subnets(self, refresh=False):
        subnets = {}
        cache_file = os.path.join(self._get_cache_path(), 'subnets')
        if refresh or not os.path.exists(cache_file):
            for s in self.conn.network.subnets():
                s_dict = s.to_dict()
                subnets[s_dict['name']] = s_dict
            self._write_cache_file(subnets, cache_file)
        else:
            subnets = self._read_cache_file(cache_file)
        return subnets

    def _print_subnets(self, subnets, subnet_name=None, refresh=False):
        columns = ['name','id', 'cidr', 'dns_nameservers', 'gateway_ip', 'is_dhcp_enabled', 'network_name', 'project_name']
        data = []
        ss = []
        projects = self._list_projects(refresh=refresh)
        networks = self._list_networks(refresh=refresh)
        if subnet_name and subnet_name in subnets:
            ss = [subnets[subnet_name]]
        else:
            ss = subnets.values()
        for s in ss:
            for p in projects.values():
                if s['project_id'] == p['id']:
                    s['project_name'] = p['name']
                    break
            for n in networks.values():
                if s['network_id'] == n['id']:
                    s['network_name'] = n['name']
                    break
            data.append([s['name'], s['id'], s['cidr'], s['dns_nameservers'], s['gateway_ip'], s['is_dhcp_enabled']
                        , s['network_name'], s['project_name']])
        df = pd.core.frame.DataFrame(data, columns=columns)
        df = df.sort_values(by=['name']).reset_index(drop=True)
        df.index = df.index + 1
        print (f'subnets list: (updatetime: {self.update_time})')
        print (df)

    def create_subnet(self, network_name_or_id, cidr=None, ip_version=4,
                      enable_dhcp=True, subnet_name=None, tenant_id=None,
                      allocation_pools=None,gateway_ip=None,
                      dns_nameservers=None,):
        subnet = self.conn.create_subnet(network_name_or_id=network_name_or_id, cidr=cidr, 
                                        ip_version=ip_version, enable_dhcp=enable_dhcp, 
                                        subnet_name=subnet_name, tenant_id=tenant_id,
                                        allocation_pools=allocation_pools,gateway_ip=gateway_ip,
                                        dns_nameservers=dns_nameservers)
        logger.debug(f'create subnet successful, {json.dumps(subnet)}')
        # 更新子网缓存
        self._list_subnets(refresh=True)
        logger.debug(f'refresh subnet cache successful')
        return subnet # Munch

    def print_subnets(self, refresh=False, subnet_name=None):
        subnets = self._list_subnets(refresh=refresh)
        self._print_subnets(subnets, subnet_name, refresh=refresh)

############# server #############
# docs.openstack.org/api-ref/compute/?expanded=list-servers-detail#list-servers

    def _list_servers(self, project_id, refresh=False):
        servers = []
        projects = self._list_projects(refresh=refresh)
        images = self._list_images(refresh=refresh)
        if project_id:
            cache_file = os.path.join(self._get_cache_path(), project_id)
            if refresh or not os.path.exists(cache_file):
                for s in self.conn.compute.servers(all_projects=True, project_id=project_id):
                    s_dict = s.to_dict()
                    for p in projects.values():
                        if s_dict['project_id'] == p['id']:
                            s_dict['project_name'] = p['name']
                            break
                    for i in images.values():
                        if s_dict['image']['id'] == i['id']:
                            s_dict['image_name'] = i['name']
                            break
                    for n in s_dict['addresses'].keys():
                        s_dict['network'] = n
                        s_dict['ip_addr'] = s_dict['addresses'][n][0]['addr']
                    servers.append(s_dict)
                self._write_cache_file(servers,cache_file)
            else:
                servers = self._read_cache_file(cache_file)
        return servers

    def _print_servers(self, servers, name_contain_str):
        columns = ['name','id','status','project_name','image_name','flavor',
                  'hypervisor_hostname','network','ip_addr','created_at']
        data = []
        for s in servers:
            data.append([s['name'], s['id'], s['status'], s['project_name']
                        , s['image_name'], s['flavor']['original_name'], 
                        s['hypervisor_hostname'], s['network'], s['ip_addr'], 
                        s['created_at']])
        df = pd.core.frame.DataFrame(data, columns=columns)
        if name_contain_str:
            df = df.loc[df['name'].str.contains(name_contain_str)]
        df = df.sort_values(by=['project_name', 'name']).reset_index(drop=True)
        df.index = df.index + 1
        # df.to_csv('./serverlist.csv', encoding = "gbk")
        print (f'servers list: (updatetime: {self.update_time})')
        print (df)

    def create_server(self, image_name, flavor_name, project_name, network_name, server_name, **kwargs):
        image_dict = self._list_images()[image_name]
        flavor_dict = self._list_flavors()[flavor_name]
        network_dict = self._list_networks()[network_name]
        server_params = {
            'name': server_name,
            'image': image_dict,
            'flavor': flavor_dict,
            'network': network_dict,
            'wait': True
        }
        server = self.conn.connect_as_project(project=project_name).create_server(**server_params)
        logger.debug(f"create server successful, {json.dumps(server)}")
        return server


    def print_servers(self, project_name=None, refresh=False, name_contains_str=None, **filters):
        servers = []
        project_ids = []
        for p in self._list_projects(refresh=refresh).values():
            if project_name is None or p['name'] == project_name:
                project_ids.append(p['id'])
        for i in project_ids:
            aServers = self._list_servers(project_id=i, refresh=refresh)
            servers += aServers
        self._print_servers(servers, name_contains_str)

    def get_server(self, name_or_id, all_projects=True):
        return self.conn.get_server(name_or_id=name_or_id, all_projects=all_projects)

if __name__ == "__main__": 
    # opst = opst_api()
    # project = opst.create_project(project_name='just_test', description="{'proxy': 'proxy.ly.sh'}")
    # project = opst.delete_project("6c2efa203a2249a6ae849b33491f04ac")
    opst = opst_api(cloud_name='prod_sh_1')
    refresh = True
    # opst.print_projects(refresh=refresh)
    # opst.print_flavors(refresh=refresh)
    # opst.print_images(refresh=refresh)
    # # opst.print_subnets(refresh=refresh)
    opst.print_servers(refresh=refresh, project_name="kyky")
    # opst.print_servers(refresh=refresh)
    # res = opst.get_security_group('default', '0cdda0232237422896331684459360a7')
    # print (res)
    # print (opst.get_security_group('2222', 'a9fc8452b53d48b78ae83f13ce3a8545'))
    # print (datetime.fromtimestamp(os.path.getmtime('/tmp/openstack.log')))
    