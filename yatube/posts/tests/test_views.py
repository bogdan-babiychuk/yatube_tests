from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from posts.models import Group, Post, User


class Container(dict):
    """Overload the items method to retain duplicate keys."""

    def __init__(self, items):
        self[""] = ""
        self._items = items

    def items(self):
        return self._items


class TestView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем неавторизованный клиент
        cls.guest_client = Client()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='wtf')
        # Создаем второй клиент
        cls.authorized_client = Client()
        # Авторизуем пользователя
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='test-группа',
            slug='test-slug',
            description='test-описание группы'
        )
        cls.post = Post.objects.create(
            text='text-текст',
            author=cls.user,
            group=cls.group,
        )

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': (reverse('posts:index')),
            'posts/group_list.html': (reverse('posts:group_posts',
                                      kwargs={'slug': 'test-slug'})),
            'posts/profile.html': reverse(
                'posts:profile',
                args=[get_object_or_404(User, username='wtf')]),
            'posts/post_detail.html': (reverse('posts:post_detail',
                                       kwargs={'post_id': '1'})),
            'posts/post_edit.html':
                reverse('posts:post_edit', kwargs={'post_id': '1'}),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        post_object = response.context['page_obj'][0]
        author_0 = post_object.author
        text_0 = post_object.text
        group_0 = post_object.group
        self.assertEqual(author_0, self.user)
        self.assertEqual(text_0, self.post.text)
        self.assertEqual(group_0, self.post.group)

    def test_group_posts_pages_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:group_posts',
                                                 kwargs={'slug': 'test-slug'}))
        self.assertIn('group', response.context)
        post_object = response.context['group']
        title_0 = post_object.title
        slug_0 = post_object.slug
        description_0 = post_object.description
        self.assertEqual(title_0, self.group.title)
        self.assertEqual(slug_0, self.group.slug)
        self.assertEqual(description_0, self.group.description)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': 'wtf'}))
        self.assertEqual(response.context['page_obj'][0].author.username,
                         'wtf')
        self.assertEqual(response.context['page_obj'][0].text,
                         'text-текст')
        self.assertEqual(response.context['page_obj'][0].group.title,
                         'test-группа')
        self.assertEqual(response.context['author'],
                         self.user)

    def test_post_detail_page_show_correct_context(self):
        response = self.guest_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': '1'}
        ))
        self.assertEqual(response.context['post'], self.post)

    def test_post_create_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id': '1'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='wtf')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.group = Group.objects.create(
            title='test-группа',
            slug='test-slug',
            description='test-описание группы'
        )

        self.bilk_post: list = []
        for i in range(13):
            self.bilk_post.append(Post(text=f'Тестовый текст {i}',
                                  group=self.group,
                                  author=self.user))
        Post.objects.bulk_create(self.bilk_post)

    def test_first_page_index_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_index_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_group_posts_contains_ten_records(self):
        response = self.client.get(reverse('posts:group_posts',
                                           kwargs={'slug': 'test-slug'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_group_posts_contains_three_records(self):
        response = self.client.get(reverse('posts:group_posts',
                                           kwargs={'slug':
                                                   'test-slug'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_profile_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:profile',
            args=[get_object_or_404(User,
                                    username='wtf')]))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_profile_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:profile',
            args=[get_object_or_404(User,
                                    username='wtf')]) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
