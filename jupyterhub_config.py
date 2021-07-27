# Configuration file for Jupyter Hub

c = get_config()

c.JupyterHub.log_level = 10
from oauthenticator.github import GitHubOAuthenticator
from jupyterhub.auth import PAMAuthenticator
from jupyterhub.apihandlers.base import APIHandler
import jupyterhub.orm as orm
import json
import asyncio
from datetime import datetime

from async_generator import aclosing
from tornado import  web
from tornado.iostream import StreamClosedError
from jupyterhub.utils import maybe_future

from tornado.escape import url_escape
from tornado import gen
from tornado.httputil import url_concat
from tornado import web

from jupyterhub.handlers.base import BaseHandler

class WrappedGitHubAuthenticator(GitHubOAuthenticator):
    async def authenticate(self,handler,data):
        result = await GitHubOAuthenticator.authenticate(self, handler, data)
        result['name'] = 'github_user_' + result['name']
        return result

class MyAuthenticator(WrappedGitHubAuthenticator,PAMAuthenticator):
    async def add_user(self, user):
        """Hook called whenever a new user is added

        If self.create_system_users, the user will attempt to be created if it doesn't exist.
        """
        user_exists = await maybe_future(self.system_user_exists(user))
        if not user_exists:
            if self.create_system_users:
                await maybe_future(self.add_system_user(user))
                dir = Path('/home/' + user.name + '/examples')
                if not dir.exists():
                    subprocess.check_call(['cp', '-r', '/srv/ipython/examples', '/home/' + user.name + '/examples'])
                    subprocess.check_call(['chown', '-R', user.name, '/home/' + user.name + '/examples'])
            else:
                raise KeyError("User %s does not exist." % user.name)

        await maybe_future(super().add_user(user))

    def authenticate(self,handler,data):
        if data is not None and 'localAuth' in data:
            result =  PAMAuthenticator.authenticate(self,handler,data)
            return result
        else:
            return WrappedGitHubAuthenticator.authenticate(self, handler, data)

class ExtUserAPIHandler(APIHandler):
    def get(self):
        data = [
            self.user_model(u, include_servers=True, include_state=True)
            for u in self.db.query(orm.User)
        ]
        self.write(json.dumps(data))
    async def post(self):
        data = self.get_json_body()
        print(data)
        user = self.find_user(data['name'])
        if user is not None:
            raise web.HTTPError(409, "User %s already exists" % data['name'])
        user = self.user_from_username(data['name'])
        if data:
            self._check_user_model(data)
            if 'admin' in data:
                user.admin = data['admin']
                self.db.commit()
        try:
            await maybe_future(self.authenticator.add_user(user))
        except Exception:
            self.log.error("Failed to create user: %s" % data['name'], exc_info=True)
            # remove from registry
            self.users.delete(user)
            raise web.HTTPError(400, "Failed to create user: %s" % data['name'])

        self.write(json.dumps(self.user_model(user)))
        self.set_status(201)



class ExtloginHandler(BaseHandler):
    """Render the login page."""

    def _render(self, login_error=None, username=None,password=None):
        return self.render_template('external_login.html',
                next=url_escape(self.get_argument('next', default='')),
                username=username,
                login_error=login_error,
                password=password,
                custom_html=self.authenticator.custom_html,
                login_url=self.settings['login_url'],
                authenticator_login_url=url_concat(
                    self.authenticator.login_url(self.hub.base_url),
                    {'next': self.get_argument('next', '')},
                ),
        )
    def get_template(self, name):
        """Return the jinja template object for a given name"""
        print('123123123')
        print(self.settings['jinja2_env'])
        return self.settings['jinja2_env'].get_template(name)
    async def get(self):
        self.statsd.incr('login.request')
        user = self.get_current_user()
        username = self.get_argument('username', default='')
        password = self.get_argument('password',default='')
        print('12312312312')
        print(username,password)
        self.finish(self._render(username=username,password=password))

c.JupyterHub.extra_handlers = [("/external/users", ExtUserAPIHandler),("/external/login",ExtloginHandler)]

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
# def pre_spawn_hook(spawner):
#     username = spawner.user.name
#     # if not username in allowed_users:
#     #     raise ValueError('User Not Registed ')
#     # else:
#     #     dir = Path('/home/' + username + '/examples')
#     #     if not dir.exists():
#     #         subprocess.check_call(['cp', '-r', '/srv/ipython/examples', '/home/' + username + '/examples'])
#     #         subprocess.check_call(['chown','-R',username,'/home/' + username + '/examples'])
#     dir = Path('/home/' + username + '/examples')
#     if not dir.exists():
#         subprocess.check_call(['cp', '-r', '/srv/ipython/examples', '/home/' + username + '/examples'])
#         subprocess.check_call(['chown','-R',username,'/home/' + username + '/examples'])
c.JupyterHub.template_paths = [os.environ['OAUTHENTICATOR_DIR'] + '/templates']
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
