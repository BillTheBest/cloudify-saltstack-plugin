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


set -e

# for some reason, default cloudify box has broken and missing packages.
sudo apt-get install --yes --fix-broken
sudo apt-get install --yes --fix-missing

# cloudify box doesn't have add-apt-repository command available by default
sudo apt-get install --yes python-software-properties

# install salt.
sudo add-apt-repository --yes ppa:saltstack/salt
sudo apt-get update
sudo apt-get install --yes salt-minion
# salt-minion service is started automatically after apt-get installation,
# but we have to change configuration afterwards (which would require restart)
sudo service salt-minion stop
