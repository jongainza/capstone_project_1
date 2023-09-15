








@app.route("/recipe", methods=["GET"])
def search_recipes():
    ingredient = request.args.get("ingredient")
        

     # Fetch a batch of random API recipes, up to the number of missing recipes
        batch_size = 100
        api_recipes = requests.get(
            f"https://api.spoonacular.com/recipes/findByIngredients",
            params={
                "ingredients": ingredient,
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
    
        return  redirect(f"/recipe/list")



@app.route("/recipe/list", methods=["GET"])
def search_recipes():

    total_recipes = (
                Recipe.query.join(Ingredient)
                .filter(Ingredient.name == ingredient)
                .order_by(func.random())
                .limit(10)
                .all()
            )
    return render_template(
                "recipes.html",
                recipes=total_recipes,
            )