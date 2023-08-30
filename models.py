from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()

bcrypt = Bcrypt()


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
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

    @classmethod
    def register(cls, username, password, email, image_url):
        """register user w/hashed password & reeturn user."""

        hashed = bcrypt.generate_password_hash(password)
        # turn bytestring into normal unicode (unicode utf8) string
        hashed_utf8 = hashed.decode("utf8")

        # return instance of user w/username and hashed pwd
        user = User(
            username=username,
            password=hashed_utf8,
            email=email,
            image_url=image_url,
        )

        db.session.add(user)
        return user

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
