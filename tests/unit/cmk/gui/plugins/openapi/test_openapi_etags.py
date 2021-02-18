#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2020 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
import pytest
import cmk.gui.config as config


@pytest.fixture(scope='function', name='etags_off')
def etags_off_fixture():
    def _set_config():
        config.rest_api_etag_locking = False

    config.register_post_config_load_hook(_set_config)
    config.initialize()
    yield
    config._post_config_load_hooks.remove(_set_config)
    config.initialize()


def test_openapi_etag_disabled(etags_off, wsgi_app, with_automation_user, with_host):
    username, secret = with_automation_user
    wsgi_app.set_authorization(('Bearer', username + " " + secret))
    base = '/NO_SITE/check_mk/api/v0'

    resp = wsgi_app.call_method(
        'get',
        base + "/objects/host_config/example.com",
        status=200,
    )

    wsgi_app.follow_link(
        resp,
        '.../update',
        base=base,
        status=200,
        params='{"attributes": {"ipaddress": "127.0.0.1"}}',
        content_type='application/json',
    )


def test_openapi_etag_enabled(wsgi_app, with_automation_user, with_host):
    username, secret = with_automation_user
    wsgi_app.set_authorization(('Bearer', username + " " + secret))
    base = '/NO_SITE/check_mk/api/v0'

    resp = wsgi_app.call_method(
        'get',
        base + "/objects/host_config/example.com",
        status=200,
    )

    wsgi_app.follow_link(
        resp,
        '.../update',
        base=base,
        status=428,
        params='{"attributes": {"ipaddress": "127.0.0.1"}}',
        content_type='application/json',
    )
    wsgi_app.follow_link(
        resp,
        '.../update',
        base=base,
        status=412,
        headers={'If-Match': "foo"},
        content_type='application/json',
    )

    resp = wsgi_app.follow_link(
        resp,
        '.../update',
        base=base,
        status=200,
        params='{"attributes": {"ipaddress": "127.0.0.1"}}',
        headers={'If-Match': resp.headers['ETag']},
        content_type='application/json',
    )
    assert resp.json['extensions']['attributes'] == {'ipaddress': '127.0.0.1'}
