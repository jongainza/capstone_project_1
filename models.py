from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()

bcrypt = Bcrypt()


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, unique=True, nullable=False)
    image_url = db.Column(
        db.Text,
        default="/static/images/chef-png.png",
    )
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)

    saved_recipes = db.relationship("SavedRecipe", backref="user", lazy=True)
    user_generated_recipes = db.relationship(
        "UserGeneratedRecipe", backref="user", lazy=True
    )
    comments = db.relationship("Comment", backref="user", lazy=True)

    @classmethod
    def register(cls, username, password, email, image_url):
        """register user w/hashed password & reeturn user."""

        hashed = bcrypt.generate_password_hash(password)
        # turn bytestring into normal unicode (unicode utf8) string
        hashed_utf8 = hashed.decode("utf8")

        # return instance of user w/username and hashed pwd
        return cls(
            username=username, password=hashed_utf8, email=email, image_url=image_url
        )

    @classmethod
    def authenticate(cls, username, password):
        """Validate the user exists and password is correct.

        Return user if valid; else return False.
        """

        u = User.query.filter_by(username=username).first()

        if u and bcrypt.check_password_hash(u.password, password):
            # Return user instance
            return u
        else:
            return False


class Recipe(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(200))
    ingredients = db.relationship("Ingredient", backref="recipe", lazy=True)
    instructions = db.relationship("Instruction", backref="recipe", lazy=True)


class Ingredient(db.Model):
    __tablename__ = "ingredients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)


class Instruction(db.Model):
    __tablename__ = "instructions"
    id = db.Column(db.Integer, primary_key=True)
    step = db.Column(db.Text, nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)


class SavedRecipe(db.Model):
    __tablename__ = "saved_recipes"
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    recipe = db.relationship("Recipe", backref="saved_recipes")


class UserGeneratedRecipe(db.Model):
    __tablename__ = "user_recipes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    ingredients = db.relationship(
        "UserGeneratedIngredient", backref="user_generated_recipe", lazy=True
    )
    instructions = db.relationship(
        "UserGeneratedInstruction", backref="user_generated_recipe", lazy=True
    )


class UserGeneratedIngredient(db.Model):
    __tablename__ = "user_ingredients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    user_generated_recipe_id = db.Column(
        db.Integer, db.ForeignKey("user_recipes.id"), nullable=False
    )


class UserGeneratedInstruction(db.Model):
    __tablename__ = "user_instructions"
    id = db.Column(db.Integer, primary_key=True)
    step = db.Column(db.Text, nullable=False)
    user_generated_recipe_id = db.Column(
        db.Integer, db.ForeignKey("user_recipes.id"), nullable=False
    )


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipe_id = db.Column(
        db.Integer, db.ForeignKey("recipes.id"), nullable=True
    )  # To store either a recipe ID or an API recipe ID
    parent_id = db.Column(
        db.Integer, db.ForeignKey("comments.id"), nullable=True
    )  # For threaded comments
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow(),
    )
    recipe = db.relationship("Recipe", backref="comments")
