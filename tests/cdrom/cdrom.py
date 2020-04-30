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
import sys
import time
import shutil
import argparse

from hwcert.test import Test
from hwcert.commandUI import CommandUI
from hwcert.command import Command, CertCommandError


class CDRomTest(Test):

    def __init__(self):
        Test.__init__(self)
        self.requirements = ["dvd+rw-tools", "genisoimage", "wodim", "util-linux"]
        self.method = None
        self.device = None
        self.type = None
        self.ui = CommandUI()
        self.test_dir = "/usr/share/doc"

    def setup(self, args=None):
        self.args = args or argparse.Namespace()
        self.device = getattr(args, "device", None)
        self.type = self.get_type(self.device)
        self.get_mode(self.type)

    def test(self):
        if not (self.method and self.device and self.type):
            return False

        if self.method not in dir(self):
            return False

        devname = self.device.get_property("DEVNAME")
        Command("eject %s" % devname).run(ignore_errors=True)
        while True:
            print("Please insert %s disc into %s, then close the tray manually." % (self.type.lower(), devname))
            if self.method == "write_test":
                print("  tips:disc should be new.")
            elif self.method == "read_test":
                print("  tips:disc should not be blank.")
            if self.ui.prompt_confirm("Done well?"):
                break
        Command("eject -t %s" % devname).run(ignore_errors=True)
        print("Waiting media..).")
        time.sleep(20)

        if not getattr(self, self.method)():
            return False
        return True

    def get_type(self, device):
        if not device:
            return None

        bd_types = ["BD_RE",  "BD_R", "BD"]
        dvd_types = ["DVD_RW", "DVD_PLUS_RW", "DVD_R", "DVD_PLUS_R", "DVD"]
        cd_types = ["CD_RW", "CD_R", "CD"]
        for type in bd_types:
            if device.get_property("ID_CDROM_" + type) == "1":
                return type
        for type in dvd_types:
            if device.get_property("ID_CDROM_" + type) == "1":
                return type
        for type in cd_types:
            if device.get_property("ID_CDROM_" + type) == "1":
                return type

        print("Can not find pr)oper test-type for %s." % device.get_name())
        return None

    def get_mode(self, type):
        if not type:
            return

        if "RW" in type or "RE" in type:
            self.method = "rw_test"
        elif "_R" in type:
            self.method = "write_test"
        else:
            self.method = "read_test"

    def rw_test(self):
        try:
            devname = self.device.get_property("DEVNAME")
            Command("umount %s" % devname).run(ignore_errors=True)
            if "BD" in self.type:
                print("Formatting ...")
                sys.stdout.flush()
                Command("dvd+rw-format -format=full %s 2>/dev/null" % devname).echo()
                self.reload_disc(devname)
                sys.stdout.flush()
                return self.write_test()
            elif "DVD_PLUS" in self.type:
                print("Formatting ...")
                sys.stdout.flush()
                Command("dvd+rw-format -force %s 2>/dev/null" % devname).echo()
                self.reload_disc(devname)
                sys.stdout.flush()
                return self.write_test()
            else:
                print("Blanking ...")
                sys.stdout.flush()
                blankCommand = Command("cdrecord -v dev=%s blank=fast" % devname).echo()
                self.reload_disc(devname)
                sys.stdout.flush()
                return self.write_test()
        except CertCommandError as e:
            return False

    def write_test(self):
        try:
            devname = self.device.get_property("DEVNAME")
            Command("umount %s" % devname).run(ignore_errors=True)
            if "BD" in self.type or "DVD_PLUS" in self.type:
                Command("growisofs -Z %s -quiet -R %s" % (devname, self.test_dir)).echo()
                self.reload_disc(devname)
                sys.stdout.flush()
                return True
            else:
                write_opts ="-sao"
                try:
                    command = Command("cdrecord dev=%s -checkdrive" % devname)
                    modes = command.get_str(regex="^Supported modes[^:]*:(?P<modes>.*$)", regex_group="modes", single_line=False, ignore_errors=True)
                    if "TAO" in modes:
                        write_opts="-tao"
                    if "SAO" in modes:
                        write_opts="-sao"
                    flags = command.get_str(regex="^Driver flags[^:]*:(?P<flags>.*$)", regex_group="flags", single_line=False, ignore_errors=True)
                    if "BURNFREE" in flags:
                        write_opts += " driveropts=burnfree"
                except CertCommandError as e:
                    print(e)

                size = Command("mkisofs -quiet -R -print-size %s " % self.test_dir).get_str()
                blocks = int(size)

                Command("mkisofs -quiet -R %s | cdrecord -v %s dev=%s fs=32M tsize=%ss -" % (self.test_dir, write_opts, devname, blocks)).echo()
                self.reload_disc(devname)
                sys.stdout.flush()
                return True
        except CertCommandError as e:
            return False

    def read_test(self):
        try:
            devname = self.device.get_property("DEVNAME")
            if os.path.exists("mnt_cdrom"):
                shutil.rmtree("mnt_cdrom")
            os.mkdir("mnt_cdrom")

            print("Mounting media ...")
            Command("umount %s" % devname).echo(ignore_errors=True)
            Command("mount -o ro %s ./mnt_cdrom" % devname).echo()

            size = Command("df %s | tail -n1 | awk '{print $3}'" % devname).get_str()
            size = int(size)
            if size == 0:
                print("Error: blank disc.")
                Command("umount ./mnt_cdrom").run(ignore_errors=True)
                Command("rm -rf ./mnt_cdrom").run(ignore_errors=True)
                return False

            if os.path.exists("device_dir"):
                shutil.rmtree("device_dir")
            os.mkdir("device_dir")

            print("Copying files ...")
            sys.stdout.flush()
            Command("cp -dpRf ./mnt_cdrom/. ./device_dir/").run()

            print("Comparing files ...")
            sys.stdout.flush()
            return_code = self.cmp_tree("mnt_cdrom", "device_dir")
            Command("umount ./mnt_cdrom").run(ignore_errors=True)
            Command("rm -rf ./mnt_cdrom ./device_dir").run(ignore_errors=True)
            return return_code
        except CertCommandError as e:
            print(e)
            return False

    def cmp_tree(self, dir1, dir2):
        if not (dir1 and dir2):
            print("Error: invalid input dir.")
            return False
        try:
            Command("diff -r %s %s" % (dir1, dir2)).run()
            return True
        except CertCommandError as e:
            print("Error: file comparison failed.")
            return False

    def reload_disc(self, device):
        if not device:
            return False

        print("Reloading the media ... ")
        sys.stdout.flush()
        try:
            Command("eject %s" % device).run()
            print("tray ejected.")
            sys.stdout.flush()
        except:
            pass

        try:
            Command("eject -t %s" % device).run()
            print("tray auto-closed.\n")
            sys.stdout.flush()
        except:
            print("Could not auto-close the tray, please close the tray manually.")
            self.ui.prompt_confirm("Done well?")

        time.sleep(20)
        return True

