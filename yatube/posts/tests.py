from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from .models import Group, Post, User, Follow, Comment


class PostTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.unauth = Client()
        self.user = User.objects.create_user(username="m_smith")
        self.client.force_login(self.user)
        self.group = Group.objects.create(
            slug="test_group", title="test_group", description="test_desc"
        )
        cache.clear()

    def search_pages(self, msg=None, post=None):
        response_index = self.client.get(reverse("index"))
        response_profile = self.client.get(
            reverse("profile", kwargs={"username": "m_smith"})
        )
        response_group = self.client.get(
            reverse("group_posts", kwargs={"slug": self.group.slug})
        )

        def url_search(resp):
            self.assertEqual(resp.status_code, 200)
            self.assertIn("page", resp.context)
            for pst in resp.context["page"]:
                count = 0
                if pst.text == msg and pst.group == self.group:
                    count += 1
            self.assertEqual(count, 1)

        url_search(response_index)
        url_search(response_profile)
        url_search(response_group)

        response_post = self.client.get(
            reverse("post", kwargs={"username": "m_smith", "post_id": post.pk})
        )
        self.assertEqual(response_post.status_code, 200)
        self.assertIn("post", response_post.context)
        self.assertEqual(response_post.context["post"].text, msg)
        self.assertEqual(response_post.context["post"].group, self.group)

    def test_signup(self):
        response = self.client.get(reverse("profile", kwargs={
            "username": "m_smith"
        }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["post_count"], 0)
        self.assertIsInstance(response.context["author"], User)
        self.assertEqual(response.context["author"].username,
                         self.user.username)

    def test_new_post(self):
        msg = "Testtext_testtext."
        self.client.post(
            reverse("new_post"),
            {"text": msg, "group": self.group.pk},
            follow=True
        )
        post = Post.objects.get(text=msg)
        self.search_pages(msg, post)

    def test_post_edit(self):
        post = Post.objects.create(
            text="Lorem ipsum dolor.", author=self.user, group=self.group
        )
        msg = "new text"
        self.client.post(
            reverse("post_edit", kwargs={
                "username": "m_smith",
                "post_id": post.pk
            }),
            {"text": msg, "group": self.group.pk},
            follow=True,
        )
        count = Post.objects.filter(text=msg, group=self.group).count()
        self.assertEqual(count, 1)
        self.assertTrue(Post.objects.filter(text=msg).exists())
        self.search_pages(msg, post)

    def test_unauth_redir(self):
        response = self.unauth.post(reverse("new_post"), follow=True)
        self.assertEqual(Post.objects.all().count(), 0)
        self.assertRedirects(
            response,
            "/auth/login/?next=/new/",
            status_code=302,
            target_status_code=200
        )


class PageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="test_user")
        self.client.force_login(self.user)
        self.group = Group.objects.create(
            slug="test_group", title="test_group", description="test_desc"
        )

    def test_page_404(self):
        response = Client().get("/page_blablabla/")
        self.assertEqual(response.status_code, 404)

    def test_cache(self):
        post1 = Post.objects.create(
            author=self.user, text="test_text", group=self.group,
        )
        response = self.client.get(reverse("index"))
        self.assertContains(response, post1.text)
        post2 = Post.objects.create(
            author=self.user, text="test_text22", group=self.group,
        )
        response2 = self.client.get(reverse("index"))
        self.assertNotContains(response2, post2.text)
        cache.clear()
        response3 = self.client.get(reverse("index"))
        self.assertContains(response3, post2.text)


class FollowCommentTest(TestCase):
    def setUp(self):
        self.auth = Client()
        self.user = User.objects.create_user(username="test_user")
        self.auth.force_login(self.user)
        self.un_auth = Client()
        self.group = Group.objects.create(
            slug="test_group", title="test_group", description="test_desc"
        )
        self.writer = User.objects.create_user(username="test_author")
        self.post = Post.objects.create(
            author=self.writer, text="test_text", group=self.group,
        )

    def test_follow(self):
        self.auth.get(reverse("profile_follow", args=[self.writer]))
        index_resp = self.auth.get(reverse("follow_index"))
        self.assertTrue(
            Follow.objects.filter(author=self.writer, user=self.user).exists()
        )
        self.assertContains(index_resp, self.post.text)

    def test_unfollow(self):
        self.auth.get(reverse("profile_unfollow", args=[self.writer]))
        index_resp = self.auth.get(reverse("follow_index"))
        self.assertFalse(
            Follow.objects.filter(author=self.writer, user=self.user).exists()
        )
        self.assertNotContains(index_resp, self.post.text)

    def test_comment(self):
        self.auth.post(
            reverse("add_comment", args=[self.writer.username, self.post.id]),
            {"text": "test"},
        )
        self.assertTrue(Comment.objects.filter(text="test").exists())
        self.un_auth.post(
            reverse("add_comment", args=[self.writer.username, self.post.id]),
            follow=True,
        )
        self.assertEqual(Comment.objects.all().count(), 1)


class ImageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="test_user")
        self.client.force_login(self.user)
        self.group = Group.objects.create(
            slug="test_group", title="test_group", description="test_desc"
        )

    def test_with_image(self):
        gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        img = SimpleUploadedFile(
            name="gif",
            content=gif,
            content_type="image/gif",
        )
        post = Post.objects.create(
            author=self.user,
            text="test_text",
            group=self.group,
            image=img
        )
        urls = [
            reverse("post", args=[self.user.username, post.id]),
            reverse("index"),
            reverse("profile", args=[self.user.username]),
            reverse("group_posts", args=[self.group]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "<img")

    def test_without_image(self):
        not_image = SimpleUploadedFile(
            name="test.txt", content=b"abc", content_type="text/plain",
        )
        url = reverse("new_post")
        response = self.client.post(url, {"text": "text", "image": not_image})
        self.assertFormError(
            response,
            "form",
            "image",
            errors=(
                "Загрузите правильное изображение. "
                "Файл, который вы загрузили, поврежден "
                "или не является изображением."
            ),
        )
