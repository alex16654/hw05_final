from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import reverse


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
    )
    slug = models.SlugField(
        unique=True,
    )
    description = models.TextField()

    def get_absolute_url(self):
        return reverse('group_posts', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField(
        "date published",
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ('-pub_date',)

    def get_absolute_url(self):
        return reverse('post', kwargs={
            'username': self.author,
            'post_id': self.pk}
        )

    def get_edit_url(self):
        return reverse('post_edit', kwargs={
            'username': self.author,
            'post_id': self.pk}
        )

    def get_profile_url(self):
        return reverse('profile', kwargs={'username': self.author})

    def __str__(self):
        return(f' user: {self.author},'
               f' group: {self.group},'
               f' date: {self.pub_date:%d/%m/%Y},'
               f' post: {self.text:.70}...')


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comment_post'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_author'
    )
    text = models.TextField(max_length=280)
    created = models.DateTimeField(auto_now_add=True)

    # def get_absolut_url(self):
    #     return reverse('add_comment', kwargs={
    #         'username': self.author,
    #         'post_id': self.post}
    #     )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return(f' user: {self.author},'
               f' date: {self.created:%d/%m/%Y},'
               f' comment: {self.text:.70}...')

class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following',
    )
    class Meta:
        models.UniqueConstraint(fields=[
            'user',
            'author'], name=
            'following_unique'
        )