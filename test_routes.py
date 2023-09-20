from unittest import TestCase
from my_app import app, db
from flask import Flask, session, request, flash
from models import Comment, User, Recipe


class TestSomeRoutes(TestCase):
    def test_home(self):
        with app.test_client() as client:
            res = client.get("/")
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("<h2>Welcome to Your Recipe App</h2>", html)

    def test_post_comment(self):
        with app.test_client() as client:
            # create user for the test
            test_user = User(
                username="testuser", password="password", email="test@gmail.com"
            )
            db.session.add(test_user)
            db.session.commit()
            # create recipe for the test
            test_recipe = Recipe(
                title="test recipe",
            )
            db.session.add(test_recipe)
            db.session.commit()
            # add one user to the session
            with client.session_transaction() as sess:
                sess["user_id"] = test_user.id

            recipe_id = 1
            parent_id = None
            text = "this is a test"

            res = client.post(
                f"/recipe/{recipe_id}/{parent_id}/comment",
                data={"text": text},
                follow_redirects=True,
            )
            # create comment
            comment = Comment.query.filter_by(
                text=text, user_id=1, recipe_id=recipe_id
            ).first()
            self.assertEqual(res.status_code, 200)
            self.assertIsNotNone(comment)  # Check if the comment was created
            self.assertEqual(comment.text, text)
            self.assertEqual(comment.user_id, 1)
            self.assertEqual(comment.recipe_id, recipe_id)
            self.assertEqual(comment.parent_id, parent_id)

    def test_show_thread_get(self):
        with app.test_client() as client:
            # Create a test user
            test_user = User(
                username="testuser2", password="password2", email="test2@gmail.com"
            )
            db.session.add(test_user)
            db.session.commit()

            # Create a test recipe
            test_recipe = Recipe(
                title="test recipe2",
            )
            db.session.add(test_recipe)
            db.session.commit()

            # Create a test comment
            test_comment = Comment(
                text="Test comment2",
                user_id=test_user.id,
                recipe_id=test_recipe.id,
            )
            db.session.add(test_comment)
            db.session.commit()

            # Add the user to the session
            with client.session_transaction() as sess:
                sess["user_id"] = test_user.id

            # Access the show_thread route with the comment_id
            comment_id = test_comment.id
            recipe_id = test_recipe.id

            res = client.get(f"/show_thread/{recipe_id}/{comment_id}")

            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Test comment2", res.data)
