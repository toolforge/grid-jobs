#!/usr/bin/env python2
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

import traceback

import flask
import toolforge

import grid_jobs

app = flask.Flask(__name__)

toolforge.set_user_agent('sge-jobs')


@app.route('/')
def home():
    return duration(7)


@app.route('/days/<int:days>')
def duration(days):
    try:
        cached = 'purge' not in flask.request.args
        gd = grid_jobs.get_view_data(days=days, cached=cached)
        ctx = {
            'days': days,
            'generated': gd['generated'],
            'tools': {},
            'tools_count': len(gd['tools']),
            'total_seen': 0,
            'total_active': 0,
        }
        for name, tool in gd['tools'].items():
            ctx['tools'][name] = {
                'seen': sum(j['count'] for j in tool['jobs'].values()),
                'unique': len(tool['jobs'].values()),
                'active': sum(j['active'] for j in tool['jobs'].values()),
            }
            ctx['total_seen'] += ctx['tools'][name]['seen']
            ctx['total_active'] += ctx['tools'][name]['active']
        return flask.render_template('home.html', **ctx)
    except Exception:
        traceback.print_exc()
        raise


@app.route('/tool/<name>')
def tool(name):
    gd = grid_jobs.get_view_data()
    ctx = {
        'tool_name': name,
        'generated': gd['generated'],
    }
    try:
        ctx['tool_data'] = gd['tools'][name]
    except KeyError:
        flask.abort(404)
    return flask.render_template('tool.html', **ctx)


@app.route('/json')
def json_dump():
    cached = 'purge' not in flask.request.args
    return flask.jsonify(
        grid_jobs.get_view_data(days=7, cached=cached)
    )


if __name__ == '__main__':
    app.run()

# vim:sw=4:ts=4:sts=4:et:
