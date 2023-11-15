#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os, sys
import pandas as pd

sys.path.append(os.path.dirname(__file__))
from database import add_job_db, query_job_db, del_job_db, \
                    add_action_db, del_action_db, query_action_db, \
                    query_project_db, del_project_db, update_project_db

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

def show_jobs():
    jobs = query_job_db()
    columns = ['job_name','job_id']
    df = pd.core.frame.DataFrame(jobs, columns=columns)
    df = df.sort_values(by=['job_id']).reset_index(drop=True)
    df.index=df.index + 1
    print ('jobs list: ')
    print (df)

def add_job(job_name):
    add_job_db(job_name)

def del_job(job_name):
    del_job_db(job_name)

def show_projects():
    projects = query_project_db()
    columns = ['group','project','proxy_domain']
    df = pd.core.frame.DataFrame(projects, columns=columns)
    df = df.sort_values(by=['group']).reset_index(drop=True)
    df.index=df.index + 1
    df.style.set_properties(**{'text-align': 'left'})
    print ('projects list: ')
    print (df)

def update_project(project_name, proxy_domain):
    update_project_db(project_name, proxy_domain)

def del_project(project_name):
    del_project_db(project_name)

def add_action(job_name,project_name,group,label):
    add_action_db(job_name,project_name,group,label)

def del_action(action_id):
    del_action_db(action_id)

def show_actions():
    actions = query_action_db()
    columns = ['action_id','job_name','project_name', 'label']
    df = pd.core.frame.DataFrame(actions, columns=columns)
    df = df.sort_values(by=['action_id']).reset_index(drop=True)
    df.index=df.index + 1
    print ('actions list: ')
    print (df)
