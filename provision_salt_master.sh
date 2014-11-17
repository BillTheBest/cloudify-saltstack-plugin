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

file_roots:
    base:
        - /srv/salt
EOF

sudo mkdir /srv/salt

sudo tee -a /srv/salt/top.sls <<EOF
base:
  '*':
    - state1
  'role:jboss':
    - match: grain
    - state2
EOF

sudo tee -a /srv/salt/state1.sls <<EOF
tree:
  pkg.installed
EOF

sudo tee -a /srv/salt/state2.sls <<EOF
/home/vagrant/testfile:
  file.managed:
    - user: vagrant
    - group: vagrant
    - mode: 644
    - contents: This is a salt test file, minions with jboss role should get it.
EOF

sudo service salt-master restart
sudo service salt-api restart
