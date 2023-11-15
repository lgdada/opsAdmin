#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import argparse
import os
import sys

from utils.opsMethods import create_project, batch_create_servers, \
    add_assets_by_manaul, print_opst_resource, get_inventory, add_dnsdb_records

class opst_func(object):
    @staticmethod
    def opst_project_func(args):
        if args.method == 'get':
            print_opst_resource(args.resource, refresh=args.refresh, project_name=args.project_name)
        if args.method == 'create':
            create_project(file_path=args.file_path)

    @staticmethod
    def opst_server_func(args):
        if args.method == 'get':
            print_opst_resource(args.resource, refresh=args.refresh,project_name=args.project_name,name_contains_str=args.name_contains_str)
        if args.method == 'create':
            batch_create_servers(item=args.item)
            
    @staticmethod
    def opst_image_func(args):
        if args.method == 'get':
            print_opst_resource(args.resource, refresh=args.refresh, image_name=args.image_name)

    @staticmethod
    def opst_flavor_func(args):
        if args.method == 'get':
            print_opst_resource(args.resource, refresh=args.refresh, flavor_name=args.flavor_name)

    @staticmethod
    def opst_network_func(args):
        if args.method == 'get':
            print_opst_resource(args.resource, refresh=args.refresh, network_name=args.network_name)

    @staticmethod
    def opst_subnet_func(args):
        if args.method == 'get':
            print_opst_resource(args.resource, refresh=args.refresh, subnet_name=args.subnet_name)

class dnsdb_func(object):
    @staticmethod
    def dnsdb_record_func(args):
        if args.method == 'add':
            add_dnsdb_records(args.record_name, args.record_ip, args.file_path, args.manual)
        if args.method == 'delete':
            pass
        if args.method == 'get':
            pass


class SubcommandHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_action(self, action):
        parts = super(argparse.RawDescriptionHelpFormatter, self)._format_action(action)
        if action.nargs == argparse.PARSER:
            parts = "\n".join(parts.split("\n")[1:])
        return parts

def get_argparse():
    # 设置格式
    formatter = lambda prog: SubcommandHelpFormatter(prog,indent_increment=0, max_help_position=20, width=100)
    parser = argparse.ArgumentParser()
    parser.formatter_class = formatter
    inventory_group = parser.add_mutually_exclusive_group() # 互斥组
    inventory_group.add_argument('--list', action='store_true',help='List active servers')
    inventory_group.add_argument('--host', help='List details about the specific host')

    subparsers = parser.add_subparsers(title='Resources',dest='resource')
    # porject
    subparser_porject = subparsers.add_parser('opst_project', help='Manage openstack project')
    subparser_porject.formatter_class = formatter
    subparser_porject_cmds = subparser_porject.add_subparsers(title='Methods',dest='method')
    ## porject get
    subparser_porject_get = subparser_porject_cmds.add_parser('get', help='Get openstack project list')
    subparser_porject_get.add_argument('--name',dest='project_name', help='Input openstack project name')
    subparser_porject_get.add_argument('--refresh', action='store_true', help='Refresh cache')
    subparser_porject_get.set_defaults(func=opst_func.opst_project_func)
    ## porject create
    subparser_porject_create = subparser_porject_cmds.add_parser('create', help='Create openstack project by config file')
    subparser_porject_create.add_argument('--file','-f',dest='file_path', help='Input project config(yaml) path. (defult:settings/newProject.yaml)')
    subparser_porject_create.set_defaults(func=opst_func.opst_project_func)

    # server
    subparser_server = subparsers.add_parser('opst_server', help='Manage openstack server')
    subparser_server.formatter_class = formatter
    subparser_server_cmds = subparser_server.add_subparsers(title='Methods',dest='method')
    ## server get
    subparser_server_get = subparser_server_cmds.add_parser('get', help='Get openstack server list')
    subparser_server_get.add_argument('--project','-p',dest='project_name', help='Search openstack server name by project_name')
    subparser_server_get.add_argument('--name','-n',dest='name_contains_str', help='Search openstack server name by server_name(name_contains_str)')
    subparser_server_get.add_argument('--refresh', action='store_true', help='Refresh cache')
    subparser_server_get.set_defaults(func=opst_func.opst_server_func)
    ## server create
    subparser_server_create = subparser_server_cmds.add_parser('create', help='Create openstack server by config file')
    subparser_server_create.add_argument('--file','-f',dest='file_path', help='Input servers config(yaml) path.(defult:settings/newServers.yaml)')
    subparser_server_create.add_argument('--item','-i',dest='item',required=True, help='which item in config(yaml)')
    subparser_server_create.set_defaults(func=opst_func.opst_server_func)

    # image
    subparser_image = subparsers.add_parser('opst_image', help='Manage openstack image')
    subparser_image.formatter_class = formatter
    subparser_image_cmds = subparser_image.add_subparsers(title='Methods',dest='method')
    ## image get
    subparser_image_get = subparser_image_cmds.add_parser('get', help='Get openstack image list')
    subparser_image_get.add_argument('--name',dest='image_name', help='Input openstack image name')
    subparser_image_get.add_argument('--refresh', action='store_true', help='Refresh cache')
    subparser_image_get.set_defaults(func=opst_func.opst_image_func)

    # flavor
    subparser_flavor = subparsers.add_parser('opst_flavor', help='Manage openstack flavor')
    subparser_flavor.formatter_class = formatter
    subparser_flavor_cmds = subparser_flavor.add_subparsers(title='Methods',dest='method')
    ## flavor get
    subparser_flavor_get = subparser_flavor_cmds.add_parser('get', help='Get openstack flavor list')
    subparser_flavor_get.add_argument('--name', dest='flavor_name',help='Input openstack flavor name')
    subparser_flavor_get.add_argument('--refresh', action='store_true', help='Refresh cache')
    subparser_flavor_get.set_defaults(func=opst_func.opst_flavor_func)

    # network
    subparser_network = subparsers.add_parser('opst_network', help='Manage openstack network')
    subparser_network.formatter_class = formatter
    subparser_network_cmds = subparser_network.add_subparsers(title='Methods',dest='method')
    ## network get
    subparser_network_get = subparser_network_cmds.add_parser('get', help='Get openstack network list')
    subparser_network_get.add_argument('--name', dest='network_name',help='Input openstack network name')
    subparser_network_get.add_argument('--refresh', action='store_true', help='Refresh cache')
    subparser_network_get.set_defaults(func=opst_func.opst_network_func)

    # subnet
    subparser_subnet = subparsers.add_parser('opst_subnet', help='Manage openstack subnet')
    subparser_subnet.formatter_class = formatter
    subparser_subnet_cmds = subparser_subnet.add_subparsers(title='Methods',dest='method')
    ## subnet get
    subparser_subnet_get = subparser_subnet_cmds.add_parser('get', help='Get openstack subnet list')
    subparser_subnet_get.add_argument('--name', dest='subnet_name',help='Input openstack subnet name')
    subparser_subnet_get.add_argument('--refresh', action='store_true', help='Refresh cache')
    subparser_subnet_get.set_defaults(func=opst_func.opst_subnet_func)

    # dnsdb_record
    subparser_record = subparsers.add_parser('dnsdb_record', help='Manage dnsdb record')
    subparser_record.formatter_class = formatter
    subparser_record_cmds = subparser_record.add_subparsers(title='Methods',dest='method')
    ## dnsdb_record get
    subparser_record_get = subparser_record_cmds.add_parser('get', help='Get dnsdb record list')
    subparser_record_get.add_argument('--name','-n', dest='record_name',help='Input dnsdb record name')
    subparser_record_get.set_defaults(func=dnsdb_func.dnsdb_record_func)
    ## dnsdb_record add
    subparser_record_add = subparser_record_cmds.add_parser('add', help='Add dnsdb record')
    record_add_group = subparser_record_add.add_mutually_exclusive_group()
    record_add_group.add_argument('--file','-f', dest='file_path',metavar='<file_path>',help='Input dns records config(yaml) path.(defult:settings/newRecords.yaml)')
    record_add_group.add_argument('--manual',action='store_true',help='Add record by manual')
    record_add_manual = subparser_record_add.add_argument_group(title='Add record by manual')
    record_add_manual.add_argument('--name','-n',dest='record_name',metavar='<record_name>',help='Input dnsdb record name')
    record_add_manual.add_argument('--ip','-i',dest='record_ip',metavar='<record_ip>',help='Input dnsdb record ip')
    subparser_record_add.set_defaults(func=dnsdb_func.dnsdb_record_func) 
    return parser
 

def main():
    parser = get_argparse()
    args = parser.parse_args()

    if args.list or args.host:
        get_inventory(host=args.host)
        sys.exit(0)
    if 'func' not in args:
        sys.stderr.write('\033[0;31mNo method specified. pass -h or --help for usage\n\033[0m')
        sys.exit(1)
    if args.func(args) == False: # 执行定义的方法func
        sys.stderr.write('\033[0;31mError execution. Please check that the parameters are correct!\n\033[0m')
        parser.parse_args([args.item, args.method, '-h'])
        sys.exit(2)
    

if __name__ == "__main__":
    main()
    # opst = opst_api(cloud_name='dev_hz_1')
    # jms = jms_api()
    # opst = opst_api(cloud_name='prod_sh_1')
    # refresh = True
    # create_project(opst)
    # batch_create_servers(opst, 'vms')
    # opst.print_servers(refresh=refresh)
    # print (opst.get_server('123'))
    # add_assets_by_manaul("/tmp/xfsiDN.yaml")

