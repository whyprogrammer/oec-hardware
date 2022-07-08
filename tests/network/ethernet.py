#!/usr/bin/env python3
# coding: utf-8

# Copyright (c) 2020 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-04-01

"""ethernet test"""

import os
import argparse

from builtins import input
from hwcompatible.env import CertEnv
from hwcompatible.document import CertDocument
from rdma import RDMATest


class EthernetTest(RDMATest):
    """
    Ethernet Test

    """
    def __init__(self):
        RDMATest.__init__(self)
        self.args = None
        self.name = ""
        self.logpath = ""
        self.cert = None
        self.device = None
        self.config_data = dict()
        self.server_ip = ""
        self.subtests = [self.test_ip_info, self.test_eth_link, self.test_icmp,
                         self.test_udp_tcp, self.test_http]
        self.target_bandwidth_percent = 0.75

    def is_RoCE(self):
        """
        Judge whether ethernet is roce
        :return:
        """
        path_netdev = ''.join(['/sys', self.device.get_property("DEVPATH")])
        path_pci = path_netdev.split('net')[0]
        cmd = "ls %s | grep -q infiniband" % path_pci
        print(cmd)
        return os.system(cmd) == 0

    def setup(self, args=None):
        """
        Initialization before test
        :param args:
        :return:
        """
        self.args = args or argparse.Namespace()
        self.device = getattr(self.args, 'device', None)
        self.interface = self.device.get_property("INTERFACE")
        self.name = self.device.get_name()
        self.logpath = os.path.join(getattr(self.args, "logdir", None), "ethernet-" + self.name + ".log")
        self.show_driver_info()
        self.config_data = getattr(args, "config_data", None)
        if self.config_data:
            self.server_ip = self.config_data.get("server_ip")
            choice = self.config_data.get("if_rdma")
        else:
            print("Failed to test item value from configuration file.")

        if self.is_RoCE():
            if choice.lower() != "y":
                return

            print("[+] Testing RoCE interface %s..." % self.interface)
            self.link_layer = 'Ethernet'
            self.subtests = [self.test_ip_info, self.test_ibstatus,
                             self.test_eth_link, self.test_icmp, self.test_rdma]

    def test(self):
        """
        Test case
        :return:
        """
        if not self.server_ip:
            print("Failed to get server ip from configuration file.")
            return False
        return self.tests()
