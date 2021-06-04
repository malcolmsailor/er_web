# Copied contents into __init__.py
# import os
# import sys

# from flask import Flask
# from flask import redirect, render_template

# sys.path.insert(
#     0,
#     os.path.abspath(
#         os.path.join(
#             os.path.dirname(__file__),
#             "/Users/Malcolm/Google Drive/python/efficient_rhythms/src",
#         )
#     ),
# )

# import er_settings

# from . import add_fields


# app = Flask(__name__)

# app.config.from_mapping(
#     SECRET_KEY="dev",
# )


# # @app.route("/", methods=("GET", "POST"))
# # def hello():
# #     return "Hello, World!"


# import wtforms
# from flask_wtf import FlaskForm
# from wtforms import StringField, IntegerField
# from wtforms.validators import DataRequired

# DOC_DICT = {}


# class MyForm(FlaskForm):
#     submit = wtforms.SubmitField("Submit")


# add_fields.add_fields_to_form(er_settings.ERSettings, MyForm, DOC_DICT)


# @app.route("/", methods=("GET", "POST"))
# def submit():
#     form = MyForm()
#     if form.validate_on_submit():
#         return redirect("/")
#     return render_template("base.jinja", form=form, doc_dict=DOC_DICT)


# # @dataclasses.dataclass
# # class DC:
# #     a: typing.List[int] = dataclasses.field(default_factory=list)
# #     b: float = 3.5


# # @dataclasses.dataclass
# # class Foo:
# #     a: typing.List[int] = dataclasses.field(
# #         default_factory=list,
# #         metadata={"val_dict": {"min_": (0,), "max_": (12,)}},
# #     )
# #     b: str = "foobar"
