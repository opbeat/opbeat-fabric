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


def run_local_checks(branch):
    # Check that we have *branch* checked out
    current_branch = local("git rev-parse --abbrev-ref HEAD", capture=True)
    if current_branch != branch:
        print colors.red(
            'Must be on branch "%s". Current branch is "%s"' % (
                branch,
                current_branch,
            ),
            bold=True,
        )
        abort("Cancelling")

    # Check that local *branch* is pushed to remote
    remote_rev = local(
        "git ls-remote -h origin %s| awk '{print $1}'" % branch, capture=True)
    if not remote_rev:
        abort(
            colors.red(
                "Branch '%s' has not been pushed to remote." % (branch,),
                bold=True,
            )
        )

    local_rev = local("git rev-parse HEAD", capture=True)
    if local_rev != remote_rev:
        abort(
            colors.red(
                "There a local commits not in remote (hint: git push).",
                bold=True,
            )
        )

    # Check that prod has been merged into *branch*
    local("git fetch")
    with settings(warn_only=True):
        result = local("git branch -a --no-merged |grep -q prod")
        if not result.return_code:
            print colors.red(
                "*** 'Prod' not MERGED into '%s' (hint: 'git pull origin prod'"\
                " or 'ssh-add')" % branch
            )
            abort("Cancelling")
    
    
    base_branch = 'prod'
    result = local('git diff --name-only origin/{base_branch}..origin/{branch}'
        .format(branch=branch, base_branch=base_branch), capture=True)
    result_list = result.split('\n')
    
    # Check if we have migrations in the deployment
    if any(i for i in result_list if 'migrations' in i):
        print colors.red(
            "WARNING: There are more than one migration in this deployment:",
            bold=True,
        )
        print colors.red(result)

    # Check if we have requirement changes in the deployment
    if any(i for i in result_list if 'requirements' in i):
        print colors.red(
            "WARNING: We have requirement changes in this deployment:",
            bold=True,
        )
        print colors.red(result)

    print colors.green("*** Preflight checks passed", bold=True)


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
