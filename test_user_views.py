"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        self.testuser2 = User.signup(username="testuser2",
                            email="test2@test.com",
                            password="testuser2",
                            image_url=None)
        
        self.testuser3= User.signup(username="testuser3",
                            email="test3@test.com",
                            password="testuser3",
                            image_url=None)
        
        db.session.commit()

        self.message = Message(text="test message",user_id=self.testuser.id)
        self.follow = Follows(user_being_followed_id=self.testuser2.id, user_following_id=self.testuser.id)
        self.follow2 = Follows(user_being_followed_id=self.testuser3.id, user_following_id=self.testuser2.id)

        db.session.add_all([self.message,self.follow,self.follow2])
        db.session.commit()

    def test_view_homepage(self):
        """Can we view the homepage?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
        response = c.get("/")
        html=response.get_data(as_text=True)

        self.assertEqual(response.status_code,200)
        self.assertIn("@testuser",html)

    def test_following_views(self):
        """Can we view pages as a logged in user? """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
        users = User.query.all()

        # Tests that the following view renders correctly
        resp = c.get(f"/users/{self.testuser.id}/following")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code,200)
        self.assertIn(">@testuser<",html)
        self.assertIn(">@testuser2<",html)
        self.assertNotIn(">@testuser3<",html)

        # Tests that the following view for other users renders correctly
        resp = c.get(f"/users/{users[1].id}/following")
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn(">@testuser2<",html)
        self.assertIn(">@testuser3<",html)
        self.assertNotIn(">@testuser<",html)

        # Cannot view following if logged out
        c.get("/logout")
        
        resp = c.get(f"/users/{users[1].id}/following",follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn("Access unauthorized",html)

    def test_followers_views(self):
        """Can we view followers pages as a logged in user? """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
        users = User.query.all()

        # Tests that the followers view renders correctly
        resp = c.get(f"/users/{self.testuser.id}/followers")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code,200)
        self.assertIn(">@testuser<",html)
        self.assertNotIn(">@testuser2<",html)
        self.assertNotIn(">@testuser3<",html)

        # Tests that the followers view for other users renders correctly
        resp = c.get(f"/users/{users[1].id}/followers")
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn(">@testuser2<",html)
        self.assertIn(">@testuser<",html)
        self.assertNotIn(">@testuser3<",html)

        resp2 = c.get(f"/users/{users[2].id}/followers")
        html2 = resp2.get_data(as_text=True)
        self.assertEqual(resp2.status_code,200)
        self.assertIn(">@testuser3<",html2)
        self.assertIn(">@testuser2<",html2)
        self.assertNotIn(">@testuser<",html2)

        # Cannot view followers if logged out
        c.get("/logout")
        
        resp = c.get(f"/users/{users[1].id}/followers",follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn("Access unauthorized",html)
    
    def test_adding_deleting_messages(self):
        """ Can we add/remove messages for the logged in user """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
        # Adding a new messaged as testuser
        resp = c.post("/messages/new",data={'text':'Adding a new message!!!!'},follow_redirects=True)
        html = resp.get_data(as_text=True)

        # New message should appear on the user page
        self.assertEqual(resp.status_code,200)
        self.assertIn("Adding a new message!!!!",html)

        # Deleting the added message
        message = Message.query.filter(Message.text=="Adding a new message!!!!").one()
        resp = c.post(f"/messages/{message.id}/delete",follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code,200)
        self.assertNotIn("Adding a new message!!!!",html)
    
    def test_logged_out_adding_deleting_messages(self):

        with self.client as c:

            #Sending a post request to add a new message when not logged in
            resp = c.post("/messages/new",data={'text':'Adding a new message!!!!'},follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code,200)
            self.assertIn("Access unauthorized",html)

            # Sending a post request to delete a message when not logged in
            messages = Message.query.all()
            resp = c.post(f"/messages/{messages[0].id}/delete",follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code,200)
            self.assertIn("Access unauthorized",html)




