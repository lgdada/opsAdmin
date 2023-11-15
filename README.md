mkdir ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/
[install]
trusted-host=mirrors.aliyun.com
EOF

pip3.6 install -U pip==20.2.4

pip3.6 install -r requirements.txt

1、server初始化功能
2、命令行接受处理jms请求
3、集成dns接口


# 数据库
project表： project_id project(项目) group(项目组) proxy_domain(监控代理)
job表：job_id  job_name(监控或服务部署项目名，与role名称对应)
action表：id job_id(外键任务id) project_id(外键项目id) label(根据jumpserver上主机label来关联hosts)


# opsAdmin
管理openstack并将主机添加到jumpserver
创建：项目、虚拟机
查看：openstack所有资源信息

## 创建项目
- 读配置文件创建
- 创建项目、网络、子网
- 更新数据到project表

## 创建虚拟机
- 创建虚拟机
- 推送到jumpserver

# jobConsole
- 操作数据库
- 定义job
- 定义action

# 执行job
进入jobs目录，通过inventoryJumpserver.py脚本动态清单(关联主机)执行相关任务