import sqlalchemy

from logger import logger
from models import Actions, Jobs, Projects, Session


def split_project_name(project_name):
    s = project_name.split("-", 1)
    if len(s) == 1:
        return "Default",s[0]
    else:
        return s[0],s[1]

def update_project_db(project_name, proxy_domain):
    group, project = split_project_name(project_name)
    try:
        with Session.begin() as session:
            result = session.query(Projects).filter(Projects.project == project, Projects.group == group).first()
            if result:
                session.query(Projects).filter(Projects.project == project).\
                    filter(Projects.group == group).update({"proxy_domain": proxy_domain},\
                    synchronize_session="fetch")
                logger.debug(f"{result} 更新到数据库")
            else:
                Project = Projects(project=project, group=group, proxy_domain=proxy_domain)
                session.add(Project)
                logger.info(f"{Project} 添加到数据库")
    except sqlalchemy.exc.IntegrityError as e:
        logger.warn(e)
    except Exception as e:
        logger.error(e)

def del_project_db(project_name):
    group, project = split_project_name(project_name)
    try:
        with Session.begin() as session:
            s = session.query(Projects).filter(Projects.project == project, Projects.group == group).delete()
            if s != 0:
                logger.info(f"project:{project_name} 从数据库中删除")
            else:
                raise Exception(f"删除 project 失败, project_name:{project_name} 不存在")
    except Exception as e:
        logger.error(e)

def query_project_db():
    project_list = []
    try:
        with Session.begin() as session:
            for r in session.query(Projects):
                project_list.append(dict(r.__dict__))
        return project_list
    except Exception as e:
        logger.error(e)

def add_job_db(job_name):
    Job = Jobs(job_name=job_name)
    try:
        with Session.begin() as session:
            session.add(Job)
        logger.info(f"job:{job_name} 添加到数据库")
    except sqlalchemy.exc.IntegrityError as e:
        logger.warn(e)
    except Exception as e:
        logger.error(e)

def query_job_db():
    job_list = []
    try:
        with Session.begin() as session:
            for r in session.query(Jobs):
                job_list.append(dict(r.__dict__))
        return job_list
    except Exception as e:
        logger.error(e)

def del_job_db(job_name):
    try:
        with Session.begin() as session:
            r = session.query(Jobs).filter(Jobs.job_name == job_name).delete()
            if r:
                logger.info(f"job:{job_name} 从数据库中删除")
            else:
                raise Exception(f"删除 job 失败, job:{job_name} 不存在")
    except Exception as e:
        logger.error(e)

def add_action_db(job_name,project_name=None,group=None, label=None):
    try:
        with Session.begin() as session:
            s = session.query(Jobs).filter(Jobs.job_name==job_name).first()
            if s is None:
                raise Exception(f"添加 action 失败, job:{job_name} 不存在")
            else:
                job_id = s.job_id
                project_ids = []
                if project_name:
                    group, project = split_project_name(project_name)
                    p = session.query(Projects.project_id).filter(Projects.project == project, Projects.group == group).first()
                    if p:
                        project_ids.append(p.project_id)
                    else:
                        raise Exception(f"添加 action 失败, project_name:{project_name} 不存在")
                elif group:
                    gs = session.query(Projects.project_id).filter(Projects.group == group).all()
                    for g in gs:
                        project_ids.append(g.project_id)
                else:
                    project_ids.append(None)         
    except Exception as e:
        logger.error(e)

    for project_id in project_ids:
        try:
            with Session.begin() as session:
                action = Actions(job_id=job_id, project_id=project_id, label=label)
                session.add(action)
            logger.info(f"action:{job_name},{project_name},{group},{label} 成功添加到数据库")
        except sqlalchemy.exc.IntegrityError as e:
            logger.warn(e)
        except Exception as e:
            logger.error(e)


def del_action_db(action_id):
    try:
        with Session.begin() as session:
            s = session.query(Actions).filter(Actions.id == action_id).delete()
            if s:
                logger.info(f"action id:{action_id} 从数据库中删除")
            else:
                raise Exception(f"删除 action 失败, id:{action_id} 不存在")
    except Exception as e:
        logger.error(e)

def query_action_db():
    action_list = []
    try:
        with Session.begin() as session:
            for s in session.query(Actions):
                if s.projects:
                    project_name = f'{s.projects.group}-{s.projects.project}'
                else:
                    project_name = ''
                action_list.append({
                    'action_id': s.id,
                    'job_name': s.jobs.job_name,
                    'project_name': project_name,
                    'label': s.label
                })
        return action_list
    except Exception as e:
        logger.error(e)

if __name__ == '__main__':
    # update_project_db("集团-基础","proxy.yygroup.sh")
    # add_job_db("install_zabbix_agent")
    # add_job_db("install_zabbix_agent3")
    # add_job_db("install_zabbix_agent2")
    add_action_db("install_zabbix_agent",project_name=None,group="集团", label=None)
    # print (query_job_db())
    # del_job_db("install_zabbix_agent")
    # delete_project_db("集团-测试")
    # del_action_db(1)
    # query_action_db()
