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


import setuptools

import main


_REQUIREMENTS_FILE = 'requirements.txt'
_README_FILE = 'README.md'
_LICENSE_FILE = 'LICENSE'
_PACKAGE_DATA = {
        '': ['utility/default_minion_installation.sh']
    }


with open(_LICENSE_FILE) as f:
    _LICENSE = f.read().strip()
with open(_README_FILE) as f:
    _README = f.read().strip()
with open(_REQUIREMENTS_FILE) as f:
    _REQUIREMENTS = f.read().strip().split()


setuptools.setup(
        name=main.PLUGIN_NAME,
        version=main.PLUGIN_VERSION,
        author=main.PLUGIN_AUTHOR,
        author_email=main.PLUGIN_EMAIL,
        license=_LICENSE,
        description=main.__doc__,
        dependency_links=[
            'git+https://github.com/cloudify-cosmo/cloudify-rest-client@3.1rc1#egg=cloudify-rest-client==3.1rc1',
            'git+https://github.com/cloudify-cosmo/cloudify-plugins-common@3.1rc1#egg=cloudify-plugins-common==3.1rc1'
        ],
        long_description=_README,
        packages=setuptools.find_packages(),
        install_requires=_REQUIREMENTS,
        package_data=_PACKAGE_DATA,
        zip_safe=False
    )
