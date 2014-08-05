# -*- coding: utf-8 -*-
from fabric.api import cd, env, run, prefix, task

from opbeat_fabric.utils import activate_env


@task
def migrate():
    """Runs migrations"""
    with cd(env.web_target), prefix(activate_env(env.web_venv)):
        run('python manage.py migrate')


@task
def collectstatic():
    """Runs collectstatic"""
    with prefix(activate_env(env.web_venv)), cd(env.web_target):
        run('python manage.py collectstatic --noinput')
