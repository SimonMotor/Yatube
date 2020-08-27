from django.db import models

from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=75, unique=True)
    description = models.TextField(max_length=400)

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name="Введите текст", help_text="Текст новой записи"
    )
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts"
    )
    group = models.ForeignKey(
        "Group",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
        verbose_name="Выберите группу",
        help_text="Необязательно",
    )
    image = models.ImageField(
        upload_to="posts/",
        blank=True,
        null=True,
        verbose_name="Изображение",
        help_text="Добавьте картинку к посту",
    )

    def __str__(self):
        auth = self.author
        date = self.pub_date
        short = self.text[:30]
        return "%s %s %s" % (auth, date, short)

    class Meta:
        ordering = ("-pub_date",)


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField()
    created = models.DateTimeField("date published", auto_now_add=True)

    def __str__(self):
        post = self.post
        author = self.author
        created = self.created
        text = self.text
        return "%s %s %s %s" % (post, author, created, text)

    class Meta:
        ordering = ("created",)


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )

    class Meta:
        unique_together = (("user", "author"),)
