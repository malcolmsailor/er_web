import flask

import er_web

from fixtures import client


def test_one(client):
    result = client.get("/")
    print(result)


def test_two(client):
    with er_web.app.test_request_context():
        request_args = flask.request.args
    with er_web.app.test_request_context():
        form = er_web.forms.ERForm(request_args)
        assert form.validate()
