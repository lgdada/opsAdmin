#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import argparse
import os
import sys
from utils.jobMethods import show_jobs, add_job, del_job, show_projects, \
                             show_actions, add_action, del_action, update_project, \
                             del_project

class job_func(object):
    @staticmethod
    def job_add_func(args):
        add_job(args.job_name)

    @staticmethod
    def job_del_func(args):
        del_job(args.job_name)

    @staticmethod
    def job_show_func(args):
        show_jobs()

class action_func(object):
    @staticmethod
    def action_add_func(args):
        add_action(args.job_name,args.project_name,args.group,args.label)

    @staticmethod
    def action_del_func(args):
        del_action(args.id)

    @staticmethod
    def action_show_func(args):
        show_actions()

class project_func(object):
    @staticmethod
    def project_show_func(args):
        show_projects()
    
    @staticmethod
    def project_add_func(args):
        update_project(args.project_name, args.proxy_domain)

    @staticmethod
    def project_del_func(args):
        del_project(args.project_name)

def get_argparse():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='Items',dest='item')
    # job
    subparser_job = subparsers.add_parser('job', help='Manage job database')
    subparser_job_cmds = subparser_job.add_subparsers(title='Methods',dest='method')
    ## job add
    subparser_job_add = subparser_job_cmds.add_parser('add', help='添加job到数据库')
    subparser_job_add.add_argument('--job_name','-j',help='要添加的job名称')
    subparser_job_add.set_defaults(func=job_func.job_add_func)
    ## job del
    subparser_job_del = subparser_job_cmds.add_parser('del', help='删除job')
    subparser_job_del.add_argument('--job_name','-j',help='要删除的job名称')
    subparser_job_del.set_defaults(func=job_func.job_del_func)
    ## job show
    subparser_job_show = subparser_job_cmds.add_parser('show', help='查看配置的job')
    subparser_job_show.set_defaults(func=job_func.job_show_func)

    # action
    subparser_action = subparsers.add_parser('action', help='Manage action database')
    subparser_action_cmds = subparser_action.add_subparsers(title='Methods',dest='method')
    ## action add
    subparser_action_add = subparser_action_cmds.add_parser('add', help='xxx')
    subparser_action_add.add_argument('--job_name','-j',help='添加任务')
    subparser_action_add_group = subparser_action_add.add_mutually_exclusive_group()
    subparser_action_add_group.add_argument('--project_name','-p',help='添加项目')
    subparser_action_add_group.add_argument('--group','-g',help='添加组下面的所有项目')
    subparser_action_add.add_argument('--label','-l',help='关联标签')
    subparser_action_add.set_defaults(func=action_func.action_add_func)
    ## action del
    subparser_action_del = subparser_action_cmds.add_parser('del', help='xxx')
    subparser_action_del.add_argument('--id','-i',help='xxx')
    subparser_action_del.set_defaults(func=action_func.action_del_func)
    ## action show
    subparser_action_show = subparser_action_cmds.add_parser('show', help='xxx')
    subparser_action_show.set_defaults(func=action_func.action_show_func)

    # project
    subparser_project = subparsers.add_parser('project', help='Manage project database')
    subparser_project_cmds = subparser_project.add_subparsers(title='Methods',dest='method')
    ## project show
    subparser_project_show = subparser_project_cmds.add_parser('show', help='xxx')
    subparser_project_show.set_defaults(func=project_func.project_show_func)
    ## project add
    subparser_project_add = subparser_project_cmds.add_parser('add', help='xxx')
    subparser_project_add.add_argument('--project_name','-p',help='xxx')
    subparser_project_add.add_argument('--proxy_domain','-d',help='xxx')
    subparser_project_add.set_defaults(func=project_func.project_add_func)
    ## project del
    subparser_project_del = subparser_project_cmds.add_parser('del', help='xxx')
    subparser_project_del.add_argument('--project_name','-p',help='xxx')
    subparser_project_del.set_defaults(func=project_func.project_del_func)
    return parser

def main():
    parser = get_argparse()
    args = parser.parse_args()

    if 'func' not in args:
        sys.stderr.write('\033[0;31mNo method specified. pass -h or --help for usage\n\033[0m')
        sys.exit(1)
    if args.func(args) == False:
        sys.stderr.write('\033[0;31mError execution. Please check that the parameters are correct!\n\033[0m')
        parser.parse_args([args.item, args.method, '-h'])
        sys.exit(2)
    

if __name__ == "__main__":
    main()