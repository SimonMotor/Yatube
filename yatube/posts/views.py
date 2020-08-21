from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow


def index(request):
    post_list = Post.objects.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "index.html",
                  {"page": page, "paginator": paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "group.html",
                  {
                      "group": group,
                      "posts": posts,
                      "page": page,
                      "paginator": paginator
                  })


@login_required
def new_post(request):
    form = PostForm(request.POST, files=request.FILES or None)
    if request.method != "POST":
        form = PostForm()
        return render(request, "new.html", {"form": form})
    elif not form.is_valid():
        return render(request, "new.html", {"form": form})
    post_get = form.save(commit=False)
    post_get.author = request.user
    post_get.save()
    return redirect("index")


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_count = Post.objects.filter(author=author).count()
    post_list = Post.objects.filter(author=author).order_by("-pub_date")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    if request.user.is_anonymous:
        following = None
    else:
        following = Follow.objects.filter(user=request.user, author=author).exists()
    return render(request, "profile.html",
                  {
                      "page": page,
                      "paginator": paginator,
                      "post_count": post_count,
                      "following": following,
                      "author": author
                  })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm()
    comment = Comment.objects.filter(post_id=post_id)
    return render(request, "post.html",
                  {
                      "author": post.author,
                      "post": post,
                      "form": form,
                      "comment": comment
                  })


@login_required
def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    if request.user != profile:
        return redirect("post", username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("post", username=request.user.username,
                            post_id=post_id)

    return render(request, "new.html", {
        "form": form,
        "post": post,
        "username": username,
        "post_id": post_id,
        "image": request.FILES
        })

@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return render(request, "includes/comments.html", {"form": form, "post": post})
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect("post", username=username,
                    post_id=post_id)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html",
                  {"page": page, "paginator": paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect("profile", username=username)
    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("profile", username=username)
