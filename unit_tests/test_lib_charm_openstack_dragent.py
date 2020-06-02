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

    def get_os_codename(self):
        self.patch_object(dragent.DRAgentCharm.singleton,
                          "get_os_codename_package")
        dragent.get_os_codename()
        self.get_os_codename_package.assert_called_once_with(
            dragent.DRAgentCharm.singleton.release_pkg,
            dragent.DRAgentCharm.singleton.package_codenames)

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

    def test_bgp_speaker_bindings(self):
        dra = dragent.DRAgentCharm()
        self.assertEqual(dra.bgp_speaker_bindings(),
                         [dragent.SPEAKER_BINDING])

    def test_get_os_codename(self):
        dra = dragent.DRAgentCharm()
        codename = 'codename'
        with mock.patch('charms_openstack.charm.OpenStackCharm.'
                        'get_os_codename_package',
                        return_value=codename) as mock_get_os_codename:
            self.assertEquals(dra.get_os_codename(), codename)
        mock_get_os_codename.assert_called_with(
            dra.release_pkg, dra.package_codenames
        )

    def test_disable_services(self):
        dra = dragent.DRAgentCharm()
        with mock.patch('charmhelpers.core.host.service') as mock_service:
            dra.disable_services()
        calls = [
            mock.call(action, svc)
            for action in ('disable', 'stop')
            for svc in dra.services
        ]
        mock_service.assert_has_calls(calls)

    def test_enable_services(self):
        dra = dragent.DRAgentCharm()
        with mock.patch('charmhelpers.core.host.service') as mock_service:
            dra.enable_services()
        calls = [
            mock.call(action, svc)
            for action in ('enable', 'start')
            for svc in dra.services
        ]
        mock_service.assert_has_calls(calls)

    def test_db_migration_overrides_base_class(self):
        dra = dragent.DRAgentCharm()
        with mock.patch(
                'charms_openstack.charm.OpenStackCharm.'
                'do_openstack_upgrade_db_migration') as base_db_migrate:
            dra.do_openstack_upgrade_db_migration()
        base_db_migrate.assert_not_called()
