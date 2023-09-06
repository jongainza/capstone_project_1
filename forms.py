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


class InstructionForm(FlaskForm):
    step = TextAreaField("Step")


class IngredientForm(FlaskForm):
    name = StringField("Ingredient Name")
    quantity = StringField("Quantity")


class RecipeForm(FlaskForm):
    title = StringField("Title")
    instructions = FieldList(FormField(InstructionForm), min_entries=1)
    ingredients = FieldList(FormField(IngredientForm), min_entries=1)
    add_step = SubmitField("Add Step")
    add_ingredient = SubmitField("Add Ingredient")
    submit = SubmitField("Create Recipe")
