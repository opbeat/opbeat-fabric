# -*- coding: utf-8 -*-
import os

from fabric import colors
from fabric.api import (
    task, local, run, put, runs_once, parallel, env, lcd, execute,
)


@task
@runs_once
def build_assets():
    """Clear the assets dir, build assets and transfer them to web servers."""
    with lcd(env.frontend_root):
        local('gulp prod')


@task
def transmit_assets():
    """Upload prepared assets."""
    execute(sync_assets)
    execute(transfer_asset_metadata)


@task
@runs_once
def sync_assets():
    """Does the actual syncing"""
    if not os.path.isfile(os.path.expanduser("~/.s3cfg")):
        print colors.yellow(
            "*** Get your AWS credentials out.\n"
            "They are personal and not shared by the team"
        )
        local("s3cmd --configure")

    local("s3cmd sync {} s3://{}".format(env.asset_build_dir, env.asset_bucket))


@task
@parallel
def transfer_asset_metadata():
    asset_target = os.path.join(env.web_target, 'frontend', 'assets')
    run("mkdir -p %s" % asset_target)
    put(
        os.path.join(env.frontend_root, 'assets', "asset_manifest.json"),
        asset_target
    )
    asset_target = os.path.join(env.web_target, 'frontend', 'static', 'build')
    put(os.path.join(env.asset_build_dir, "app-for-500.css"), asset_target)

    # run("mkdir -p %s" % asset_target + "/build/")
    # put(os.path.join(env.asset_build_dir, 'app.css'),  asset_target + "/build/")
