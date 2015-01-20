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


import subprocess
import time
import yaml

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError
from cloudify.exceptions import RecoverableError

import utils


def _start_service():
    ctx.logger.info('Starting salt minion')
    subprocess.call(['sudo', 'service', 'salt-minion', 'start'])


def _append_grains(minion_id):
    # grains = a list of pairs
    grains = ctx.node.properties.get('grains', [])
    if grains:
        mgr = utils.instantiate_manager()
        added_grains = []
        for i in grains:
            grain = i.keys()[0]
            value = i.values()[0]
            response, result = mgr.append_grain(minion_id, grain, value)
            if response.ok:
                added_grains.append((grain, value))
        ctx.logger.info('Using additional grains: {0}.'.format(str(added_grains)))
        response, result = mgr.list_grains(minion_id)
        all_grains = []
        if response.ok:
            all_grains = result[minion_id]
        # TODO: Turn the following into some sort of debug.
        ctx.logger.info('A complete collection of currently used grains grains: {0}.'.format(str(all_grains)))


def _execute_highstate(minion_id):
    mgr = utils.instantiate_manager()

    ctx.logger.info(
        'Executing highstate on minion {0}...'.format(minion_id)
    )
    resp, result = mgr.highstate(minion_id)
    if resp.ok:
        ctx.logger.info('Executed highstate on minion {0}.'.format(minion_id))
    else:
        ctx.logger.error('Got response {0}'.format(resp))
        raise NonRecoverableError(
            'Unable to execute highstate on minion {0}.'.format(minion_id)
        )

    utils.api_log_out(mgr)


@operation
def run(*args, **kwargs):
    utils.validate_properties(ctx.node.properties)
    minion_id = utils.get_minion_id()

    _start_service()
    # note that highstate usually depends on grains.
    _append_grains(minion_id)
    _execute_highstate(minion_id)
