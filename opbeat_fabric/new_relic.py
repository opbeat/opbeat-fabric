import requests
from fabric.api import task, cd, prefix, run

from .git import get_deployment_info
from .opbeat import get_opbeat_configuration, get_paths
from .utils import activate_env


def get_new_relic_configuration():
    path, venv = get_paths()
    with prefix(activate_env(venv)), cd(path):
        out = run(
            'python -c "'
            'from webapp import settings;'
            "print settings.OPBEAT['NEW_RELIC_APP_ID'],"
            " settings.OPBEAT['NEW_RELIC_API_ID']"
            '"',
        )
        new_relic_app_id, new_relic_api_id = out.split(' ')
        return new_relic_app_id, new_relic_api_id

# @task
def send_deployment(branch='prod'):
    new_relic_app_id, new_relic_api_id = get_new_relic_configuration()
    org_id, app_id, secret_token = get_opbeat_configuration()
    deployment_info = get_deployment_info()

    description = "Branch: {branch}. Revision: {revision}."\
    	" Organization: {org_id}. App: {app_id}. Server: {server}".format(
        branch=branch,
        server=deployment_info['server'],
        org_id=org_id,
        app_id=app_id,
        revision=deployment_info['revision']
    )

    url =  "https://api.newrelic.com/deployments.xml"
    headers = {
        "x-api-key": new_relic_api_id,
    }
    data = {
        # "deployment[app_name]": "staging.opbeat.com",
        "deployment[application_id]": new_relic_app_id,
        "deployment[description]": str(description),
        "deployment[user]": str(deployment_info['user']),
        # "deployment[changelog]": "many hands make light work TEST",
    }
    response = requests.post(url, data=data, headers=headers)
