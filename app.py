from flask import Flask, render_template, redirect, session, flash, g, request
from flask_debugtoolbar import DebugToolbarExtension
from models import (
    connect_db,
    db,
    User,
    Recipe,
    Ingredient,
    Instruction,
    SavedRecipe,
    UserGeneratedRecipe,
    UserGeneratedIngredient,
    UserGeneratedInstruction,
)

from forms import RegistrationForm, LoginForm
from sqlalchemy.exc import IntegrityError
import requests

CURR_USER_KEY = "curr_user"

spoonacular_api_key = "35a15401df8045c189874b3ddcacadbb"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///foodie_db"
app.app_context().push()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

connect_db(app)
db.drop_all()
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


res = requests.get(
    "https://api.spoonacular.com/recipes/642927/analyzedInstructions",
    params={
        # "query": "fish",
        # "includeIngredients": "cheese",
        # "number": 2,
        "apiKey": "35a15401df8045c189874b3ddcacadbb",
    },
)
# User Authentication


@app.route("/register", methods=["GET", "POST"])
def register():
    # Handle user registration form submission and data validation
    # Example: if request.method == 'POST': ... (create a new user)
    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            user = User.register(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )

            db.session.commit()

        except IntegrityError:
            flash("Username already taken", "danger")
            return render_template("/users/register.html", form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template("users/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    # Handle user login form submission and authentication
    # Example: if request.method == 'POST': ... (authenticate user)
    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", "danger")

    return render_template("users/login.html", form=form)


@app.route("/logout")
def logout():
    # Logout the current user and redirect to the homepage
    # Example: logout_user() from Flask-Login
    """Handle logout of user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
        flash("Goodbye!", "info")
    return redirect("/login")


# User Profile
@app.route("/profile/<int:user_id>")
def user_profile(user_id):
    # Fetch user details, saved recipes, and user-generated recipes using SQLAlchemy
    # Pass the data to the template
    return render_template("user_profile.html")


# Recipe Search and Display
@app.route("/")
def home():
    # Fetch a list of recipes from the database using SQLAlchemy
    # Pass the data to the template
    return render_template("home.html")


@app.route("/recipe", methods=["GET"])
def search_recipes():
    ingredient = request.args.get("ingredient")

    if ingredient:
        url = f"https://api.spoonacular.com/recipes/findByIngredients"
        params = {
            "ingredients": ingredient,
            "number": 10,  # You can adjust the number of results as needed
            "apiKey": spoonacular_api_key,
        }

        response = requests.get(url, params=params)
        recipes = response.json()

        return render_template("recipes.html", recipes=recipes)

    return render_template("recipes.html", recipes=None)


@app.route("/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    # Fetch recipe details and comments from the database using SQLAlchemy
    # Pass the data to the template
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": spoonacular_api_key}

    response = requests.get(url, params=params)
    recipe = response.json()

    return render_template("recipe_detail.html", recipe=recipe)


# User Interaction
@app.route("/recipe/<int:recipe_id>/save")
def save_recipe(recipe_id):
    # Save the recipe to the user's profile
    return redirect("/recipe/{}".format(recipe_id))


@app.route("/recipe/<int:recipe_id>/unsave")
def unsave_recipe(recipe_id):
    # Remove the saved recipe from the user's profile
    return redirect("/recipe/{}".format(recipe_id))


@app.route("/recipe/<int:recipe_id>/comment", methods=["POST"])
def post_comment(recipe_id):
    # Handle user comment submission and add to the database
    return redirect("/recipe/{}".format(recipe_id))


# User-Generated Recipes
@app.route("/recipe/submit", methods=["GET", "POST"])
def submit_recipe():
    # Handle user-generated recipe submission form and moderation process
    return render_template("submit_recipe.html")


@app.route("/recipe/pending")
def pending_recipes():
    # Fetch pending user-generated recipes from the database using SQLAlchemy
    # Pass the data to the template
    return render_template("pending_recipes.html")


@app.route("/recipe/approve/<int:user_recipe_id>")
def approve_recipe(user_recipe_id):
    # Approve a user-generated recipe
    return redirect("/recipe/pending")


@app.route("/recipe/reject/<int:user_recipe_id>")
def reject_recipe(user_recipe_id):
    # Reject a user-generated recipe
    return redirect("/recipe/pending")


# Recipe Filtering and Sorting
@app.route("/recipes/filter")
def filter_recipes():
    # Display page to filter recipes by cuisine, dietary preferences, etc.
    return render_template("filter_recipes.html")


@app.route("/recipes/sort")
def sort_recipes():
    # Display page to sort recipes by rating, preparation time, etc.
    return render_template("sort_recipes.html")


# Meal Planning
@app.route("/meal/plan")
def meal_plan():
    # Display page to plan meals and generate a shopping list
    return render_template("meal_plan.html")


# Social Sharing
@app.route("/recipe/<int:recipe_id>/share/facebook")
def share_facebook(recipe_id):
    # Share a recipe on Facebook and redirect back to recipe detail
    return redirect("/recipe/{}".format(recipe_id))


# Recipe Recommendations
@app.route("/recommendations")
def recommendations():
    # Display personalized recipe recommendations based on user preferences
    return render_template("recommendations.html")
