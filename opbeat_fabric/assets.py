# -*- coding: utf-8 -*-
import json
import os

from fabric import colors
from fabric.api import (
    task, local, run, put, runs_once, parallel, env, lcd, execute, prefix
)
from fabric.context_managers import shell_env

@task
@runs_once
def build_assets():
    """Clear the assets dir, build assets and transfer them to web servers."""
    with lcd(env.frontend_root), shell_env(NODE_ENV=env.environment):
        local('npm run prod')


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

    local("s3cmd --add-header='Cache-Control: public, max-age=86400' --no-preserve sync {} s3://{}".format(env.asset_build_dir, env.asset_bucket))


@task
@parallel
def transfer_asset_metadata():
    asset_target = os.path.join(env.web_target, 'frontend', 'assets')
    run("mkdir -p %s" % asset_target)

    manifest_file = os.path.join(env.frontend_root, 'assets', "asset_manifest.json")
    with open(manifest_file, 'r') as f:
        app_css_name = json.loads(f.read())['app_css'][0]

    asset_target = os.path.join(env.web_target, 'frontend', 'assets')
    put(manifest_file, asset_target)

    app_css_hashed_file = os.path.join(env.frontend_root, app_css_name)
    app_css_generic_file = os.path.join(env.asset_build_dir, "app-for-500.css")

    local("cp %s %s" % (app_css_hashed_file, app_css_generic_file))

    asset_target = os.path.join(env.web_target, 'frontend', 'static', 'build')
    run("mkdir -p %s" % asset_target)
    put(app_css_generic_file, asset_target)

    # run("mkdir -p %s" % asset_target + "/build/")
    # put(os.path.join(env.asset_build_dir, 'app.css'),  asset_target + "/build/")
