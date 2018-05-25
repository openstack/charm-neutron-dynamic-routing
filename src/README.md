# Overview

This charm provides the BGP speaker, dynamic routing agent, feature for OpenStack

# Charm Usage

Neutron dynamic routing relies on services from the rabbitmq-server charm and assumes a functioning neutron stack:

    # The neutron-dynamic-routing charm only requires a relationship to rabbitmq-server
    juju deploy neutron-dynamic-routing
    juju deploy rabbitmq-server
    juju add-relation neutron-dynamic-routing rabbitmq-server

    # For minimum functionality a full neutron stack is required:
    juju deploy keystone
    juju deploy neutron-api
    juju deploy percona-cluster
    juju add-relation keystone percona-cluster
    juju add-relation keystone neutron-api
    juju add-relation neutron-api percona-cluster
    juju add-relation neutron-api rabbitmq-server

NOTE: This charm supports OpenStack versions Pike or newer.  Specify version
      to install using the openstack-origin and source configuration options.

# Feature Usage

For utilizing the dynamic routing feature of OpenStack see upstream documentation for [neutron dynamic routing](https://docs.openstack.org/neutron-dynamic-routing/latest/).

# Bugs

Please report bugs on [Launchpad](https://bugs.launchpad.net/charm-neutron-dynamic-routing/+filebug).

For general questions please refer to the OpenStack [Charm Guide](https://docs.openstack.org/charm-guide/latest/).
