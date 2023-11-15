#!/bin/bash
if [ $# -ne 1 ]; then
    echo "Usage:"
    echo "bash script.sh param"
    exit 3
fi

if [ -f /etc/redhat-release ]; then
    if grep -Eqi "release 6." /etc/redhat-release; then
        RELEASE="el6"
    elif grep -Eqi "release 7." /etc/redhat-release; then
        RELEASE="el7"
    elif grep -Eqi "release 8." /etc/redhat-release; then
        RELEASE="el8"
    fi
else
    echo "sorry! operation system is not support!"
    exit 3
fi

P=`rpm -qa zabbix-agent2`
if [[ ! -n $P ]]; then
    eval rpm -ivh $1
fi

if [ $RELEASE == "el6" ]; then
    chkconfig zabbix-agent2 on
    exit 0
fi

systemctl enable zabbix-agent2.service