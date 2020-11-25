from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse


from posts.models import Post, Group, Comment, Follow, User


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

    def test_show_new_post(self):
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
                reverse('group_posts', args=[test_group.slug]),
                reverse('post', args=[self.user.username, post.id]),
        )
        for url in urls:
            response_authorized = self.authorized_client.get(url)
            cache.clear()
            response_unauthorized = self.unauthorized_client.get(url)
            if url != reverse('post', args=[self.user.username, post.id]):
                post_auth = response_authorized.context['page'][0].text
                post_unauth = response_unauthorized.context['page'][0].text
            else:
                post_auth = response_authorized.context['post'].text
                post_unauth = response_unauthorized.context['post'].text
            with self.subTest(
                    'Пост не отображается на "' + url + '"' +
                    'для авторизованного пользователя'):
                self.assertEqual(post_auth, post.text)
            with self.subTest(
                    'Пост не отображается на "' + url + '"' +
                    'для неавторизованного пользователя'):
                self.assertEqual(post_unauth, post.text)


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
        post.refresh_from_db()
        self.assertEqual(post.text, data['text'])
        self.assertEqual(post.group.id, data['group'])


    def test_specific_page_image(self):
        test_group = Group.objects.create(
            title='tester',
            slug='test',
            description='common'
        )
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B'
        )
        img = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.authorized_client.post(reverse('new_post'), {
            'image': img,
            'text': 'bla',
            'group': test_group.id}
        )
        post = Post.objects.last()
        urls = (reverse('index'),
                reverse('profile', args=[self.user.username]),
                reverse('group_posts', args=[test_group.slug]),
                reverse('post', args=[self.user.username, post.id]),
        )
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertContains(response, '<img')


    def test_page_image_check_text(self):
        small_gif = (b'abc')
        img = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        response = self.authorized_client.post(reverse('new_post'), {
                'image': img,
                'text': 'bla'}
        )
        count_post = Post.objects.all().count()
        self.assertEqual(count_post, 0)
        error = ('Загрузите правильное изображение. '
                 'Файл, который вы загрузили, '
                 'поврежден или не является изображением.')
        self.assertFormError(
            response, 'form', 'image', error
        )


    def test_cache(self):
        url = reverse('index')
        response_authorized_index = self.authorized_client.get(url)
        Post.objects.create(
            text='Это текст публикации',
            author=self.user,
        )
        self.assertEqual(
            self.authorized_client.get(url).content,
            response_authorized_index.content
        )
        cache.clear()
        self.assertNotEqual(
            self.authorized_client.get(url).content,
            response_authorized_index.content
        )


    def test_view_post_with_follow(self):
        data = {'text': 'Это текст публикации второго пользователя'}
        Follow.objects.create(
            author=self.user_second,
            user=self.user
        )
        Post.objects.create(
            author=self.user_second,
            text=data['text']
        )
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertContains(response, data['text'])


    def test_auth_follow(self):
        current_following_count = self.user.following.count()
        response_follow = self.authorized_client.get(reverse(
                'profile_follow',
                kwargs={'username': self.user_second},)
        )
        follow_author_user = Follow.objects.filter(
            author=self.user_second,
            user=self.user
        )
        self.assertRedirects(
            response_follow, reverse(
                'profile', kwargs={
                'username': self.user_second})
        )
        self.assertEqual(
            follow_author_user.count(),
            current_following_count + 1
        )


    def test_unfollow(self):
        current_following_count = self.user.following.count()
        follow_author_user = Follow.objects.filter(
            author=self.user_second,
            user=self.user)
        response_unfollow = self.authorized_client.get(reverse(
            'profile_unfollow', kwargs={
            'username': self.user_second})
        )
        self.assertRedirects(response_unfollow, reverse(
            'profile', kwargs={
            'username': self.user_second}),
        )
        self.assertEqual(
            follow_author_user.count(),
            current_following_count
        )


    def test_add_comment_auth(self):
        post = Post.objects.create(
            text='Это текст публикации',
            author=self.user,
        )
        count = Comment.objects.count()
        self.authorized_client_second.post(reverse(
            'add_comment', kwargs={
            'username': self.user,
            'post_id': post.pk}), {
            'text': 'коммент',
            'post': post.pk},
            follow=True,
        )
        count_comment = Comment.objects.count()
        comment_last = Comment.objects.last()
        response = self.authorized_client.get(reverse(
            'post', kwargs={
            'username': self.user,
            'post_id': post.pk})
        )
        self.assertEqual(count_comment, count + 1)
        self.assertEqual(response.context['comments'][0].text,
            comment_last.text,
        )


    def test_add_comment_unauth(self):
        post = Post.objects.create(
            text='Это текст публикации',
            author=self.user,
        )
        self.unauthorized_client.post(reverse(
            'add_comment', kwargs={
            'username': self.user,
            'post_id': post.pk}), {
            'text': 'коммент',
            'post': post.pk},
            follow=True,
        )
        comment_count = Comment.objects.all().count()
        self.assertEqual(comment_count, 0)
