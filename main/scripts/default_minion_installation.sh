#!/bin/bash


###############################################################################
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
###############################################################################


ubuntu_installation() {

    # for some reason, default cloudify box has broken and missing packages
    sudo apt-get --yes --fix-broken --fix-missing install || exit 1

    # cloudify box doesn't have add-apt-repository command available by default
    which add-apt-repository 1>/dev/null 2>&1 || {
        sudo apt-get update || exit 1
        sudo apt-get --yes --no-install-recommends install python-software-properties || exit 1
    }

    # install salt
    sudo add-apt-repository --yes ppa:saltstack/salt || exit 1
    sudo apt-get update || exit 1
    sudo apt-get --yes --no-install-recommends install salt-minion || exit 1

    # on Ubuntu salt-minion service is started automatically after apt-get
    # installation, but we have to change configuration afterwards
    # (which would require restart)
    sudo service salt-minion stop || true
}


centos_or_redhat_installation() {

    link=http://ftp.linux.ncsu.edu/pub/epel/6/i386/epel-release-6-8.noarch.rpm
    sudo rpm --verbose --upgrade "${link}"
    sudo yum --verbose --assumeyes install salt-minion
    sudo service salt-minion stop || true
    sudo chmod 644 /etc/salt/minion || true
}


OS_TYPE=
OS_DESC=
which lsb_release 1>/dev/null 2>&1
if [ $? -eq 0 ]; then
    OS_DESC="`lsb_release -i`"
    for r in ubuntu; do
        lsb_release -a 2>/dev/null | grep -i "${r}" 1>/dev/null && {
            OS_TYPE="${r}"
            break
        }
    done
    [ -z "${OS_TYPE}" ] && {
        lsb_release="`echo ${OS_DESC} | cut -d: -f2 | xargs`"
        echo "Unsupported LSB release: ${lsb_release}." 1>&2
        exit 1
    }
else
    [ -f /etc/system-release -a -r /etc/system-release ] \
            && OS_DESC="`cat /etc/system-release`"
    if [ -e /etc/centos-release ]; then
        OS_TYPE=centos
    else
        if [ -e /etc/redhat-release ]; then
            OS_TYPE=redhat
        else
            echo -n 'Could not recognise OS type'
            [ -n "${OS_DESC}" ] && echo -n " (${OS_DESC})"
            echo .
        fi
    fi
fi


set -x

case "${OS_TYPE}" in
    ubuntu) ubuntu_installation ;;
    centos|redhat) centos_or_redhat_installation ;;
esac

sudo mkdir -p /etc/salt
sudo touch /etc/salt/minion
