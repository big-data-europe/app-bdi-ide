'''
functions and classes for generating HAR data from parsed http data
'''

import http
import json


# json_repr for HTTP header dicts
def header_json_repr(d):
    return [
        {
            'name': k,
            'value': v
        } for k, v in sorted(d.iteritems())
    ]


def query_json_repr(d):
    # d = {string: [string]}
    # we need to print all values of the list
    output = []
    for k, l in sorted(d.iteritems()):
        for v in l:
            output.append({
                'name': k,
                'value': v
            })
    return output


# add json_repr methods to http classes
def HTTPRequestJsonRepr(self):
    '''
    self = http.Request
    '''
    return {
        'method': self.msg.method,
        'url': self.url,
        'httpVersion': 'HTTP/' + self.msg.version,
        'cookies': [],
        'queryString': query_json_repr(self.query),
        'headersSize': -1,
        'headers': header_json_repr(self.msg.headers),
        'bodySize': len(self.msg.body),
    }
http.Request.json_repr = HTTPRequestJsonRepr


def HTTPResponseJsonRepr(self):
    content = {
        'size': self.body_length,
        'mimeType': self.mimeType
    }
    if self.compression_amount is not None:
        content['compression'] = self.compression_amount
    if self.text:
        if self.encoding:
            content['text'] = self.text
            content['encoding'] = self.encoding
        else:
            content['text'] = self.text.encode('utf8')  # must transcode to utf-8
    return {
        'status': int(self.msg.status),
        'statusText': self.msg.reason,
        'httpVersion': 'HTTP/' + self.msg.version,
        'cookies': [],
        'headersSize': -1,
        'bodySize': self.raw_body_length,
        'redirectURL': self.msg.headers['location'] if 'location' in self.msg.headers else '',
        'headers': header_json_repr(self.msg.headers),
        'content': content,
    }
http.Response.json_repr = HTTPResponseJsonRepr


# custom json encoder
class JsonReprEncoder(json.JSONEncoder):
    '''
    Custom Json Encoder that attempts to call json_repr on every object it
    encounters.
    '''

    def default(self, obj):
        if hasattr(obj, 'json_repr'):
            return obj.json_repr()
        return json.JSONEncoder.default(self, obj) # should call super instead?
