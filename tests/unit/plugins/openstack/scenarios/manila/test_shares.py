# Copyright 2015 Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import ddt
import mock

from rally.plugins.openstack.scenarios.manila import shares
from tests.unit import test


@ddt.ddt
class ManilaSharesTestCase(test.ScenarioTestCase):

    @ddt.data(
        {"share_proto": "nfs", "size": 3},
        {"share_proto": "cifs", "size": 4,
         "share_network": "foo", "share_type": "bar"},
    )
    def test_create_and_delete_share(self, params):
        fake_share = mock.MagicMock()
        scenario = shares.CreateAndDeleteShare(self.context)
        scenario._create_share = mock.MagicMock(return_value=fake_share)
        scenario.sleep_between = mock.MagicMock()
        scenario._delete_share = mock.MagicMock()

        scenario.run(min_sleep=3, max_sleep=4, **params)

        scenario._create_share.assert_called_once_with(**params)
        scenario.sleep_between.assert_called_once_with(3, 4)
        scenario._delete_share.assert_called_once_with(fake_share)

    @ddt.data(
        {},
        {"detailed": True},
        {"detailed": False},
        {"search_opts": None},
        {"search_opts": {}},
        {"search_opts": {"foo": "bar"}},
        {"detailed": True, "search_opts": None},
        {"detailed": False, "search_opts": None},
        {"detailed": True, "search_opts": {"foo": "bar"}},
        {"detailed": False, "search_opts": {"quuz": "foo"}},
    )
    @ddt.unpack
    def test_list_shares(self, detailed=True, search_opts=None):
        scenario = shares.ListShares(self.context)
        scenario._list_shares = mock.MagicMock()

        scenario.run(detailed=detailed, search_opts=search_opts)

        scenario._list_shares.assert_called_once_with(
            detailed=detailed, search_opts=search_opts)

    @ddt.data(
        {"params": {"share_proto": "nfs"}, "new_size": 4},
        {
            "params": {
                "share_proto": "cifs",
                "size": 4,
                "share_network": "foo",
                "share_type": "bar",
                "snapshot_id": "snapshot_foo",
                "description": "foo_description",
                "metadata": {"foo_metadata": "foo"},
                "share_network": "foo_network",
                "share_type": "foo_type",
                "is_public": True,
                "availability_zone": "foo_avz",
                "share_group_id": "foo_group_id"
            },
            "new_size": 8
        }
    )
    @ddt.unpack
    def test_create_and_extend_shares(self, params, new_size):
        size = params.get("size", 1)
        share_group_id = params.get("share_group_id", None)
        snapshot_id = params.get("snapshot_id", None)
        description = params.get("description", None)
        metadata = params.get("metadata", None)
        share_network = params.get("share_network", None)
        share_type = params.get("share_type", None)
        is_public = params.get("is_public", False)
        availability_zone = params.get("availability_zone", None)

        fake_share = mock.MagicMock()
        scenario = shares.CreateAndExtendShare(self.context)
        scenario._create_share = mock.MagicMock(return_value=fake_share)
        scenario._extend_share = mock.MagicMock()

        scenario.run(new_size=new_size, **params)

        scenario._create_share.assert_called_with(
            share_proto=params["share_proto"],
            size=size,
            snapshot_id=snapshot_id,
            description=description,
            metadata=metadata,
            share_network=share_network,
            share_type=share_type,
            is_public=is_public,
            availability_zone=availability_zone,
            share_group_id=share_group_id
        )
        scenario._extend_share.assert_called_with(fake_share, new_size)

    @ddt.data(
        {"params": {"share_proto": "nfs"}, "new_size": 4},
        {
            "params": {
                "share_proto": "cifs",
                "size": 4,
                "share_network": "foo",
                "share_type": "bar",
                "snapshot_id": "snapshot_foo",
                "description": "foo_description",
                "metadata": {"foo_metadata": "foo"},
                "share_network": "foo_network",
                "share_type": "foo_type",
                "is_public": True,
                "availability_zone": "foo_avz",
                "share_group_id": "foo_group_id"
            },
            "new_size": 8
        }
    )
    @ddt.unpack
    def test_create_and_shrink_shares(self, params, new_size):
        size = params.get("size", 2)
        share_group_id = params.get("share_group_id", None)
        snapshot_id = params.get("snapshot_id", None)
        description = params.get("description", None)
        metadata = params.get("metadata", None)
        share_network = params.get("share_network", None)
        share_type = params.get("share_type", None)
        is_public = params.get("is_public", False)
        availability_zone = params.get("availability_zone", None)

        fake_share = mock.MagicMock()
        scenario = shares.CreateAndShrinkShare(self.context)
        scenario._create_share = mock.MagicMock(return_value=fake_share)
        scenario._shrink_share = mock.MagicMock()

        scenario.run(new_size=new_size, **params)

        scenario._create_share.assert_called_with(
            share_proto=params["share_proto"],
            size=size,
            snapshot_id=snapshot_id,
            description=description,
            metadata=metadata,
            share_network=share_network,
            share_type=share_type,
            is_public=is_public,
            availability_zone=availability_zone,
            share_group_id=share_group_id
        )
        scenario._shrink_share.assert_called_with(fake_share, new_size)

    @ddt.data(
        {},
        {"description": "foo_description"},
        {"neutron_net_id": "foo_neutron_net_id"},
        {"neutron_subnet_id": "foo_neutron_subnet_id"},
        {"nova_net_id": "foo_nova_net_id"},
        {"description": "foo_description",
         "neutron_net_id": "foo_neutron_net_id",
         "neutron_subnet_id": "foo_neutron_subnet_id",
         "nova_net_id": "foo_nova_net_id"},
    )
    def test_create_share_network_and_delete(self, params):
        fake_sn = mock.MagicMock()
        scenario = shares.CreateShareNetworkAndDelete(self.context)
        scenario._create_share_network = mock.MagicMock(return_value=fake_sn)
        scenario._delete_share_network = mock.MagicMock()
        expected_params = {
            "description": None,
            "neutron_net_id": None,
            "neutron_subnet_id": None,
            "nova_net_id": None,
        }
        expected_params.update(params)

        scenario.run(**params)

        scenario._create_share_network.assert_called_once_with(
            **expected_params)
        scenario._delete_share_network.assert_called_once_with(fake_sn)

    @ddt.data(
        {},
        {"description": "foo_description"},
        {"neutron_net_id": "foo_neutron_net_id"},
        {"neutron_subnet_id": "foo_neutron_subnet_id"},
        {"nova_net_id": "foo_nova_net_id"},
        {"description": "foo_description",
         "neutron_net_id": "foo_neutron_net_id",
         "neutron_subnet_id": "foo_neutron_subnet_id",
         "nova_net_id": "foo_nova_net_id"},
    )
    def test_create_share_network_and_list(self, params):
        scenario = shares.CreateShareNetworkAndList(self.context)
        fake_network = mock.Mock()
        scenario._create_share_network = mock.Mock(
            return_value=fake_network)
        scenario._list_share_networks = mock.Mock(
            return_value=[fake_network,
                          mock.Mock(),
                          mock.Mock()])
        expected_create_params = {
            "description": params.get("description"),
            "neutron_net_id": params.get("neutron_net_id"),
            "neutron_subnet_id": params.get("neutron_subnet_id"),
            "nova_net_id": params.get("nova_net_id"),
        }
        expected_list_params = {
            "detailed": params.get("detailed", True),
            "search_opts": params.get("search_opts"),
        }
        expected_create_params.update(params)

        scenario.run(**params)

        scenario._create_share_network.assert_called_once_with(
            **expected_create_params)
        scenario._list_share_networks.assert_called_once_with(
            **expected_list_params)

    @ddt.data(
        {},
        {"search_opts": None},
        {"search_opts": {}},
        {"search_opts": {"foo": "bar"}},
    )
    def test_list_share_servers(self, search_opts):
        scenario = shares.ListShareServers(self.context)
        scenario.context = {"admin": {"credential": "fake_credential"}}
        scenario._list_share_servers = mock.MagicMock()

        scenario.run(search_opts=search_opts)

        scenario._list_share_servers.assert_called_once_with(
            search_opts=search_opts)

    @ddt.data(
        {"security_service_type": "fake_type"},
        {"security_service_type": "fake_type",
         "dns_ip": "fake_dns_ip",
         "server": "fake_server",
         "domain": "fake_domain",
         "user": "fake_user",
         "password": "fake_password",
         "description": "fake_description"},
    )
    def test_create_security_service_and_delete(self, params):
        fake_ss = mock.MagicMock()
        scenario = shares.CreateSecurityServiceAndDelete(self.context)
        scenario._create_security_service = mock.MagicMock(
            return_value=fake_ss)
        scenario._delete_security_service = mock.MagicMock()
        expected_params = {
            "security_service_type": params.get("security_service_type"),
            "dns_ip": params.get("dns_ip"),
            "server": params.get("server"),
            "domain": params.get("domain"),
            "user": params.get("user"),
            "password": params.get("password"),
            "description": params.get("description"),
        }

        scenario.run(**params)

        scenario._create_security_service.assert_called_once_with(
            **expected_params)
        scenario._delete_security_service.assert_called_once_with(fake_ss)

    @ddt.data("ldap", "kerberos", "active_directory")
    def test_attach_security_service_to_share_network(self,
                                                      security_service_type):
        scenario = shares.AttachSecurityServiceToShareNetwork(self.context)
        scenario._create_share_network = mock.MagicMock()
        scenario._create_security_service = mock.MagicMock()
        scenario._add_security_service_to_share_network = mock.MagicMock()

        scenario.run(security_service_type=security_service_type)

        scenario._create_share_network.assert_called_once_with()
        scenario._create_security_service.assert_called_once_with(
            security_service_type=security_service_type)
        scenario._add_security_service_to_share_network.assert_has_calls([
            mock.call(scenario._create_share_network.return_value,
                      scenario._create_security_service.return_value)])

    @ddt.data(
        {"share_proto": "nfs", "size": 3, "detailed": True},
        {"share_proto": "cifs", "size": 4, "detailed": False,
         "share_network": "foo", "share_type": "bar"},
    )
    def test_create_and_list_share(self, params):
        scenario = shares.CreateAndListShare()
        scenario._create_share = mock.MagicMock()
        scenario.sleep_between = mock.MagicMock()
        scenario._list_shares = mock.MagicMock()

        scenario.run(min_sleep=3, max_sleep=4, **params)

        detailed = params.pop("detailed")
        scenario._create_share.assert_called_once_with(**params)
        scenario.sleep_between.assert_called_once_with(3, 4)
        scenario._list_shares.assert_called_once_with(detailed=detailed)

    @ddt.data(
        ({}, 0, 0),
        ({}, 1, 1),
        ({}, 2, 2),
        ({}, 3, 0),
        ({"sets": 5, "set_size": 8, "delete_size": 10}, 1, 1),
    )
    @ddt.unpack
    def test_set_and_delete_metadata(self, params, iteration, share_number):
        scenario = shares.SetAndDeleteMetadata()
        share_list = [{"id": "fake_share_%s_id" % d} for d in range(3)]
        scenario.context = {"tenant": {"shares": share_list}}
        scenario.context["iteration"] = iteration
        scenario._set_metadata = mock.MagicMock()
        scenario._delete_metadata = mock.MagicMock()
        expected_set_params = {
            "share": share_list[share_number],
            "sets": params.get("sets", 10),
            "set_size": params.get("set_size", 3),
            "key_min_length": params.get("key_min_length", 1),
            "key_max_length": params.get("key_max_length", 256),
            "value_min_length": params.get("value_min_length", 1),
            "value_max_length": params.get("value_max_length", 1024),
        }

        scenario.run(**params)

        scenario._set_metadata.assert_called_once_with(**expected_set_params)
        scenario._delete_metadata.assert_called_once_with(
            share=share_list[share_number],
            keys=scenario._set_metadata.return_value,
            delete_size=params.get("delete_size", 3),
        )
