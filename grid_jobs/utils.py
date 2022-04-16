# -*- coding: utf-8 -*-
#
# This file is part of grid-jobs
# Copyright (C) 2017 Bryan Davis and contributors
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division

import datetime
import hashlib
import json
import os
import pwd

import ldap3
import redis


class Cache(object):
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.conn = redis.Redis(host='tools-redis', decode_responses=True)
        u = pwd.getpwuid(os.getuid())
        self.prefix = hashlib.sha1(
            '{}.{}'.format(u.pw_name, u.pw_dir).encode('utf-8')).hexdigest()

    def key(self, val):
        return '%s%s' % (self.prefix, val)

    def load(self, key):
        if self.enabled:
            try:
                return json.loads(self.conn.get(self.key(key)) or '')
            except ValueError:
                return None
        else:
            return None

    def save(self, key, data, expiry=3600):
        if self.enabled:
            real_key = self.key(key)
            self.conn.setex(real_key, expiry, json.dumps(data))


def tail_lines(filename, nbytes):
    """Get lines from last n bytes from the filename as an iterator."""
    with open(filename, 'rb') as f:
        try:
            f.seek(-nbytes, os.SEEK_END)
        except IOError:
            # File got truncated? Start at the front
            f.seek(0, os.SEEK_SET)

        # Ignore first line as it may be only part of a line
        f.readline()

        # We can't simply `return f` as the returned f will be closed
        # Do all the IO within this function
        for line in f:
            yield line.decode('utf-8').rstrip()


def totimestamp(dt, epoch=None):
    """Convert a datetime to unix epoch seconds."""
    # From http://stackoverflow.com/a/8778548/8171
    if epoch is None:
        epoch = datetime.datetime(1970, 1, 1)
    td = dt - epoch
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6


def ldap_conn():
    """
    Return a ldap connection

    Return value can be used as a context manager
    """
    servers = ldap3.ServerPool([
        ldap3.Server('ldap-ro.eqiad.wikimedia.org'),
        ldap3.Server('ldap-ro.codfw.wikimedia.org'),
    ], ldap3.ROUND_ROBIN, active=True, exhaust=True)
    return ldap3.Connection(
        servers, read_only=True, auto_bind=True)


def uid_from_dn(dn):
    keys = dn.split(',')
    uid_key = keys[0]
    uid = uid_key.split('=')[1]
    return uid
