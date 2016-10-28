#!/usr/bin/env python

import os
from flask import Flask, send_file, jsonify, abort, request, render_template
from flask.ext.cors import CORS
from iiif2 import iiif, web
from configs import options, cors, approot, cache_root, media_root, cache_expr

app = Flask(__name__)
cors = CORS(app) if cors else None


def resolve(identifier):
    """Resolves a iiif identifier to the resource's path on disk."""
    return os.path.join(media_root, identifier)


@app.route('/')
def index():
    return jsonify({'identifiers': [f for f in os.listdir(media_root)]})


@app.route('/<identifier>/info.json')
def image_info(identifier):
    try:
        uri = "%s%s" % (request.url_root, identifier)
        return jsonify(web.info(uri, resolve(identifier)))
    except:
        abort(400)


@app.route('/<identifier>', defaults={'quality': 'default', 'fmt': 'jpg'})
@app.route('/<identifier>/view/<quality>.<fmt>')
def view(identifier, quality="default", fmt="jpg"):
    uri = '%s%s' % (request.url_root, identifier)
    return render_template('viewer.html', info=web.info(uri, resolve(identifier)))


@app.route('/<identifier>/<region>/<size>/<rotation>/<quality>.<fmt>')
def image_processor(identifier, **kwargs):
    cache_path = os.path.join(cache_root, web.urihash(request.path))

    if os.path.exists(cache_path):
        mime = iiif.type_map[kwargs.get('fmt')]['mime']
        return send_file(cache_path, mimetype=mime)

    try:
        params = web.Parse.params(identifier, **kwargs)
        tile = iiif.IIIF.render(resolve(identifier), **params)
        tile.save(cache_path, tile.mime)
        return send_file(tile, mimetype=tile.mime)
    except:
        abort(400)


@app.after_request
def add_header(response):
    response.cache_control.max_age = cache_expr  # minutes
    return response

if __name__ == '__main__':
    app.run(**options)
