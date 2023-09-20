from flask import (
    Flask,
    render_template,
    redirect,
    session,
    flash,
    g,
    request,
    url_for,
    abort,
)
from flask_debugtoolbar import DebugToolbarExtension
from models import (
    connect_db,
    db,
    User,
    Recipe,
    Ingredient,
    Instruction,
    SavedRecipe,
    Comment,
)

from forms import (
    RegistrationForm,
    LoginForm,
    CommentForm,
    RecipeForm,
)
from sqlalchemy.exc import IntegrityError, NoResultFound
import requests, json
from sqlalchemy import or_, func, text
from datetime import datetime
import random


spoonacular_api_key = "35a15401df8045c189874b3ddcacadbb"
#
# "9161efe8f1dc4b55b016c30584e8209c"
# "f89f72907ab54854aa13dcf946a10079"

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


res = requests.get(
    "https://api.spoonacular.com/recipes/642927/analyzedInstructions",
    params={
        "apiKey": "35a15401df8045c189874b3ddcacadbb",
    },
)

# User Authentication


@app.route("/register", methods=["GET", "POST"])
def register():
    # Handle user registration form submission and data validation

    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            new_user = User.register(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.add(new_user)
            db.session.commit()
            session["user_id"] = new_user.id
            session["user_name"] = new_user.username
            flash("Welcome! Successfully Created Your Account!")
            return redirect(f"/profile/{new_user.id}")

        except IntegrityError:
            db.session.rollback()
            flash("Username already taken", "danger")
            return render_template("/users/register.html", form=form)

    else:
        return render_template("users/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    # Handle user login form submission and authentication

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            flash(f"Welcome Back!, {user.username}!", "success")
            session["user_id"] = user.id
            session["user_name"] = user.username
            return redirect(f"/profile/{user.id}")
        else:
            form.username.errors = ["Invalid username/password"]

    return render_template("users/login.html", form=form)


@app.route("/logout")
def logout():
    # Logout the current user and redirect to the homepage
    """Handle logout of user."""
    session.pop("user_id", "user_name")
    flash("Goodbye!")
    return redirect("/")


@app.route("/")
def home():
    if "user_id" in session:
        user_id = session["user_id"]

        # check if user exists in database
        user = User.query.get(user_id)

        if user is not None:
            return redirect(f"/profile/{session['user_id']}")

        # if the user is not in the database clear the session
        session.pop("user_id")

    return render_template("index.html")


@app.route("/profile/<int:user_id>")
def show_profile(user_id):  # Retrieve user details from the database
    if "user_id" not in session:
        flash("Please login first!")
        return redirect("/login")

    user = User.query.get_or_404(user_id)

    # Retrieve saved recipes from the database
    saved_recipes = user.saved_recipes

    # Retrieve user-generated recipes from the database
    user_generated_recipes = Recipe.query.filter_by(user_id=user_id).all()

    # Pass user data and other data to the template
    return render_template(
        "users/user_profile.html",
        user=user,
        saved_recipes=saved_recipes,
        user_generated_recipes=user_generated_recipes,
    )


@app.route("/recipe", methods=["GET"])
def search_recipes():
    ingrediente = request.args.get("ingredient")

    # Fetch a batch of random API recipes, up to the number of missing recipes
    batch_size = 40
    api_recipes = requests.get(
        f"https://api.spoonacular.com/recipes/findByIngredients",
        params={
            "ingredients": ingrediente,
            "number": batch_size,
            "apiKey": spoonacular_api_key,
        },
    ).json()

    for recipe in api_recipes:
        recipe_title = recipe["title"]
        # Check if a recipe with the same title already exists in the database
        existing_recipe = Recipe.query.filter_by(title=recipe_title).first()

        if not existing_recipe:
            # Fetch the recipe details from the API
            url = f"https://api.spoonacular.com/recipes/{recipe['id']}/information"
            params = {"apiKey": spoonacular_api_key}
            response = requests.get(url, params=params)
            api_recipe_data = response.json()

            # Extract relevant recipe details for the current recipe
            recipe_image = api_recipe_data.get("image", None)
            recipe_ingredients = api_recipe_data.get("extendedIngredients", [])

            # Check if analyzedInstructions exist and have steps
            instructions_data = api_recipe_data.get("analyzedInstructions", [])
            if instructions_data and instructions_data[0].get("steps"):
                recipe_steps = instructions_data[0].get("steps")
            else:
                recipe_steps = []

            # Create new Recipe, Ingredients, and Instruction objects
            new_recipe = Recipe(title=recipe_title, image=recipe_image)
            db.session.add(new_recipe)
            db.session.commit()

            for ingredient in recipe_ingredients:
                new_ingredient = Ingredient(
                    name=ingredient["original"], recipe_id=new_recipe.id
                )
                db.session.add(new_ingredient)

            for step in recipe_steps:
                new_step = Instruction(step=step["step"], recipe_id=new_recipe.id)
                db.session.add(new_step)

        # Commit all changes for this batch of API recipes
        db.session.commit()

    return redirect(f"/recipe/list/{ingrediente}")


@app.route("/recipe/list/<ingrediente>", methods=["GET"])
def show_recipes(ingrediente):
    pattern = f"%{ingrediente}%"
    total_recipes = (
        Recipe.query.join(Ingredient)
        .filter(Ingredient.name.ilike(pattern))
        .order_by(func.random())
        .limit(12)
        .all()
    )
    print("Ingredient:", ingrediente)
    print("TOTAL_RECIPES:", total_recipes)

    return render_template(
        "recipes.html", recipes=total_recipes, ingredient=ingrediente
    )


@app.route("/recipe/db/<int:recipe_id>")
def db_recipe_detail(recipe_id):
    # Fetch the recipe from the database
    recipe = Recipe.query.get(recipe_id)

    user_id = session.get("user_id")
    saved_recipe = SavedRecipe.query.filter_by(
        user_id=user_id, recipe_id=recipe.id
    ).first()
    created_recipe = Recipe.query.filter_by(id=recipe.id, user_id=user_id).first()
    comments = Comment.query.filter_by(recipe_id=recipe.id).all()

    form = CommentForm()
    if saved_recipe or created_recipe:
        return render_template(
            "recipe_detail.html",
            recipe=recipe,
            saved_recipe=saved_recipe,
            created_recipe=created_recipe,
            comments=comments,
            form=form,
            user=session["user_id"],
        )
    else:
        return render_template(
            "recipe_detail.html",
            recipe=recipe,
            comments=comments,
            form=form,
            user=session["user_id"],
        )


# User Interaction
@app.route("/recipe/<int:recipe_id>/save", methods=["GET", "POST"])
def save_recipe(recipe_id):
    # # Check if the recipe already exists in "recipes" database
    db_recipe = Recipe.query.get(recipe_id)
    # Get the user's ID from the session
    user_id = session.get("user_id")

    # Update User's Saved Recipes
    if user_id:
        user = User.query.get(user_id)
        if user:
            # Check if the recipe already exists in "saved_recipes" database
            db_saved_recipe = SavedRecipe.query.filter_by(
                user_id=user_id, recipe_id=db_recipe.id
            ).first()
            if not db_saved_recipe:
                saved_recipe = SavedRecipe(recipe_id=db_recipe.id, user_id=user_id)
                # Swap recipe and user
                db.session.add(saved_recipe)
                db.session.commit()
                flash("Recipe saved successfully!", "success")
            else:
                flash("Recipe is already saved!", "info")

        else:
            flash("User not found!", "error")
    else:
        flash("User not authenticated!", "error")

    return redirect(f"/recipe/db/{recipe_id}")


@app.route("/recipe/<int:recipe_id>/unsave")
def unsave_recipe(recipe_id):
    # Remove the saved recipe from the user's profile
    user_id = session.get("user_id")
    if not user_id:
        flash("Access Unauthoried", "Danger")
        return redirect("/login")

    saved_recipes = SavedRecipe.query.filter_by(
        recipe_id=recipe_id, user_id=user_id
    ).all()
    for saved_recipe in saved_recipes:
        db.session.delete(saved_recipe)
        db.session.commit()
    flash("Recipe delated succesfully", "success")
    return redirect(f"/profile/{user_id}")


@app.route("/recipe/<int:recipe_id>/<parent_id>/comment", methods=["POST"])
def post_comment(recipe_id, parent_id):
    # Handle user comment submission and add to the database
    # Check if the user is logged in
    if not session["user_id"]:
        flash("You must be logged in to post a comment", "danger")
        return redirect("/login")

    user_id = session.get("user_id")

    # Convert the 'None' string to actual None
    if parent_id == "None":
        parent_id = None

    # Get the form data
    text = request.form.get("text")

    if text:
        # Check if this is a reply to an existing comment
        if parent_id is not None:
            comment = Comment(
                text=text,
                user_id=session["user_id"],
                recipe_id=recipe_id,
                parent_id=parent_id,
                timestamp=datetime.utcnow(),
            )
            db.session.add(comment)
            db.session.commit()
            flash("Reply posted successfully!", "success")

        else:
            # Handle regular comments
            comment = Comment(
                text=text,
                user_id=session["user_id"],
                recipe_id=recipe_id,
                timestamp=datetime.utcnow(),
                parent_id=None,
            )
            db.session.add(comment)
            db.session.commit()
            flash("Comment posted successfully!", "success")
    else:
        flash("Comment cannot be empty", "danger")

    return redirect(f"/profile/{user_id}")


@app.route("/create_recipe", methods=["GET", "POST"])
def create_recipe():
    # Check if the user is logged in
    user_id = session.get("user_id")
    if user_id is None:
        flash("You must be logged in to create a recipe", "danger")
        return redirect("/login")  # Redirect to the login page or an appropriate page

    # Create an instance of the recipe form
    form = RecipeForm()

    if request.method == "POST":
        # Check if the submitted form is the recipe form
        if form.validate_on_submit():
            # Create a new recipe
            new_recipe = Recipe(
                title=form.title.data,
                user_generated=True,
                user_id=user_id,
                image=form.image.data,
                status="pending",
            )

            db.session.add(new_recipe)
            db.session.commit()

            # Collect ingredients and steps data from the request
            ingredients = request.form.getlist("ingredient")
            steps = request.form.getlist("step")

            # Loop through the submitted ingredients and add them to the recipe
            for ingredient in ingredients:
                if ingredient:
                    new_ingredient = Ingredient(
                        name=ingredient,
                        recipe_id=new_recipe.id,
                    )
                    db.session.add(new_ingredient)

            # Loop through the submitted steps and add them to the recipe
            for step in steps:
                if step:
                    new_instruction = Instruction(
                        step=step,
                        recipe_id=new_recipe.id,
                    )
                    db.session.add(new_instruction)

            # Commit all changes to the database
            db.session.commit()

            return redirect(
                f"/profile/{user_id}"
            )  # Redirect to the user's profile page

    return render_template("/created_recipes/create_recipe.html", form=form)


@app.route("/show_thread/<int:recipe_id>/<int:comment_id>", methods=["GET", "POST"])
def show_thread(recipe_id, comment_id):
    user_id = session.get("user_id")
    recipe = Recipe.query.get(recipe_id)
    comment = Comment.query.get(comment_id)
    child_comments = Comment.query.filter_by(parent_id=comment_id).all()
    return render_template(
        "show_thread.html",
        comment=comment,
        child_comments=child_comments,
        recipe=recipe,
        user_id=user_id,
        form=CommentForm(),
    )
