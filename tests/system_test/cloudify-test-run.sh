set -e
set -x

name=foo$1

cfy blueprints upload -b $name -p /vagrant/blueprint.yaml
cfy deployments create -b $name -d $name-deploy
cfy executions start -d $name-deploy -w install -l
