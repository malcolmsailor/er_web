import pytest

import er_web


@pytest.fixture
def client():
    er_web.app.config["TESTING"] = True
    er_web.app.config["WTF_CSRF_ENABLED"] = False
    with er_web.app.test_client() as client_:
        # with er_web.app.app_context():
        # not sure I need to do anything with this context
        yield client_
