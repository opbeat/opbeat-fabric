import requests
from fabric.api import run, settings, task, cd, env
from .opbeat import get_paths

def send_deployment():
    path, venv = get_paths()
    with settings(warn_only=True), cd(path):
        branch = run('`git rev-parse --abbrev-ref HEAD`')
        revision = run('`git log -n 1 --pretty=format:%H`')
        description = "Branch: {revision}. Server: {server}".format(
            revision=revision, server=env.deployment_server)

    url =  "https://api.newrelic.com/deployments.xml"
    headers = {
        "x-api-key": "bc3c8760db299c358f850c1da56d47c9fa24835fd2501bf",
    }
    data = {
        # "deployment[app_name]": "staging.opbeat.com",
        "deployment[application_id]": "4391011",
        "deployment[revision]": str(revision),
        "deployment[description]": str(description),
        "deployment[changelog]": "many hands make light work TEST",
        "deployment[user]": "Emil Kjer TEST",
    }
    response = requests.post(url, data=data, headers=headers)