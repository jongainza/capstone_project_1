from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    SubmitField,
    FieldList,
    FormField,
)
from wtforms.validators import InputRequired, Email, DataRequired


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    email = StringField("Email", validators=[InputRequired(), Email()])
    image_url = StringField("Image_URL")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])


class CommentForm(FlaskForm):
    text = TextAreaField("Comment", validators=[DataRequired()])
    submit = SubmitField("Post Comment")


class RecipeForm(FlaskForm):
    title = StringField("Title")
    image = StringField("Image_URL")
    ingredient = StringField("Ingredient")
    step = StringField("Step")


# class IngredientsForm(FlaskForm):
#     ingredient = StringField("Ingredient")


# class InstructionsForm(FlaskForm):
#     step = StringField("Step")
