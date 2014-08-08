# -*- coding: utf-8 -*-
from __future__ import print_function
import socket
import sys
import time
from fabric.api import task, env, run, cd, execute, sudo

from opbeat_fabric.aws import setup_instance, setup_dns, terminate_instance

WAITING = '|/-\\'


@task
def setup_stage_instance(number):
    name = '{}.stage.opbeat.com'.format(number)
    sys.stdout.flush()
    ec2_conn, instance = setup_instance(name)
    i = 0
    while instance.state == 'pending':
        i = _wait(instance.update, i, prefix='Creating instance... ')
    i = 0
    while not instance.ip_address:
        i = _wait(instance.update, i, prefix='Waiting for IP address... ')
    print('\nGot IP: {}'.format(instance.ip_address))
    print('Setting up DNS record... ')
    route53_conn, zone = setup_dns(name, instance.dns_name)
    i = 0
    while not _is_reachable(name):
        i = _wait(i=i, prefix='Waiting for host to become reachable... ')
    print('\nUpdating hostname')
    execute(set_hostname, name, hosts=[name])
    print('\nUpdating salt')
    execute(update_salt, hosts=[name])


@task
def teardown_stage_instance(number):
    name = '{}.stage.opbeat.com'.format(number)
    print('Terminating {}...'.format(name), end='')
    sys.stdout.flush()
    conn, instance = terminate_instance(name)
    i = 0
    while instance.state != 'terminated':
        i = _wait(instance.update, i, prefix='Terminating {}... '.format(name))


@task
def update_salt():
    status = sudo('service salt-minion status')
    if not 'stop/waiting' in status:
        sudo('service salt-minion stop')
    sudo('supervisorctl stop all')
    with cd('/var/salt/provisioning'):
        sudo('chgrp -R admin .')
        run('git pull')
        sudo('salt-call state.highstate')
    sudo('service salt-minion start')
    sudo('supervisorctl start all')


@task
def set_hostname(name):
    sudo('echo "{}" > /etc/hostname'.format(name))
    sudo('echo "\n127.0.1.1 {}" >> /etc/hosts'.format(name))
    sudo('service hostname restart')


def _wait(func=lambda: None, i=0, prefix=''):
    func()
    print('\r{}{}'.format(prefix, WAITING[i % len(WAITING)]), end='')
    sys.stdout.flush()
    time.sleep(1)
    return i + 1


def _is_reachable(host, port=22):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        return True
    except socket.error:
        return False
    finally:
        s.close()
