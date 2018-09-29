from flask import Flask, request, jsonify, render_template, make_response, abort, send_from_directory
from datetime import datetime
from operator import itemgetter
from markupsafe import Markup
from tinydb import TinyDB, Query
import html
import itertools
import json
import os
import sys
import urllib

# From http://flask.pocoo.org/snippets/35/
class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    In nginx:
    location /myprefix {
        proxy_pass http://192.168.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /myprefix;
        }

    :param app: the WSGI application
    '''
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)


app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)
filename = 'standups.json'
db = TinyDB(filename)


def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


@app.route("/user/<user>")
def user(user):
    Record = Query()
    result = db.search(Record.user.search(user))
    if request_wants_json():
        return jsonify(result)
    return render_template('entries.html', entries=result)


@app.route("/entry/<doc_id>")
def entry(doc_id):
    Record = Query()
    result = db.get(doc_id=doc_id)
    if request_wants_json():
        return jsonify(result)
    return render_template('entries.html', entries=[result])


@app.route("/")
def all():
    result = db.all()
    if request_wants_json():
        return jsonify(result)
    return render_template('entries.html', entries=result)


@app.route("/record", methods=["POST"])
def record():
    if request.form['secret'] != config['secret']:
        abort(403)
    try:
        doc_id = db.insert({
            'user': request.form['user'],
            'content': html.escape(request.form['message']),
            'created': str(datetime.now()),
        })
        if request_wants_json() :
            return make_response(jsonify({ 'status': 'success', 'id': doc_id }), 200)
        return ('', 204)
    except:
        e = sys.exc_info()
        if request_wants_json() :
            return make_response(jsonify({ 'status' : 'failure', 'error': str(e) }), 400)
        return (str(e), 400)


@app.route('/import', methods=["GET", "POST"])
def import_():
    print(list(request.files.keys()))
    if request.method == "POST" and 'json' in request.files:
        if request.form['secret'] != config['secret']:
            abort(403)
        user = request.form['user']
        dump = json.loads(request.files["json"].read())
        for entry in dump:
            db.insert({
                'user': user,
                'content': entry['content'].replace("<p>", "").replace("</p>", ""),
                'created': entry['created'],
            })
        return ("Inserted %d records for <a href='/user/%s'>%s</a>." % (len(dump), user, user), 200)
    return render_template('import.html')


@app.route('/file')
def file():
    return send_from_directory(os.getcwd(), filename)


@app.errorhandler(400)
def page_not_found(e):
    return '', 404

@app.template_filter('urlencode')
def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.parse.quote_plus(s)
    return Markup(s)

def main(port=None):
    global config
    with open('config.json') as f:
        config = json.loads(f.read())
        assert('port' in config)
        assert('secret' in config)
    app.run(port=config['port'])

if __name__ == "__main__":
    main()
