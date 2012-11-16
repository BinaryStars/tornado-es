# -*- coding: utf-8 -*-

import json

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.ioloop import IOLoop
from urllib import urlencode


class ESConnection(object):

    def __init__(self, host='localhost', port= '9200', io_loop=None):
        self.io_loop = io_loop or IOLoop.instance()
        self.host = host
        self.port = port
        self.client = AsyncHTTPClient(self.io_loop)

    def create_path(self, method, **kwargs):
        index = kwargs.get('index', '_all')
        type_ = '/' + kwargs.get('type') if kwargs.has_key('type') else ''
        size = kwargs.get('size', 10)
        page = kwargs.get('page', 1)
        from_ = (page-1)*size
        routing = kwargs.get('routing', '')
        jsonp_callback = kwargs.get('jsonp_callback', '')
        parameters = {'from': from_, 'size': size}
        if routing:
            parameters["routing"] = routing
        path = "/%(index)s%(type)s/_%(method)s?%(querystring)s%(jsonp_callback)s" % {
                    "querystring":urlencode(parameters),
                    "method": method,
                    "index":index,
                    "type": type_,
                    "jsonp_callback": "&callback=" + jsonp_callback if jsonp_callback else ""
                    }
        return path

    def search(self, callback, **kwargs):
        path = self.create_path("search", **kwargs)
        source = json.dumps( kwargs.get('source', {"query":{"query_string" : {"query" : "*"}}}))
        self.post_by_path(path, callback, source)

    def multi_search(self, callback, **kwargs):
        path = self.create_path("msearch", **kwargs)
        source = kwargs.get('source', {"query":{"query_string" : {"query" : "*"}}})
        self.post_by_path(path, callback, source)

    def post_by_path(self, path, callback, source):
        url = 'http://%(host)s:%(porta)s%(path)s' % {"host": self.host, "porta": self.port, "path": path}
        request_http = HTTPRequest(url, method="POST", body=source)
        self.client.fetch(request_http, callback)

    def get_by_path(self, path, callback):
        url = 'http://%(host)s:%(porta)s%(path)s' % {"host": self.host, "porta": self.port, "path": path}
        self.client.fetch(url, callback)

    def get(self, index, type, uid, callback):
        path = '/{index}/{type}/{uid}'.format(**locals())
        url = 'http://%(host)s:%(porta)s%(path)s' % {"host": self.host, "porta": self.port, "path": path}
        def to_dict_callback(response):
            source = json.loads(response.body).get('_source', {})
            callback(source)
        self.client.fetch(url, to_dict_callback)
