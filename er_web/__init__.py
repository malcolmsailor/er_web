import flask
from flaskext.markdown import Markdown

app = flask.Flask(__name__)
md = Markdown(app)

app.config.from_mapping(
    SECRET_KEY="dev",  # TODO
)

from . import routes
