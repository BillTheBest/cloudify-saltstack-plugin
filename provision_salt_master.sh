set -e

# for some reason, default cloudify box has broken and missing packages.
sudo apt-get install --yes --fix-broken
sudo apt-get install --yes --fix-missing

# cloudify box doesn't have add-apt-repository command available by default
sudo apt-get install --yes python-software-properties

# install salt.
sudo add-apt-repository --yes ppa:saltstack/salt
sudo apt-get update
sudo apt-get install --yes salt-master
sudo apt-get install --yes salt-api

sudo tee -a /etc/salt/master <<EOF
log_level_logfile: info

rest_cherrypy:
    port: 8000
    disable_ssl: True
    webhook_disable_auth: True

external_auth:
    pam:
        vagrant:
            - .*
EOF

sudo service salt-master restart
sudo service salt-api restart
