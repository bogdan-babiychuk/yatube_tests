from django.shortcuts import render, get_object_or_404, redirect
from .models import Group, Post, User
from django.contrib.auth.decorators import login_required
from .forms import PostForm
from users.utils import paginate

RECORD: int = 10
NUMBER_30: int = 30


def index(request):
    post_list = Post.objects.all()
    page_obj = paginate(request, post_list, RECORD)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_list.all()
    page_obj = paginate(request, posts, RECORD)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    title = 'Профайл пользователя'
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    count_posts = posts.count()
    page_obj = paginate(request, posts, RECORD)
    context = {
        'author': author,
        'count_posts': count_posts,
        'page_obj': page_obj,
        'title': title, }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    title = 'Пост'
    post = get_object_or_404(Post, id=post_id)
    short_word = post.text[:NUMBER_30]
    posts_count = Post.objects.filter(author=post.author).count()
    context = {
        'short_word': short_word,
        'title': title,
        'post': post,
        'posts_count': posts_count,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    title = 'Добавить запись'
    form = PostForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.author = request.user
            new_form.save()
            return redirect("posts:profile", username=request.user)
        return render(request, 'posts/create_post.html',
                      {'form': form, 'title': title})

    return render(request, 'posts/create_post.html',
                  {'title': 'Добавление статьи', 'form': form,
                   'is_edit': False, })


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, 'posts/post_edit.html', context)
