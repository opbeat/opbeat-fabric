# -*- coding: utf-8 -*-
from fabric import colors
from fabric.utils import abort
from fabric.api import (
    local, run, settings, cd, lcd, prefix, env, task,
)


def activate_env(venv):
    return 'source %s/bin/activate' % venv


def install_requirements(target, venv_dir):
    print colors.cyan(
        '# Updating requirements %s in %s' % (target, venv_dir), bold=True)

    with cd(target), prefix(env.umask):

        run('yes w | {0}/bin/pip install -r requirements-prod.txt'.format(
            venv_dir))

        # make sure we clean up for the next guy/girl
        run('find {0} -type f ! -perm -g+w -exec chmod g+w {{}} \;'.format(
            venv_dir))




@task
def test(*args):
    """
    Run tests locally.

    To create coverage report, use the "coverage" argument,
    e.g: fab test:coverage
    """
    with lcd(env.local_base_dir):
        if 'coverage' in args:
            args = list(args)
            args.remove('coverage')
            coverage_env = 'WITH_COVERAGE=1 '
        else:
            coverage_env = ''
        args = ' '.join(args)
        local('%spython manage.py test --failfast %s' % (coverage_env, args))
