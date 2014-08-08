import requests
from fabric.api import task, cd, prefix, run, env

from .git import update_env_deployment_info
from .opbeat import get_opbeat_configuration, get_paths
from .utils import activate_env


def update_env_new_relic_configuration():
    """Set New Relic specific configurations in env"""
    #TODO refactor this when the new settings are available
    path, venv = get_paths()
    with prefix(activate_env(venv)), cd(path):
        out = run(
            'python -c "'
            'from webapp import settings;'
            "print settings.NEW_RELIC_APP_ID,"
            " settings.NEW_RELIC_API_ID"
            '"',
        )
        new_relic_app_id, new_relic_api_id = out.split(' ')
        env.new_relic_app_id = new_relic_app_id
        env.new_relic_api_id = new_relic_api_id

@task
def send_deployment(branch='prod'):
    """Send deployment information to New Relic"""
    update_env_new_relic_configuration()
    update_env_deployment_info()

    org_id, app_id, secret_token = get_opbeat_configuration()

    description = "Branch: {branch}. Revision: {revision}."\
        " Organization: {org_id}. App: {app_id}. Server: {server}".format(
        branch=branch,
        server=env.deployment_server,
        org_id=org_id,
        app_id=app_id,
        revision=env.git_revision
    )

    url =  "https://api.newrelic.com/deployments.xml"
    headers = {
        "x-api-key": env.new_relic_api_id,
    }
    data = {
        "deployment[application_id]": env.new_relic_app_id,
        "deployment[description]": description,
        "deployment[user]": env.git_user,
    }
    response = requests.post(url, data=data, headers=headers)
