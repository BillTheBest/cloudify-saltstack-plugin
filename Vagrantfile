# -*- mode: ruby -*-
# vi: set ft=ruby :


VAGRANTFILE_API_VERSION = "2"


MASTER_BOX_NAME = "cloudify3.1rc1"
MINION_BOX_NAME = "cloudify3.1rc1"

MASTER_CPUS = 1
MASTER_MEMORY = 1024

MINION_CPUS = MASTER_CPUS
MINION_MEMORY = MASTER_MEMORY
MINIONS = []
#             host name | machine cpus | machine memory | machine private ip
MINIONS.push(["minion1",  MINION_CPUS,   MINION_MEMORY,   "192.168.50.11"])
MINIONS.push(["minion2",  MINION_CPUS,   MINION_MEMORY,   "192.168.50.12"])


Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.vm.box_check_update = false

    config.vm.define "master", primary: true do |vm|
        vm.vm.box = "#{MASTER_BOX_NAME}"
        vm.vm.hostname = "master"
        vm.vm.provider "virtualbox" do |vb|
            vb.cpus = "#{MASTER_CPUS}"
            vb.memory = "#{MASTER_MEMORY}"
        end
        vm.vm.network :private_network, ip: "192.168.50.10"
        vm.vm.provision :shell, path: "provision_salt_master.sh"
    end

    MINIONS.each_index do |i|
        config.vm.define "#{MINIONS[i][0]}" do |vm|
            vm.vm.box = "#{MINION_BOX_NAME}"
            vm.vm.hostname = "#{MINIONS[i][0]}"
            vm.vm.provider "virtualbox" do |vb|
                vb.cpus = "#{MINIONS[i][1]}"
                vb.memory = "#{MINIONS[i][2]}"
            end
            vm.vm.network :private_network, ip: "#{MINIONS[i][3]}"
            vm.vm.provision "shell", privileged: false, inline: "echo '{\n    \"host_ip\": \"localhost\",\n    \"agent_user\": \"vagrant\",\n    \"agent_private_key_path\": \"/home/vagrant/.ssh/id_rsa\"\n}' > ~/cloudify/inputs.json"
        end
    end
end
