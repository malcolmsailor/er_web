
import er_web
import er_web.forms as forms

from fixtures import client

def test_form_temp(client):
    with er_web.app.test_request_context():
        form = forms.ERForm({})
    breakpoint()
