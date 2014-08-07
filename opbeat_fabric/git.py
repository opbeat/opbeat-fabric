# -*- coding: utf-8 -*-
from __future__ import print_function
from fabric import colors
from fabric.api import (
    task, local, run, settings, put, runs_once, parallel,
    cd, prefix, env, sudo, lcd, roles, execute
)

from .opbeat import get_paths


def update_code(target, branch):
    print(
        colors.cyan('*** Updating %s branch (%s)' % (target, branch), bold=True)
    )
    run = print
    with prefix(env.umask), cd(target):

        run('git fetch')
        with settings(warn_only=True):
            run('git reset --hard HEAD')
        run('git checkout %s' % branch)
        run('git pull origin  %s' % branch)
        run('find `pwd` -name "*.pyc" -exec rm -f {} \;')

def get_deployment_info():
    path, venv = get_paths()
    with settings(warn_only=True), cd(path):
        data = {
            'user': run('git config user.name'),
            'branch': run('git rev-parse --abbrev-ref HEAD'),
            'revision': run('git log -n 1 --pretty=format:%H'),
            'server': env.deployment_server,
        }
    return data