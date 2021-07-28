# Designed to be run as 
# 
# docker run -it -p 8000:8000 jupyterhub/oauthenticator

FROM jupyterhub/jupyterhub

# Install oauthenticator from git
RUN python3 -m pip install oauthenticator
RUN python3 -m pip install notebook
# Create oauthenticator directory and put necessary files in it
RUN mkdir /srv/oauthenticator
RUN mkdir /srv/ipython
RUN mkdir /srv/ipython/examples
ADD helloworld.ipynb /srv/ipython/examples/helloworld.ipynb

WORKDIR /srv/oauthenticator
ENV OAUTHENTICATOR_DIR /srv/oauthenticator
ENV OAUTH_CALLBACK_URL http://192.168.1.47:8000/hub/oauth_callback
ENV CLIENT_ID e345bffe48cdad378f58
ENV CLIENT_SECRET 95e3fa5557bbe93d8d2dc6e25d8ca80b7c5aeedf
ADD templates templates
ADD jupyterhub_config.py jupyterhub_config.py
ADD addusers.sh /srv/oauthenticator/addusers.sh
ADD userlist /srv/oauthenticator/userlist
ADD ssl /srv/oauthenticator/ssl
RUN chmod 700 /srv/oauthenticator

RUN ["sh", "/srv/oauthenticator/addusers.sh"]
