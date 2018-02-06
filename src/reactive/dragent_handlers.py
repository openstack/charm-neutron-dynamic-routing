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


@reactive.when('amqp.connected')
def setup_amqp_req(amqp):
    """Use the amqp interface to request access to the amqp broker using our
    local configuration.
    """
    amqp.request_access(username='dragent',
                        vhost='openstack')
    dragent.assess_status()


# Note that because of the way reactive.when works, (which is to 'find' the
# __code__ segment of the decorated function, it's very, very difficult to add
# other kinds of decorators here.  This rules out adding other things into the
# charm args list.  It is also CPython dependent.
@reactive.when('amqp.available')
def render_stuff(amqp):
    """Render the configuration for Barbican when all the interfaces are
    available.
    """
    hookenv.log("about to call the render_configs with {}".format(amqp))
    dragent.render_configs(amqp)
    dragent.assess_status()
