#!/bin/sh

useradd -m -s /bin/bash $0
echo  "111111\n111111" | passwd $0
cp -r /srv/ipython/examples /home/$0/examples
chown -R $user /home/$0/examples