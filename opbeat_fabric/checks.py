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
        return True
    return False


def detect_migration_changes(branch):
    """Check if we have migrations in the deployment"""
    changed_files = _get_changed_file_list(branch)

    relevant_files = [i for i in changed_files if 'migrations' in i] 
    if any(relevant_files):
        print colors.red(
            "WARNING: There are more than one migration in this deployment:",
            bold=True,
        )
        for file in relevant_files:
            print colors.red(file)
        return True
    return False
