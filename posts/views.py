from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect

from .models import Post, Group, Comment, Follow
from .forms import PostForm, CommentForm

User = get_user_model()


@cache_page(1, key_prefix= 'index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 8)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {
        'page': page,
        'paginator': paginator,
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 8)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {
        'group': group,
        'page': page,
        'paginator': paginator,
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if not form.is_valid():
        return render(request, 'new_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('index')


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 8)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = author.following.filter(user=request.user.id).exists()
    return render(request, 'profile.html', {
        'page': page,
        'author': author,
        'paginator': paginator,
        'following': following,
    })


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    form = CommentForm()
    comments = post.comment_post.all()
    return render(request, 'post.html', {
        'form': form,
        'author': author,
        'post': post,
        'comments': comments
    })


def post_edit(request, username, post_id):
    if request.user.username != username:
        return redirect('post', username=username, post_id=post_id)
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if not form.is_valid():
        return render(request, 'new_post.html', {
            'form': form,
            'post': post,
        })
    form.save()
    return redirect('post', username=username, post_id=post_id)


def page_not_found(request, exception):
    return render(request, "misc/404.html", {
        "path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)

@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = get_object_or_404(User, username=request.user)
    form = CommentForm(request.POST or None)
    comments = post.comment_post.all()
    if not form.is_valid():

        return redirect(request, 'post', {
            'form': form,
            'post': post,
            'comments': comments})
    comment = form.save(commit=False)
    comment.post = post
    comment.author = author
    comment.save()
    return redirect('post', username, post_id)

@login_required
def follow_index(request):
    post = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post, 8)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {
        'page': page,
        'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get(user=user, author=author).delete()
    return redirect('profile', username=username)
