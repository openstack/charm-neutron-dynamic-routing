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

import charm.openstack.dragent as dragent  # noqa

import charms_openstack.bus
import charms_openstack.charm as charm


charms_openstack.bus.discover()

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
    with charm.provide_charm_instance() as instance:
        if instance.get_os_codename() in ['ocata', 'pike']:
            use_16bit_asn = True
        else:
            use_16bit_asn = False
        endpoint.publish_info(passive=True,
                              bindings=instance.bgp_speaker_bindings(),
                              use_16bit_asn=use_16bit_asn)
        instance.assess_status()


@reactive.when('amqp.connected')
def setup_amqp_req(amqp):
    """Use the amqp interface to request access to the amqp broker using our
    local configuration.
    """
    amqp.request_access(username='neutron',
                        vhost='openstack')
    with charm.provide_charm_instance() as instance:
        instance.assess_status()


@reactive.when('amqp.available.ssl')
def configure_ssl(_amqp):
    with charm.provide_charm_instance() as instance:
        instance.configure_ssl()


@reactive.when('charm.installed')
@reactive.when_not('config.rendered')
def disable_services():
    with charm.provide_charm_instance() as instance:
        instance.disable_services()
        instance.assess_status()


@reactive.when('config.rendered')
def enable_services():
    with charm.provide_charm_instance() as instance:
        instance.enable_services()
        instance.assess_status()


@reactive.when('amqp.available')
def render_configs(*args):
    """Render the configuration for dynamic routing when all the interfaces are
    available.
    """
    with charm.provide_charm_instance() as instance:
        instance.upgrade_if_available(args)
        instance.render_with_interfaces(args)
        reactive.set_flag('config.rendered')
        instance.assess_status()
