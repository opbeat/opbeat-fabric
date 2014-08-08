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

def update_env_deployment_info():
    path, venv = get_paths()
    with settings(warn_only=True), cd(path):
        env.git_user = str(run('git config user.name'))
        env.git_revision = ("%s" % run('git log -n 1 --pretty=format:%H'))
