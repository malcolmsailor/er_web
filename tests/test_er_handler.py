import er_web
from er_web import forms, er_handler
from fixtures import client


def test_form_temp(client):
    with er_web.app.test_request_context():
        form = forms.ERForm({})
    if form.validate():
        er_handler.make_music(form)
