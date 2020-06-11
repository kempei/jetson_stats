# -*- coding: UTF-8 -*-
# This file is part of the jetson_stats package (https://github.com/rbonghi/jetson_stats or http://rnext.it).
# Copyright (c) 2019 Raffaello Bonghi.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
# TODO temporary commented: import stat
from multiprocessing import Process, Queue
from multiprocessing.managers import BaseManager
# TODO temporary commented: from  grp import getgrnam
from .tegrastats import Tegrastats
# Load queue library for python 2 and python 3
try:
    import queue
except ImportError:
    import Queue as queue

PIPE_JTOP_STATS = '/tmp/jtop_stats'
PIPE_JTOP_CTRL = '/tmp/jtop_ctrl'
PIPE_JTOP_USER = 'jetson_stats'
AUTHKEY = 'aaabbcc'


class CtrlManager(BaseManager):

    def __init__(self, authkey=AUTHKEY):
        super(CtrlManager, self).__init__(address=(PIPE_JTOP_CTRL), authkey=authkey)

    def get_queue(self):
        pass


class StatsManager(BaseManager):

    def __init__(self, authkey=AUTHKEY):
        super(StatsManager, self).__init__(address=(PIPE_JTOP_STATS), authkey=authkey)

    def stats(self):
        pass


class JtopServer(Process):

    def __init__(self, timeout=1):
        self.q = Queue()
        self.stats = {}
        super(JtopServer, self).__init__()
        # try:
        #    gid = getgrnam(JtopServer.PIPE_JTOP_USER).gr_gid
        # except KeyError:
        # TODO: Check how to be writeable only from same group
        # raise Exception("Group jetson_stats does not exist!")
        #    print("Check how to be writeable only from same group")
        #    gid = os.getgid()
        # Remove old pipes if exists
        if os.path.exists(PIPE_JTOP_CTRL):
            print("Remove old pipe {pipe}".format(pipe=PIPE_JTOP_CTRL))
            os.remove(PIPE_JTOP_CTRL)
        if os.path.exists(PIPE_JTOP_STATS):
            print("Remove old pipe {pipe}".format(pipe=PIPE_JTOP_STATS))
            os.remove(PIPE_JTOP_STATS)
        # Register queue manager
        CtrlManager.register('get_queue', callable=lambda: self.q)
        self.controller = CtrlManager()
        # os.chown(JtopServer.PIPE_JTOP_CTRL, os.getuid(), gid)
        # Set mode
        # https://www.tutorialspoint.com/python/os_chmod.htm
        # os.chmod(JtopServer.PIPE_JTOP_CTRL, stat.S_IWOTH)
        # Register stats
        StatsManager.register("stats", self._read_data)
        self.broadcaster = StatsManager()
        self.broadcaster.start()
        # Set mode
        # TODO: Set mode is only readable from all
        # os.chmod(JtopServer.PIPE_JTOP_CTRL, stat.S_IWOTH)
        # Setup tegrastats
        self.tegra = Tegrastats('/usr/bin/tegrastats')
        self.tegra.attach(self.tegra_stats)
        self.counter = 0

    def run(self):
        while True:
            try:
                # Decode control message
                _ = self.q.get(timeout=1)
                # print(out)
                # Run stats
                self.tegra.open(interval=1000)
            except queue.Empty:
                if self.tegra.close():
                    print("tegrastats close")
            except KeyboardInterrupt:
                break

    def open(self):
        # Run the Control server
        self.start()
        s = self.controller.get_server()
        s.serve_forever()

    def close(self):
        print("End Server")
        self.broadcaster.shutdown()

    def tegra_stats(self, stats):
        print("stats")
        # Update stats
        self.stats_sync = self.broadcaster.stats()
        self.stats_sync.update(stats)
        self.counter += 1

    def _read_data(self):
        return self.stats

    def __call__(self):
        return self
# EOF
