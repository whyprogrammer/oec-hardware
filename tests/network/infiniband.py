#!/usr/bin/env python
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

import os
import argparse

from hwcert.test import Test
from hwcert.command import Command
from rdma import RDMATest


class InfiniBandTest(RDMATest):
    def __init__(self):
        RDMATest.__init__(self)
        self.link_layer = 'InfiniBand'
        self.subtests = [self.test_ip_info, self.test_ibstatus, self.test_ib_link,
                         self.test_icmp, self.test_rdma]
        self.speed = 56000   # Mb/s
        self.target_bandwidth_percent = 0.5

    def test_ib_link(self):
        if 'LinkUp' not in self.phys_state:
            print("[X] Device is not LinkUp.")

        if 'ACTIVE' not in self.state:
            print("[X] Link is not ACTIVE.")

        if 0x0 == self.base_lid:
            print("[X] Fail to get base lid of %s." % self.interface)
            return False
        print("[.] The base lid is %s" % self.base_lid)

        if 0x0 == self.sm_lid:
            print("[X] Fail to get subnet manager lid of %s." % self.interface)
            return False
        print("[.] The subnet manager lid is %s" % self.sm_lid)

        return True

if __name__ == '__main__':
    t = InfiniBandTest()
    t.server_ip = '199.1.37.20'
    t.speed = 10000   # Mb/s

    from hwcert.device import Device
    properties = {
        'DEVPATH': '/devices/pci0000:d7/0000:d7:02.0/0000:d8:00.0/net/ib0',
        'INTERFACE': 'ib0'
    }
    t.device = Device(properties)
    t.interface = t.device.get_property("INTERFACE")
    # t.setup()
    t.test()
