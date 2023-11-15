from jmsApi import jms_api
from database import update_project_db

jms = jms_api()
proxy={
    '数据库': "proxy.database.sh",
    '大数据': "proxy.bigdata.sh",
    '龙盈':"proxy.ly.sh",
    '美业':"proxy.my.sh",
    '盈火':"proxy.yh.sh",
    '盈盈':"proxy.yygroup.sh",
    '集团':"proxy.yygroup.sh",
    '绿度':"proxy.bigdata.sh",
    '玖定':"proxy.ly.sh",
}
proxy_domain = ""
for project in jms.get_project_list():
    full_value = project['full_value']
    project_name = full_value.split("/")
    if len(project_name)==3:
        proxy_domain = ""
        project=f'{project_name[1].strip()}-{project_name[2].strip()}'
        # print (project_name[1].strip())
        # print (project_name[1].strip() in proxy.keys())
        if project_name[1].strip() in proxy.keys():
            proxy_domain=proxy[project_name[1].strip()]
        if project_name[2].strip() in proxy.keys():
            proxy_domain=proxy[project_name[2].strip()]
        update_project_db(project,proxy_domain)