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

from __future__ import absolute_import
from __future__ import print_function

import mock

import charm.openstack.dragent as dragent
import reactive.dragent_handlers as handlers

import charms_openstack.test_utils as test_utils


class TestDRAgentHooks(test_utils.TestRegisteredHooks):
    def test_registered_hooks(self):
        # test that the hooks actually registered the relation expressions that
        # are meaningful for this interface: this is to handle regressions.
        # The keys are the function names that the hook attaches to.
        defaults = [
            'charm.installed',
            'config.changed',
            'update-status',
            'upgrade-charm',
        ]
        hook_set = {
            'when': {
                'publish_bgp_info': ('endpoint.bgp-speaker.changed',),
                'setup_amqp_req': ('amqp.connected', ),
                'render_configs': ('amqp.available', ),
                'configure_ssl': ('amqp.available.ssl', ),
                'enable_services': ('config.rendered',),
                'disable_services': ('charm.installed',),
            },
            'when_not': {
                'disable_services': ('config.rendered',),
            },
        }
        self.registered_hooks_test_helper(handlers, hook_set, defaults)


class TestDRAgentHandlers(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.patch_release(dragent.DRAgentCharm.release)
        self.dragent_charm = mock.MagicMock()
        self.patch_object(handlers.charm, 'provide_charm_instance',
                          new=mock.MagicMock())
        self.provide_charm_instance().__enter__.return_value = \
            self.dragent_charm
        self.provide_charm_instance().__exit__.return_value = None

    def test_publish_bgp_info(self):
        _bindings = ['bgp-speaker']
        bgp = mock.MagicMock()
        self.dragent_charm.bgp_speaker_bindings.return_value = _bindings
        handlers.publish_bgp_info(bgp)
        self.dragent_charm.get_os_codename.assert_called()
        bgp.publish_info.assert_called_once_with(passive=True,
                                                 bindings=_bindings,
                                                 use_16bit_asn=False)

    def test_publish_bgp_info_pike(self):
        _bindings = ['bgp-speaker']
        bgp = mock.MagicMock()
        self.dragent_charm.get_os_codename.return_value = 'pike'
        self.dragent_charm.bgp_speaker_bindings.return_value = _bindings
        handlers.publish_bgp_info(bgp)
        self.dragent_charm.get_os_codename.assert_called()
        bgp.publish_info.assert_called_once_with(passive=True,
                                                 bindings=_bindings,
                                                 use_16bit_asn=True)

    def test_setup_amqp_req(self):
        amqp = mock.MagicMock()
        handlers.setup_amqp_req(amqp)
        amqp.request_access.assert_called_once_with(
            username='neutron', vhost='openstack')

    def test_configure_ssl(self):
        handlers.configure_ssl(mock.MagicMock())
        self.dragent_charm.configure_ssl.assert_called_once_with()

    def test_disable_services(self):
        handlers.disable_services()
        self.dragent_charm.disable_services.assert_called_once_with()
        self.dragent_charm.assess_status.assert_called_once_with()

    def test_enable_services(self):
        handlers.enable_services()
        self.dragent_charm.enable_services.assert_called_once_with()
        self.dragent_charm.assess_status.assert_called_once_with()

    def test_render_configs(self):
        self.patch_object(handlers.reactive, 'set_flag')
        amqp = mock.MagicMock()
        handlers.render_configs(amqp)
        self.dragent_charm.upgrade_if_available.assert_called_once_with(
            (amqp,))
        self.dragent_charm.render_with_interfaces.assert_called_once_with(
            (amqp,))
        self.set_flag.assert_called_once_with('config.rendered')
        self.dragent_charm.assess_status.assert_called_once()
