# -*- coding: utf-8 -*-
from fabric import colors
from fabric.utils import abort
from fabric.api import (
    local, run, settings, cd, lcd, prefix, env, task,
)



def _get_changed_file_list(branch):
    base_branch = 'prod'
    result = local('git diff --name-only origin/{base_branch}..origin/{branch}'
        .format(branch=branch, base_branch=base_branch), capture=True)
    return result.split('\n')

def _get_remote_revision(branch):
    return local(
        "git ls-remote -h origin %s| awk '{print $1}'" % branch, capture=True)


def detect_requirement_changes(branch):
    """Check if we have requirement changes in the deployment"""
    changed_files = _get_changed_file_list(branch)

    relevant_files = [i for i in changed_files if 'requirements' in i] 
    if any(relevant_files):
        print colors.red(
            "WARNING: We have requirement changes in this deployment:",
            bold=True,
        )
        for file in relevant_files:
            print colors.red(file)

def detect_migration_changes(branch):
    """Check if we have migrations in the deployment"""
    changed_files = _get_changed_file_list(branch)

    relevant_files = [i for i in changed_files if 'migrations' in i] 
    if any(relevant_files):
        print colors.red(
            "WARNING: You have migrations in this deployment:",
            bold=True,
        )
        for file in relevant_files:
            print colors.red(file)

def detect_current_branch_prod(branch):
    if branch == 'prod':
        print colors.red(
            "WARNING: Deploying prod branch some checks won't be detected",
            bold=True,
        )

def detect_prod_merged_in(branch):
    """Check that prod has been merged into *branch*"""
    local("git fetch")
    with settings(warn_only=True):
        result = local("git branch -a --no-merged |grep -q prod")
        if not result.return_code:
            print colors.red(
                "*** 'Prod' not MERGED into '%s' (hint: 'git pull origin prod'"
                " or 'ssh-add')" % branch
            )
            abort("Cancelling")

def detect_missing_push(branch):
    remote_rev = _get_remote_revision(branch)
    local_rev = local("git rev-parse HEAD", capture=True)
    if local_rev != remote_rev:
        abort(
            colors.red(
                "There a local commits not in remote (hint: git push).",
                bold=True,
            )
        )

def detect_local_branch_pushed(branch):
    """Check that local *branch* is pushed to remote"""
    remote_rev = _get_remote_revision(branch)
    if not remote_rev:
        abort(
            colors.red(
                "Branch '%s' has not been pushed to remote." % (branch,),
                bold=True,
            )
        )

def detecth_if_deploy_branch_is_is_current(branch):
    """Check that we have *branch* checked out"""
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


def run_local_checks(branch):
    detecth_if_deploy_branch_is_is_current(branch)
    detect_local_branch_pushed(branch)
    detect_missing_push(branch)
    detect_prod_merged_in(branch)
    detect_current_branch_prod(branch)
    detect_requirement_changes(branch)
    detect_migration_changes(branch)

    print colors.green("*** Preflight checks passed", bold=True)
    