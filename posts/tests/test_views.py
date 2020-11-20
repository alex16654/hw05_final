from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse


from posts.models import Post, Group, Comment, Follow

User = get_user_model()


class StaticViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.user_second = User.objects.create_user(username='SashaBasov')
        cls.authorized_client = Client()
        cls.authorized_client_second = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_second.force_login(cls.user_second)
        cls.unauthorized_client = Client()
        #cls.unauthorized_client_second = Client()

    def test_new_post(self):
        test_group = Group.objects.create(
            title='tester',
            slug='test',
            description='common'
        )
        data = {'text': 'Это текст публикации',
                'group': test_group.id}
        response = self.authorized_client.post(
            reverse('new_post'), data, follow=True)
        post = Post.objects.last()
        self.assertEqual(
            post.text,
            data['text']
        )
        self.assertEqual(
            post.author.username,
            self.user.username
        )
        self.assertEqual(
            post.group_id,
            data['group']
        )
        self.assertEqual(
            response.status_code,
            200,
            'Функция добавления нового поста работает неправильно'
        )

    def test_new_profile(self):
        response = self.unauthorized_client.get(
            reverse('profile',
                    kwargs={'username': self.user}
                    )
        )
        self.assertEqual(
            response.status_code,
            200,
            'Профайл пользователя не создается после регистрации'
        )

    def test_show_new_post_auth(self):
        cache.clear()
        test_group = Group.objects.create(
            title='tester',
            slug='test',
            description='common'
        )
        post = Post.objects.create(
            text='Это текст публикации',
            author=self.user,
            group=test_group
        )
        urls = (reverse('index'),
                reverse('profile', args=[self.user.username]),
                reverse('group_posts', args=[test_group.slug]))
        for url in urls:
            response_authorized = self.authorized_client.get(url)
            with self.subTest(
                    'Пост не отображается на "' + url + '"' +
                    'для авторизованного пользователя'):
                self.assertEqual(
                    response_authorized.context['page'][0].text,
                    post.text)

    def test_show_new_post_unauth(self):
        cache.clear()
        test_group = Group.objects.create(
            title='tester',
            slug='test',
            description='common'
        )
        post = Post.objects.create(
            text='Это текст публикации',
            author=self.user,
            group=test_group
        )
        urls = (reverse('index'),
                reverse('profile', args=[self.user.username]),
                reverse('group_posts', args=[test_group.slug]))
        for url in urls:
            response_unauthorized = self.unauthorized_client.get(url)
            with self.subTest(
                    'Пост не отображается на "' + url + '"' +
                    'для неавторизованного пользователя'):
                self.assertEqual(
                    response_unauthorized.context['page'][0].text,
                    post.text)

    def test_show_one_new_post(self):
        test_group = Group.objects.create(
            title='tester',
            slug='test',
            description='common'
        )
        post = Post.objects.create(
            text='Это текст публикации',
            author=self.user,
            group=test_group
        )
        url = reverse('post', args=[self.user.username, post.id])
        response_authorized = self.authorized_client.get(url)
        response_unauthorized = self.unauthorized_client.get(url)
        self.assertEqual(
            response_authorized.context['post'].text,
            post.text, 'Пост не отображается для '
                       'авторизованного пользователя')
        self.assertEqual(
            response_unauthorized.context['post'].text,
            post.text, 'Пост не отображается для '
                       'неавторизованного пользователя')

    def test_edit_post(self):
        test_group_edit = Group.objects.create(
            title='tester_edit',
            slug='test_edit',
            description='common_edit'
        )
        post = Post.objects.create(
            text='Это текст публикации',
            author=self.user,
        )
        data = {'text': 'Это отредактированная публикация',
                'group': test_group_edit.id}
        response = self.authorized_client.post(reverse(
            'post_edit', args=[self.user.username, post.id]), data,
            follow=True)
        edit_post = Post.objects.last()
        self.assertEqual(
            edit_post.id,
            post.id
        )
        self.assertEqual(
            edit_post.text,
            data['text']
        )
        self.assertEqual(
            edit_post.group.id,
            data['group']
        )

    def test_specific_page_image(self):
        with open('media/posts/IMG_5233.jpg', 'rb') as img:
            self.authorized_client.post(reverse('new_post'), {
                'image': img,
                'text': 'bla'}
            )
        post = Post.objects.last()
        response = self.authorized_client.get(reverse('post', kwargs={
            'username': self.user.username,
            'post_id': post.pk}))
        self.assertContains(response, '<img')

    def test_page_image_index(self):
        cache.clear()
        with open('media/posts/IMG_5233.jpg', 'rb') as img:
            self.authorized_client.post(reverse('new_post'), {
                'image': img,
                'text': 'bla'}
            )
        response = self.authorized_client.get(reverse('index'))
        self.assertContains(response, '<img')

    def test_page_image_profile(self):
        with open('media/posts/IMG_5233.jpg', 'rb') as img:
            self.authorized_client.post(reverse('new_post'), {
                'image': img,
                'text': 'bla'}
            )
        response = self.authorized_client.get(reverse('profile', kwargs={
            'username': self.user.username}))
        self.assertContains(response, '<img')

    def test_page_image_group(self):
        test_group = Group.objects.create(
            title='tester',
            slug='test',
            description='common'
        )
        with open('media/posts/IMG_5233.jpg', 'rb') as img:
            self.authorized_client.post(reverse('new_post'), {
                'image': img,
                'text': 'bla',
                'group': test_group.id}
            )
        post = Post.objects.last()
        response = self.authorized_client.get(reverse('group_posts', kwargs={
            'slug': post.group.slug})
        )
        self.assertContains(response, '<img')

    def test_page_image_check_text(self):
        with open('media/posts/123.txt', 'rb') as img:
            self.authorized_client.post(reverse('new_post'), {
                'image': img,
                'text': 'bla'}
            )
        count_post = Post.objects.all().count()
        self.assertEqual(count_post, 0)

    def test_cashe(self):
        test_group = Group.objects.create(
            title='tester',
            slug='test',
            description='common'
        )
        post = Post.objects.create(
            text='Это текст публикации',
            author=self.user,
            group=test_group
        )
        url_index = reverse('index')
        response_authorized_index = self.authorized_client.get(url_index)
        self.assertNotContains(
            response_authorized_index,
            post.text)
        url_group = (reverse('group_posts', args=[test_group.slug]))
        response_authorized_group = self.authorized_client.get(url_group)
        self.assertContains(
            response_authorized_group,
            post.text)
        cache.clear()
        post_after_clear = Post.objects.create(
            text='Это текст публикации после очистки кэша',
            author=self.user,
            group=test_group,
        )
        response_authorized_after_clear = self.authorized_client.get(url_index)
        self.assertContains(
            response_authorized_after_clear,
            post_after_clear.text)

    def test_view_post_with_follow(self):
        test_group = Group.objects.create(
            title='tester',
            slug='test',
            description='common'
        )
        data = {'text': 'Это текст публикации второго пользователя',
                'group': test_group.id}
        self.authorized_client.get(reverse(
            'profile_follow', kwargs={'username': self.user_second.username}))
        self.authorized_client_second.post(
            reverse('new_post'), data, follow=True)
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertContains(response, data['text'])

    def test_auth_follow(self):
        current_following_count = self.user.following.count()
        response_follow = self.authorized_client.get(reverse(
                'profile_follow',
                kwargs={'username': self.user_second},)
        )
        self.assertRedirects(
            response_follow, reverse(
                'profile', kwargs={
                'username': self.user_second})
        )
        self.assertEqual(Follow.objects.count(), current_following_count + 1)

    def test_unfollow(self):
        current_following_count = self.user.following.count()
        response_follow = self.authorized_client.get(reverse(
            'profile_follow',
            kwargs={'username': self.user_second})
        )
        response_unfollow = self.authorized_client.get(reverse(
            'profile_unfollow', kwargs={
            'username': self.user_second})
        )
        self.assertRedirects(response_unfollow, reverse(
            'profile', kwargs={
            'username': self.user_second}),
        )
        self.assertEqual(Follow.objects.count(), current_following_count)

    def test_add_comment(self):
        self.authorized_client.post(reverse('new_post'), {
            'text': 'Это текст'})
        post = Post.objects.get(author=self.user)

        response = self.authorized_client.get(reverse(
            'post', args=[
            self.user_second,
            post.pk])
        )
        comment = self.authorized_client_second.post(reverse(
            'add_comment', args=[
            self.user_second,
            post.pk,
            'text'])
        )
        self.assertContains(response, comment)

