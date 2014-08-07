import requests
# from fabric.api import task

from .git import get_deployment_info
from .opbeat import get_opbeat_configuration


# @task
def send_deployment():
    
    org_id, app_id, secret_token = get_opbeat_configuration()
    deployment_info = get_deployment_info()

    description = "Branch: {branch}. Organization: {org_id}."\
    				" App: {app}. Server: {server}".format(
        branch=deployment_info['branch'],
        server=deployment_info['server'],
        org_id=org_id,
        app_id=app_id
    )

    url =  "https://api.newrelic.com/deployments.xml"
    headers = {
        "x-api-key": "bc3c8760db299c358f850c1da56d47c9fa24835fd2501bf",
    }
    data = {
        # "deployment[app_name]": "staging.opbeat.com",
        "deployment[application_id]": "4391011", #TODO get from config
        "deployment[revision]": str(deployment_info['revision']),
        "deployment[description]": str(description),
        "deployment[user]": str(deployment_info['user']),
        # "deployment[changelog]": "many hands make light work TEST",
    }
    response = requests.post(url, data=data, headers=headers)