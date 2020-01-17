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

import charmhelpers.core as ch_core
import charmhelpers.contrib.network.ip as ch_ip

import charms_openstack.charm
import charms_openstack.adapters as os_adapters

PACKAGES = [
    'neutron-bgp-dragent',
    'neutron-dynamic-routing-common',
    'python-neutron-dynamic-routing',
]

PY3_PACKAGES = [
    'neutron-bgp-dragent',
    'neutron-dynamic-routing-common',
    'python3-neutron-dynamic-routing',
]

NEUTRON_DIR = '/etc/neutron/'
NEUTRON_CONF = NEUTRON_DIR + "neutron.conf"
DRAGENT_CONF = NEUTRON_DIR + "bgp_dragent.ini"

OPENSTACK_RELEASE_KEY = ('neutron-dynamic-routing-charm.'
                         'openstack-release-version')

SPEAKER_BINDING = 'bgp-speaker'
PROVIDER_BINDING = 'provider'


# select the default release function
charms_openstack.charm.use_defaults('charm.default-select-release')


@os_adapters.config_property
def provider_ip(cls):
    """Return the provider binding network IP

    Use the extra binding, provider, to determine the correct provider network
    IP.

    :returns: string IP address
    """

    return ch_ip.get_relation_ip(PROVIDER_BINDING)


@os_adapters.config_property
def speaker_ip(cls):
    """Return the BGP speaker binding network IP

    Use the interface-bgp relation binding, to determine the correct bgp
    network IP.

    :returns: string IP address
    """

    return ch_ip.get_relation_ip(SPEAKER_BINDING)


class DRAgentRelationAdapters(os_adapters.OpenStackRelationAdapters):

    """
    Adapters collection to append specific adapters for Neutron Dynamic Routing
    """
    relation_adapters = {
        'amqp': os_adapters.RabbitMQRelationAdapter,
    }


class DRAgentCharm(charms_openstack.charm.OpenStackCharm):
    """DRAgentCharm provides the specialisation of the OpenStackCharm
    functionality to manage a dragent unit.
    """

    release = 'ocata'
    name = 'neutron-dynamic-routing'
    packages = PACKAGES
    default_service = 'neutron-bgp-dragent'
    services = [default_service]
    required_relations = ['amqp']
    adapters_class = DRAgentRelationAdapters
    group = 'neutron'

    restart_map = {
        NEUTRON_CONF: services,
        DRAGENT_CONF: services,
    }

    # Package for release version detection
    release_pkg = 'neutron-dynamic-routing-common'

    # Package codename map for neutron-dynamic-routing-common
    package_codenames = {
        'neutron-dynamic-routing-common': collections.OrderedDict([
            ('10', 'ocata'),
            ('11', 'pike'),
            ('12', 'queens'),
            ('13', 'rocky'),
            ('14', 'stein'),
            ('15', 'train'),
        ]),
    }

    def install(self):
        """Configure openstack-origin and install packages

        :returns: None
        """

        self.configure_source()
        super().install()

    def do_openstack_upgrade_db_migration(self, *args):
        """Override the default do_openstack_upgrade_db_migration function.
        DRAgentCharm has no database to migrate.

        :returns: None
        """

        pass

    def bgp_speaker_bindings(self):
        """Return BGP speaker bindings for the bgp interface

        :returns: list of bindings
        """
        return [SPEAKER_BINDING]

    def get_os_codename(self):
        """Return OpenStack Codename for installed application

        :returns: OpenStack Codename
        :rtype: str
        """
        return self.get_os_codename_package(
            self.release_pkg,
            self.package_codenames)

    def disable_services(self):
        """Disable services, typically used awaiting required relations."""
        for service in self.services:
            ch_core.host.service('disable', service)
            ch_core.host.service('stop', service)

    def enable_services(self):
        """Enable services, typically used when required relations complete."""
        for service in self.services:
            ch_core.host.service('enable', service)
            ch_core.host.service('start', service)


class RockyDRAgentCharm(DRAgentCharm):

    release = 'rocky'

    packages = PY3_PACKAGES

    purge_packages = [
        'python-neutron-dynamic-routing',
        'python-memcache',
    ]

    python_version = 3
