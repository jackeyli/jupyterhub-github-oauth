# Configuration file for Jupyter Hub

c = get_config()

c.JupyterHub.log_level = 10
from oauthenticator.github import GitHubOAuthenticator
from jupyterhub.auth import PAMAuthenticator

class WrappedGitHubAuthenticator(GitHubOAuthenticator):
    async def authenticate(self,handler,data):
        result = await GitHubOAuthenticator.authenticate(self, handler, data)
        result['name'] = 'github_user_' + result['name']
        return result

class MyAuthenticator(WrappedGitHubAuthenticator,PAMAuthenticator):
     def authenticate(self,handler,data):
        if data is not None and 'localAuth' in data:
            result =  PAMAuthenticator.authenticate(self,handler,data)
            print('123123123',result)
            return result
        else:
            return WrappedGitHubAuthenticator.authenticate(self, handler, data)

c.JupyterHub.authenticator_class = MyAuthenticator




import os
import sys
import pwd
import subprocess
from pathlib import Path

join = os.path.join

here = os.path.dirname(__file__)
root = os.environ.get('OAUTHENTICATOR_DIR', here)
sys.path.insert(0, root)
allowed_users = set()
def update_allowed_users():
    with open(join(root, 'userlist')) as f:
        for line in f:
            if not line:
                continue
            parts = line.split()
            name = parts[0]
            allowed_users.add(name)
def check_allowed(username):
    update_allowed_users()
    return username in allowed_users
def pre_spawn_hook(spawner):
    username = spawner.user.name
    # if not username in allowed_users:
    #     raise ValueError('User Not Registed ')
    # else:
    #     dir = Path('/home/' + username + '/examples')
    #     if not dir.exists():
    #         subprocess.check_call(['cp', '-r', '/srv/ipython/examples', '/home/' + username + '/examples'])
    #         subprocess.check_call(['chown','-R',username,'/home/' + username + '/examples'])
    dir = Path('/home/' + username + '/examples')
    if not dir.exists():
        subprocess.check_call(['cp', '-r', '/srv/ipython/examples', '/home/' + username + '/examples'])
        subprocess.check_call(['chown','-R',username,'/home/' + username + '/examples'])
c.JupyterHub.template_paths = [os.environ['OAUTHENTICATOR_DIR'] + '/templates']
c.Spawner.pre_spawn_hook = pre_spawn_hook
c.MyAuthenticator.create_system_users = True
c.MyAuthenticator.oauth_callback_url = os.environ['OAUTH_CALLBACK_URL']
c.MyAuthenticator.client_id = os.environ['CLIENT_ID']
c.MyAuthenticator.client_secret = os.environ['CLIENT_SECRET']
# ssl config
ssl = join(root, 'ssl')
keyfile = join(ssl, 'ssl.key')
certfile = join(ssl, 'ssl.cert')
if os.path.exists(keyfile):
    c.JupyterHub.ssl_key = keyfile
if os.path.exists(certfile):
    c.JupyterHub.ssl_cert = certfile
