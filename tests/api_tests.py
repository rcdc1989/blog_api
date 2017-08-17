import unittest
import os
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Python 2 compatibility

# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "posts.config.TestingConfig"

from posts import app
from posts import models
from posts.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the posts API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)
        
    def test_get_empty_posts(self):
        """ Getting posts from an empty database """
        response = self.client.get("/api/posts",
                                    headers=[("Accept", "application/json")]
                                  )
    
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
    
        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data, [])
    
    def test_get_posts(self):
        """ Getting posts from a populated database """
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")

        session.add_all([postA, postB])
        session.commit()
        
        response = self.client.get("/api/posts", 
                                    headers=[("Accept", "application/json")]
                                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(data), 2)

        postA = data[0]
        self.assertEqual(postA["title"], "Example Post A")
        self.assertEqual(postA["body"], "Just a test")

        postB = data[1]
        self.assertEqual(postB["title"], "Example Post B")
        self.assertEqual(postB["body"], "Still a test")
        
    def test_get_post(self):
        """ Getting a single post from a populated database """
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")

        session.add_all([postA, postB])
        session.commit()

        response = self.client.get("/api/posts/{}".format(postB.id),
                                    headers=[("Accept", "application/json")]
                                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        post = json.loads(response.data.decode("ascii"))
        self.assertEqual(post["title"], "Example Post B")
        self.assertEqual(post["body"], "Still a test")

    def test_get_non_existent_post(self):
        """ Getting a single post which doesn't exist """
        response = self.client.get("/api/posts/1", 
                                    headers=[("Accept", "application/json")]
                                    )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"], "Could not find post with id 1")
        
    def test_unsupported_accept_header(self):
        response = self.client.get("/api/posts",
            headers=[("Accept", "application/xml")]
        )

        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"],
                         "Request must accept application/json data")
                         
                         
    def test_delete_post(self):
        """ delete a post """
        
        #create an example post
        postB = models.Post(title="Example Post B", body="Still a test")

        session.add(postB)
        session.commit()

        response = self.client.get("/api/posts/{}".format(postB.id),
                                    headers=[("Accept", "application/json")]
                                    )
                                    
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        post = json.loads(response.data.decode("ascii"))
        self.assertEqual(post["title"], "Example Post B")
        self.assertEqual(post["body"], "Still a test")
        
        #now that we have some data, attempt to delete
        response = self.client.delete("/api/posts/{}".format(postB.id),
                            headers=[("Accept", "application/json")]
                            )
        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"], "Deleted post with id 1")
        
    def test_delete_nonexistent_post(self):
        """ delete a post """
        
        #attempt to delete post with arbitrary id 1
        response = self.client.delete("/api/posts/{}".format(1),
                            headers=[("Accept", "application/json")]
                            )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"], "Could not find post with id 1")
        
    def test_get_posts_with_title(self):
        """ Filtering posts by title """
        postA = models.Post(title="Post with bells", body="Just a test")
        postB = models.Post(title="Post with whistles", body="Still a test")
        postC = models.Post(title="Post with bells and whistles",
                            body="Another test")

        session.add_all([postA, postB, postC])
        session.commit()

        response = self.client.get("/api/posts?title_like=whistles",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(posts), 2)

        post = posts[0]
        self.assertEqual(post["title"], "Post with whistles")
        self.assertEqual(post["body"], "Still a test")

        post = posts[1]
        self.assertEqual(post["title"], "Post with bells and whistles")
        self.assertEqual(post["body"], "Another test")
    
    def test_get_posts_with_content(self):
        """ Filtering posts by content text """
        #create test data
        postA = models.Post(title="Post with bells", body="hat hat hat")
        postB = models.Post(title="Post with whistles", body="cat cat cat")
        postC = models.Post(title="Post with bells and whistles",
                            body="hat cat hat cat")

        session.add_all([postA, postB, postC])
        session.commit()

        response = self.client.get("/api/posts?content_like=hat",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(posts), 2)

        post = posts[0]
        self.assertEqual(post["title"], "Post with bells")
        self.assertEqual(post["body"], "hat hat hat")

        post = posts[1]
        self.assertEqual(post["title"], "Post with bells and whistles")
        self.assertEqual(post["body"], "hat cat hat cat")
        
    def test_get_posts_with_content_and_title(self):
        """ Filtering posts by content text  and title"""
        #create test data
        postA = models.Post(title="Post with bells", body="hat hat hat")
        postB = models.Post(title="Post with whistles", body="cat cat cat")
        postC = models.Post(title="Post with bells and whistles",
                            body="hat cat hat cat")

        session.add_all([postA, postB, postC])
        session.commit()

        response = self.client.get("/api/posts?content_like=hat&title_like=whistles",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(posts), 1)

        post = posts[0]
        self.assertEqual(post["title"], "Post with bells and whistles")
        self.assertEqual(post["body"], "hat cat hat cat")
    
if __name__ == "__main__":
    unittest.main()
