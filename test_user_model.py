"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test the User model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )


        db.session.add_all([u,u2])
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        # Tests repr method
        self.assertEqual(f"{u}", f"<User #{u.id}: {u.username}, {u.email}>")
        self.assertEqual(f"{u2}", f"<User #{u2.id}: {u2.username}, {u2.email}>")
    
    def test_following(self):
        """Does following work?"""
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )


        db.session.add_all([u,u2])
        db.session.commit()

        # Users should not be following each other
        self.assertEqual(u.is_followed_by(u2), False)
        self.assertEqual(u2.is_followed_by(u), False)

        # User1 follows User2
        follow = Follows(user_being_followed_id=u2.id,user_following_id=u.id);
        db.session.add(follow)
        db.session.commit()
        
        #Relationships should be set up
        self.assertIn(u,u2.followers)
        self.assertIn(u2, u.following)
        self.assertEqual(u.is_followed_by(u2), False)
        self.assertEqual(u2.is_followed_by(u), True)
        self.assertEqual(u.is_following(u2), True)
        self.assertEqual(u2.is_following(u), False)
    
    def test_user_signup(self):
        """Does User.signup work?"""

        #Tests User.signup method
        u = User.signup(username="testy", password="password", email="testy@gmail.com", image_url="")

        self.assertEqual(f"{u}", f"<User #{u.id}: {u.username}, {u.email}>")

        #Test failure by passing in non valid fields

        self.assertRaises(ValueError, User.signup,username="testy2", password="", email="testy@gmail.com", image_url="")

    
    def test_user_auth(self):
        """Does User.authenticate work?"""
        #Test user authentication
        u = User.signup(username="testy", password="password", email="testy@gmail.com", image_url="")

        #Should return the user if the correct username and password is passed in
        user = User.authenticate("testy","password")
        self.assertEqual(user, u)

        #Should return false if the incorrect username or password is passed in
        user = User.authenticate("testy","password123")
        self.assertEqual(user, False)
        user = User.authenticate("badusername","password")
        self.assertEqual(user, False)
        
