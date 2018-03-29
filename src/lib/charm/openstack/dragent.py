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
# The dragent handlers class

# bare functions are provided to the reactive handlers to perform the functions
# needed on the class.
from __future__ import absolute_import

import collections

import charmhelpers.contrib.network.ip as ch_ip

import charms_openstack.charm
import charms_openstack.adapters as os_adapters

PACKAGES = ['neutron-bgp-dragent', 'neutron-dynamic-routing-common',
            'python-neutron-dynamic-routing']
NEUTRON_DIR = '/etc/neutron/'
NEUTRON_CONF = NEUTRON_DIR + "neutron.conf"
DRAGENT_CONF = NEUTRON_DIR + "bgp_dragent.ini"

OPENSTACK_RELEASE_KEY = ('neutron-dynamic-routing-charm.'
                         'openstack-release-version')

SPEAKER_BINDING = 'bgp-speaker'
PROVIDER_BINDING = 'provider'


# select the default release function
charms_openstack.charm.use_defaults('charm.default-select-release')


def render_configs(interfaces_list):
    """Using a list of interfaces, render the configs and, if they have
    changes, restart the services on the unit.
    """
    # Starting out with just amqp
    try:
        [i for i in interfaces_list]
    except TypeError:
        interfaces_list = [interfaces_list]
    DRAgentCharm.singleton.render_with_interfaces(interfaces_list)


def assess_status():
    """Just call the DRAgentCharm.singleton.assess_status() command to update
    status on the unit.
    """
    DRAgentCharm.singleton.assess_status()


def bgp_speaker_bindings():
    """Speaker bindings for bgp interface

    :return: list of bindings
    """
    return [SPEAKER_BINDING]


@os_adapters.config_property
def provider_ip(cls):
    return ch_ip.get_relation_ip(PROVIDER_BINDING)


@os_adapters.config_property
def speaker_ip(cls):
    return ch_ip.get_relation_ip(SPEAKER_BINDING)


class TransportURLAdapter(os_adapters.RabbitMQRelationAdapter):
    """Add Transport URL to RabbitMQRelationAdapter
    TODO: Move to charms.openstack.adapters
    """

    @property
    def transport_url(self):
        hosts = self.hosts or [self.host]
        if hosts:
            transport_url_hosts = ','.join([
                "{}:{}@{}:{}".format(self.username,
                                     self.password,
                                     host_,
                                     self.port)
                for host_ in hosts])
            return "rabbit://{}/{}".format(transport_url_hosts, self.vhost)

    @property
    def port(self):
        return self.ssl_port or 5672


class DRAgentCharm(charms_openstack.charm.OpenStackCharm):
    """DRAgentCharm provides the specialisation of the OpenStackCharm
    functionality to manage a dragent unit.
    """

    release = 'pike'
    name = 'neutron-dynamic-routing'
    packages = PACKAGES
    default_service = 'neutron-bgp-dragent'
    services = ['neutron-bgp-dragent']

    # Note that the hsm interface is optional - defined in config.yaml
    required_relations = ['amqp']

    adapters_class = os_adapters.OpenStackRelationAdapters
    adapters_class.relation_adapters = {
        'amqp': TransportURLAdapter,
    }

    restart_map = {
        NEUTRON_CONF: services,
        DRAGENT_CONF: services,
    }

    # Package for release version detection
    release_pkg = 'neutron-dynamic-routing-common'

    # Package codename map for barbican-common
    package_codenames = {
        'neutron-dynamic-routing-common': collections.OrderedDict([
            ('11', 'pike'),
            ('12', 'queens'),
            ('13', 'rocky'),
        ]),
    }

    def install(self):
        self.configure_source()
        super().install()

    def get_amqp_credentials(self):
        """Provide the default amqp username and vhost as a tuple.

        :returns (username, host): two strings to send to the amqp provider.
        """
        return (self.config['rabbit-user'], self.config['rabbit-vhost'])

    def states_to_check(self, required_relations=None):
        """Override the default states_to_check() for the assess_status
        functionality so that, if we have to have an HSM relation, then enforce
        it on the assess_status() call.

        If param required_relations is not None then it overrides the
        instance/class variable self.required_relations.

        :param required_relations: [list of state names]
        :returns: [states{} as per parent method]
        """
        if required_relations is None:
            required_relations = self.required_relations
        return super(DRAgentCharm, self).states_to_check(
            required_relations=required_relations)
