# -*- coding: utf-8 -*-

from fabric.api import (
    task, run, settings, cd, prefix, env, warn, roles
)

from opbeat_fabric.utils import activate_env


@task
def register_machine(organization_id=None, app_id=None, secret_token=None,
                     server=None, credentials_func=None):
    """Notify Opbeat of the deployment on an individual machine."""
    f = credentials_func or get_opbeat_configuration
    organization_id, app_id, secret_token, server = f(
        organization_id, app_id, secret_token, server
    )
    if not server:
        server = 'https://' + env.deployment_server
    path, venv = get_paths()
    with settings(warn_only=True), cd(path):
        run(
            "curl -v {server}/api/v1/organizations/{org_id}/apps/{app_id}/releases/ "
            '-H "Authorization: Bearer {secret_token}" '
            '-d rev=`git log -n 1 --pretty=format:%H` '
            '-d branch=`git rev-parse --abbrev-ref HEAD` '
            '-d machine=`hostname` '
            '-d status=machine-completed '
            '{flags}'
            .format(
                secret_token=secret_token,
                app_id=app_id,
                org_id=organization_id,
                server=server,
                flags=env.deployment_flags
            )
        )


@task
def register_deployment(organization_id=None, app_id=None, secret_token=None,
                        server=None, credentials_func=None):
    """Notify Opbeat that a deployment has ended."""
    f = credentials_func or get_opbeat_configuration
    organization_id, app_id, secret_token, server = f(
        organization_id, app_id, secret_token, server
    )
    if not server:
        server = 'https://' + env.deployment_server

    path, venv = get_paths()
    with settings(warn_only=True), cd(path):
        run(
            "curl -v {server}/api/v1/organizations/{org_id}/apps/{app_id}/releases/ "
            '-H "Authorization: Bearer {secret_token}" '
            '-d rev=`git log -n 1 --pretty=format:%H` '
            '-d branch=`git rev-parse --abbrev-ref HEAD` '
            '-d status=completed '
            '{flags}'
            .format(
                secret_token=secret_token,
                app_id=app_id,
                org_id=organization_id,
                server=server,
                flags=env.deployment_flags
            )
        )


def get_opbeat_configuration(organization_id=None, app_id=None, secret_token=None, server=None):
    if organization_id is None or app_id is None or secret_token is None:
        path, venv = get_paths()
        with prefix(activate_env(venv)), cd(path):
            out = run(
                'DJANGO_SETTINGS_MODULE=webapp.settings python -c "'
                'from webapp import settings;'
                "print settings.OPBEAT['ORGANIZATION_ID'],"
                " settings.OPBEAT['APP_ID'],"
                " settings.OPBEAT['SECRET_TOKEN'],"
                " settings.OPBEAT.get('SERVERS', [''])[0]"
                '"',
            )
            new_org_id, new_app_id, new_secret_token, new_server = out.split(' ')
            organization_id = organization_id or new_org_id
            app_id = app_id or new_app_id
            secret_token = secret_token or new_secret_token
            server = server or new_server

    return organization_id, app_id, secret_token, server


def get_paths():
    for role in env.effective_roles:
        if hasattr(env, role + '_target'):
            return getattr(env, role + '_target'), getattr(env, role + '_venv')
    warn('No paths for any roles in {} found'.format(env.effective_roles))
    return None, None

