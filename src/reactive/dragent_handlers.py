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
import charmhelpers.core.hookenv as hookenv

import charms_openstack.charm as charm

# This charm's library contains all of the handler code associated with
# dragent -- we need to import it to get the definitions for the charm.
import charm.openstack.dragent as dragent  # noqa


# Use the charms.openstack defaults for common states and hooks
charm.use_defaults(
    'charm.installed',
    'amqp.connected',
    'config.changed',
    'update-status')


@reactive.when('charm.installed')
def debug():
    if not hookenv.config('debug'):
        return
    for key, value in reactive.get_states().items():
        print(key, value)


# Use for testing with the quagga charm
@reactive.when('endpoint.bgp-speaker.joined')
def publish_bgp_info(endpoint):
    endpoint.publish_info(asn=hookenv.config('asn'),
                          passive=True)


@reactive.when('amqp.connected')
def setup_amqp_req(amqp):
    """Use the amqp interface to request access to the amqp broker using our
    local configuration.
    """
    amqp.request_access(username='dragent',
                        vhost='openstack')
    dragent.assess_status()


@reactive.when('amqp.available')
def render_stuff(*args):
    """Render the configuration for dyanmic routing when all the interfaces are
    available.
    """
    hookenv.log("about to call the render_configs with {}".format(args))
    dragent.render_configs(args)
    dragent.assess_status()
