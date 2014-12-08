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


from cloudify import ctx
from cloudify.decorators import operation

from validation import validate_context


@operation
def run(*args, **kwargs):
    validate_context(ctx.node.properties)
    ctx.logger.info('Nothing to do.  We do not stop salt-minion service '
                    'because there may be multiple minions running on '
                    'the same machine.')
