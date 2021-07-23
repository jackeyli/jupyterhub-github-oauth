#!/bin/sh

IFS="
"
for line in `cat userlist`; do
  test -z "$line" && continue
  user=`echo $line | cut -f 1 -d' '`
  echo "existing user $user"
   useradd -m -s /bin/bash $user
   echo  "111111\n111111" | passwd $user 
   cp -r /srv/ipython/examples /home/$user/examples
   chown -R $user /home/$user/examples
done
