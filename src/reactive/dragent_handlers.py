# Copyright 2018 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# this is just for the reactive handlers and calls into the charm.
from __future__ import absolute_import

import charms.reactive as reactive

import charms_openstack.charm as charm

# This charm's library contains all of the handler code associated with
# dragent -- we need to import it to get the definitions for the charm.
import charm.openstack.dragent as dragent


# Use the charms.openstack defaults for common states and hooks
charm.use_defaults(
    'charm.installed',
    'config.changed',
    'update-status',
    'upgrade-charm')


@reactive.when('endpoint.bgp-speaker.changed')
def publish_bgp_info(endpoint):
    """Publish BGP information about this unit to interface-bgp peers
    """
    if dragent.get_os_codename() in ['ocata', 'pike']:
        use_16bit_asn = True
    else:
        use_16bit_asn = False
    endpoint.publish_info(passive=True,
                          bindings=dragent.bgp_speaker_bindings(),
                          use_16bit_asn=use_16bit_asn)
    dragent.assess_status()


@reactive.when('amqp.connected')
def setup_amqp_req(amqp):
    """Use the amqp interface to request access to the amqp broker using our
    local configuration.
    """
    amqp.request_access(username='neutron',
                        vhost='openstack')
    dragent.assess_status()


@reactive.when('amqp.available')
def render_configs(*args):
    """Render the configuration for dynamic routing when all the interfaces are
    available.
    """
    dragent.upgrade_if_available(args)
    dragent.render_configs(args)
    dragent.assess_status()
