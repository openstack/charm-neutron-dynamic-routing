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

import charms_openstack.test_utils as test_utils


class Helper(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.patch_release(dragent.DRAgentCharm.release)
        self.SPEAKER_BINDING = "bgp-speaker"
        self.PROVIDER_BINDING = "provider"


class TestOpenStackDRAgent(Helper):

    def test_render_configs(self):
        self.patch_object(dragent.DRAgentCharm.singleton,
                          "render_with_interfaces")
        dragent.render_configs("interfaces-list")
        self.render_with_interfaces.assert_called_once_with(
            "interfaces-list")

    def test_bgp_speaker_bindings(self):
        self.assertEqual(dragent.bgp_speaker_bindings(),
                         [self.SPEAKER_BINDING])

    def test_speaker_ip(self):
        _ip = "10.0.0.10"
        self.patch_object(dragent.ch_ip, "get_relation_ip")
        self.get_relation_ip.return_value = _ip
        dra = dragent.DRAgentCharm()
        self.assertEqual(dragent.speaker_ip(dra), _ip)
        self.get_relation_ip.assert_called_once_with(self.SPEAKER_BINDING)

    def test_provider_ip(self):
        _ip = "10.200.0.25"
        self.patch_object(dragent.ch_ip, "get_relation_ip")
        self.get_relation_ip.return_value = _ip
        dra = dragent.DRAgentCharm()
        self.assertEqual(dragent.provider_ip(dra), _ip)
        self.get_relation_ip.assert_called_once_with(self.PROVIDER_BINDING)


class TestTransportURLAdapter(Helper):

    def test_transport_url(self):
        _expected = "rabbit://user:pass@10.0.0.50:5672/vhost"
        amqp = mock.MagicMock()
        amqp.relation_name = "amqp"
        amqp.username.return_value = "user"
        amqp.vhost.return_value = "vhost"
        tua = dragent.TransportURLAdapter(amqp)
        tua.vip = None
        tua.password = "pass"
        tua.ssl_port = None

        # Single
        tua.private_address = "10.0.0.50"
        self.assertEqual(tua.transport_url, _expected)

        # Multiple
        _expected = ("rabbit://user:pass@10.200.0.20:5672,"
                     "user:pass@10.200.0.30:5672/vhost")
        amqp.rabbitmq_hosts.return_value = ["10.200.0.20", "10.200.0.30"]
        self.assertEqual(tua.transport_url, _expected)

    def test_port(self):
        _ssl_port = '2765'
        _port = '5672'
        amqp = mock.MagicMock()
        tua = dragent.TransportURLAdapter(amqp)
        # Default Port
        tua.ssl_port = None
        self.assertEqual(tua.port, _port)
        # SSL port
        tua.ssl_port = _ssl_port
        self.assertEqual(tua.port, _ssl_port)


class TestDRAgentCharm(Helper):

    def test_install(self):
        dra = dragent.DRAgentCharm()
        self.patch_object(dragent.charms_openstack.charm.OpenStackCharm,
                          "configure_source")
        self.patch_object(dragent.charms_openstack.charm.OpenStackCharm,
                          "install")
        dra.install()
        self.configure_source.assert_called_once_with()
        self.install.assert_called_once_with()
