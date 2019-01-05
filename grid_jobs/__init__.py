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

import collections
import datetime
import http.client
import json

import ldap3

from . import utils

ACCOUNTING_FIELDS = [
    'qname', 'hostname', 'group', 'owner', 'job_name', 'job_number',
    'account', 'priority', 'submission_time', 'start_time', 'end_time',
    'failed', 'exit_status', 'ru_wallclock', 'ru_utime', 'ru_stime',
    'ru_maxrss', 'ru_ixrss', 'ru_ismrss', 'ru_idrss', 'ru_isrss', 'ru_minflt',
    'ru_majflt', 'ru_nswap', 'ru_inblock', 'ru_oublock', 'ru_msgsnd',
    'ru_msgrcv', 'ru_nsignals', 'ru_nvcsw', 'ru_nivcsw', 'project',
    'department', 'granted_pe', 'slots', 'task_number', 'cpu', 'mem', 'io',
    'category', 'iow', 'pe_taskid', 'maxvemem', 'arid', 'ar_submission_time',
]

CACHE = utils.Cache()


def tools_from_accounting(days):
    """Get a list of (tool, job name, count, last) tuples for jobs running on
    exec nodes in the last N days."""
    delta = datetime.timedelta(days=days)
    cutoff = int(utils.totimestamp(datetime.datetime.now() - delta))
    jobs = collections.defaultdict(lambda: collections.defaultdict(list))
    files = [
        '/data/project/.system_sge/gridengine/default/common/accounting',
        '/data/project/.system_sge/gridengine/default/common/accounting.1',
    ]
    for f in files:
        try:
            for line in utils.tail_lines(f, 400 * 45000 * days):
                parts = line.split(':')
                job = dict(zip(ACCOUNTING_FIELDS, parts))
                if int(job['end_time']) < cutoff:
                    continue

                tool = job['owner']
                if tool is not None:
                    name = job['job_name']
                    jobs[tool][name].append(int(job['end_time']))
        except FileNotFoundError:
            print(e)

    tools = []
    for tool_name, tool_jobs in jobs.items():
        tool_name = normalize_toolname(tool_name)
        if tool_name is not None:
            for job_name, job_starts in tool_jobs.items():
                tools.append((
                    tool_name,
                    job_name,
                    len(job_starts),
                    max(job_starts)
                ))
    return tools


def gridengine_status():
    """Get a list of (tool, job name, host) tuples for jobs currently running
    on exec nodes."""
    conn = http.client.HTTPSConnection('tools.wmflabs.org')
    conn.request(
        'GET', '/sge-status',
        headers={
            'User-Agent': 'https://tools.wmflabs.org/sge-jobs/'
        }
    )
    res = conn.getresponse().read()
    grid_info = {}
    if res:
        grid_info = json.loads(res.decode('utf-8'))['data']['attributes']

    tools = []
    for host, info in grid_info.items():
        if info['jobs']:
            tools.extend([
                (
                    normalize_toolname(job['job_owner']),
                    job['job_name'],
                    host
                )
                for job in info['jobs'].values()
            ])
    return tools


def normalize_toolname(name):
    if name.startswith('tools.'):
        return name[6:]
    return name  # T168653


def tools_members(tools):
    """
    Return a dict that has members of a tool associated with each tool
    Ex:
    {'musikbot': ['musikanimal'],
     'ifttt': ['slaporte', 'mahmoud', 'madhuvishy', 'ori']}
    """
    tool_to_members = collections.defaultdict(set)
    with utils.ldap_conn() as conn:
        for tool in tools:
            conn.search(
                'ou=servicegroups,dc=wikimedia,dc=org',
                '(cn=tools.{})'.format(tool),
                ldap3.SUBTREE,
                attributes=['member', 'cn'],
                time_limit=5
            )
            for resp in conn.response:
                attributes = resp.get('attributes')
                for member in attributes.get('member', []):
                    tool_to_members[tool].add(utils.uid_from_dn(member))
    return tool_to_members


def get_view_data(days=7, cached=True):
    """Get a structured collection of data about tools that are running on
    grid nodes.

    Return value will be a structure something like:
        {
            'generated': datetime,
            'tools': {
                'tool A': {
                    'jobs': {
                        'job X': {
                            'count': N,
                            'last': datetime,
                        },
                        'job Y': {
                            'count': N,
                            'last': datetime,
                        },
                        ...
                    },
                    'members': [
                        'user A',
                        'user B',
                        ...
                    ]
                },
                ...
            },
        }
    """

    cache_key = 'maindict:days={}'.format(days)
    ctx = CACHE.load(cache_key) if cached else None
    if ctx is None:
        date_fmt = '%Y-%m-%d %H:%M'
        tools = collections.defaultdict(lambda: {
            'jobs': collections.defaultdict(lambda: {
                'count': 0,
                'last': '',
                'active': 0,
            }),
            'members': [],
        })

        for rec in tools_from_accounting(days):
            tools[rec[0]]['jobs'][rec[1]]['count'] += rec[2]
            tools[rec[0]]['jobs'][rec[1]]['last'] = (
                datetime.datetime.fromtimestamp(rec[3]).strftime(date_fmt))

        for rec in gridengine_status():
            tools[rec[0]]['jobs'][rec[1]]['active'] += 1
            tools[rec[0]]['jobs'][rec[1]]['count'] += 1
            tools[rec[0]]['jobs'][rec[1]]['last'] = 'Currently running'

        for key, val in tools_members(tools.keys()).items():
            tools[key]['members'] = list(val)

        ctx = {
            'generated': datetime.datetime.now().strftime(date_fmt),
            'tools': tools,
        }
        CACHE.save(cache_key, ctx)
    return ctx
