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

import collections
import ipaddress

import netifaces

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
BGP_ROUTER_ID_MAPPINGS = 'bgp-router-id-mappings'
BGP_ROUTER_ID_FALLBACK = 'bgp-router-id-fallback'


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


def _parse_unit_router_ids(mappings: str) -> dict[str, str]:
    """Parse the bgp-router-id-mappings option.

    Each whitespace-separated entry must have the form '<unit>:<router-id>'
    with a non-empty unit and router ID, and each unit may be mapped only
    once.

    :param mappings: raw value of the bgp-router-id-mappings option
    :returns: a mapping of unit number to router ID
    :rtype: dict[str, str]
    :raises ValueError: if the option is malformed or maps a unit more than
                        once
    """
    router_ids = {}
    for mapping in mappings.split():
        unit, sep, router_id = mapping.partition(':')
        if not sep or not unit or not router_id:
            raise ValueError(
                '{} entry {!r} is malformed; expected '
                '<unit>:<router-id>'.format(BGP_ROUTER_ID_MAPPINGS, mapping))
        if unit in router_ids:
            raise ValueError(
                '{} has duplicate entries for unit {}'.format(
                    BGP_ROUTER_ID_MAPPINGS, unit))
        router_ids[unit] = router_id
    return router_ids


def _highest_ipv4_address() -> str:
    """Return the highest IPv4 address of any non-loopback interface."""
    addresses = []
    for nic in netifaces.interfaces():
        for entry in netifaces.ifaddresses(nic).get(netifaces.AF_INET, []):
            address = ipaddress.IPv4Address(entry['addr'])
            if not address.is_loopback:
                addresses.append(address)
    return str(max(addresses))


@os_adapters.config_property
def bgp_router_id(cls):
    """Return the BGP router ID for this unit."""
    unit_number = ch_core.hookenv.local_unit().split('/')[-1]
    router_ids = _parse_unit_router_ids(
        ch_core.hookenv.config(BGP_ROUTER_ID_MAPPINGS))
    if unit_number in router_ids:
        return router_ids[unit_number]
    if ch_core.hookenv.config(BGP_ROUTER_ID_FALLBACK) == 'highest':
        return _highest_ipv4_address()
    return provider_ip(cls)


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
            ('16', 'ussuri'),
            ('17', 'victoria'),
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

    @staticmethod
    def _is_valid_bgp_router_id(value: str) -> bool:
        # RFC6286: the BGP router ID must be a 4-octet, unsigned, non-zero
        # integer.
        try:
            return int(ipaddress.IPv4Address(value)) != 0
        except ValueError:
            return False

    def custom_assess_status_check(self):
        """Check that the BGP router IDs are valid and unique."""
        mappings = ch_core.hookenv.config(BGP_ROUTER_ID_MAPPINGS)
        try:
            router_ids = _parse_unit_router_ids(mappings)
        except ValueError as e:
            return 'blocked', str(e)
        if len(set(router_ids.values())) != len(router_ids):
            return 'blocked', '{} values must be unique'.format(
                BGP_ROUTER_ID_MAPPINGS)

        unit_number = ch_core.hookenv.local_unit().split('/')[-1]
        if mappings and unit_number not in router_ids:
            return 'blocked', (
                '{} is set but has no router id for unit {}'.format(
                    BGP_ROUTER_ID_MAPPINGS, unit_number))

        if unit_number in router_ids:
            router_id = router_ids[unit_number]
            source = '{} value {} for unit {}'.format(
                BGP_ROUTER_ID_MAPPINGS, router_id, unit_number)
        else:
            router_id = bgp_router_id(self.__class__)
            source = 'default bgp-router-id {}'.format(router_id)

        if not self._is_valid_bgp_router_id(router_id):
            return 'blocked', (
                '{} is not a 4-octet, unsigned, non-zero integer'.format(
                    source))

        return None, None


class RockyDRAgentCharm(DRAgentCharm):

    release = 'rocky'

    packages = PY3_PACKAGES

    purge_packages = [
        'python-neutron-dynamic-routing',
        'python-memcache',
    ]

    python_version = 3
