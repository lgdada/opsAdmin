import os
import sys

from sqlalchemy import (Column, ForeignKey, Integer, String, UniqueConstraint,
                        create_engine, event)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, sessionmaker

sys.path.append(os.path.dirname(__file__))
from getSettings import setting


config = setting.config
db_file = setting.file_abspath(config.get('database', 'db_file'))

engine = create_engine('sqlite:///' + db_file, convert_unicode=True)
engine.execute("PRAGMA foreign_keys=ON")
Base = declarative_base()

class Projects(Base):
    __tablename__ = 'projects'
    project_id = Column(Integer, primary_key=True, autoincrement=True)
    project = Column(String(50), unique=False, nullable=False)
    group = Column(String(50), unique=False, nullable=False)
    proxy_domain = Column(String(120), unique=False, nullable=False)
    jobmaps = relationship('Actions', cascade="all", backref='projects')

    def __repr__(self):
        return '<project %r, group %r, proxy_domain %r>' % (self.project,self.group,self.proxy_domain)

class Jobs(Base):
    __tablename__ = 'jobs'
    job_id = Column(Integer, primary_key=True, autoincrement=True)
    job_name = Column(String(50), unique=True, nullable=False)
    jobmaps = relationship('Actions', cascade="all", backref='jobs')

    def __repr__(self):
        return '<job_name %r>' % self.job_name

class Actions(Base):
    __tablename__ = 'actions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey('jobs.job_id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.project_id'), default='')
    label = Column(String(50), unique=False, default='')

    __table_args__ = (UniqueConstraint('job_id','project_id','label'),)

    def __repr__(self):
        return '<job_id %r, project_id %r, label %r>' % (self.job_id,self.project_id,self.label)


Base.metadata.create_all(bind=engine)

Session = sessionmaker(engine)
