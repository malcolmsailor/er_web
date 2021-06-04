import flask

app = flask.Flask(__name__)

app.config.from_mapping(
    SECRET_KEY="dev",  # TODO
)

from . import routes
