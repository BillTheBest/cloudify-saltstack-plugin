name=foo$1

cfy blueprints upload -b $name /vagrant/blueprint.yaml
cfy deployments create -b $name -d $name-deploy
cfy deployments execute -l -d $name-deploy install
