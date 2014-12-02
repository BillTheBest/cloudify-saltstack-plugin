set -e

echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDXh+bGLllCRjtfY1qnvDS3GZLQBgLk1+P8J+H2xxSruIxIsr77TTo+cVWy9lCt5f5OFCeqWP3vVIj+aND4RQu5fs2Pixkbg4Er83D2h4ySKU4TQlV8PLrY7FScCBCX38tM5vUYXrVk2eN0hhpBCoZTHyDvYzLM0Wsiu2xXqNZpnqVtSeGMlfRoAH+XhUUTVrEfRm2HHb/VpodgXBejDI1aDAvrQGc8qpW5Mp7BdVj70MMa/vFmmIeyMKi4CtqSj/1a54g5FGz+mCdPqiwmX3mExRKqMC3hmqUcw18H7VlTXS5v4319SjuAOTBA6oh5avHjOo+TiX71eYAO/XtuM+Cb vagrant@precise64' >> .ssh/authorized_keys

sudo add-apt-repository --yes ppa:saltstack/salt
sudo apt-get update
sudo apt-get install --yes salt-master salt-api

sudo service salt-master stop
sudo service salt-api stop

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
    - contents: This is a salt test file, minions with jboss role should get it. Trololololol.
EOF

sudo service salt-master start
sudo service salt-api start
