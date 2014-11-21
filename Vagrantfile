# -*- mode: ruby -*-
# vi: set ft=ruby :


VAGRANTFILE_API_VERSION = "2"


Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.vm.box_check_update = false

    config.vm.define "salt-master" do |vm|
        vm.vm.box = "ubuntu/trusty64"
        vm.vm.hostname = "salt-master"
        vm.vm.provider "virtualbox" do |vb|
            vb.cpus = 1
            vb.memory = 1024
        end
        vm.vm.network :private_network, ip: "192.168.51.10"
        vm.vm.provision :shell, inline: "apt-get -y update"
        vm.vm.provision :shell, inline: "apt-get -y autoremove chef puppet cloud-init"
        vm.vm.provision :shell, path: "provision_salt_master.sh"
    end

    config.vm.define "cfy-minion" do |vm|
        vm.vm.box = "cloudify-3.1.0-rc1"
        vm.vm.hostname = "cfy-minion"
        vm.vm.provider "virtualbox" do |vb|
            vb.cpus = 2
            vb.memory = 2048
        end
        vm.vm.network :private_network, ip: "192.168.51.11"
        vm.vm.provision :shell, inline: "echo -e '\\n192.168.51.10 salt' | tee -a /etc/hosts"
        vm.vm.provision "shell", privileged: false, inline: "echo '{\n    \"host_ip\": \"localhost\",\n    \"agent_user\": \"vagrant\",\n    \"agent_private_key_path\": \"/home/vagrant/.ssh/id_rsa\"\n}' > ~/cloudify/inputs.json"
    end

end
