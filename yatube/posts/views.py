from django.shortcuts import redirect, render, get_object_or_404
from .models import Post, Group, User
from .forms import PostForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


def index(request):
    post_list = Post.objects.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "index.html", {"page": page, "paginator": paginator})


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
    form = PostForm(request.POST)
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
    return render(request, 'profile.html',
                  {
                      'page': page,
                      'paginator': paginator,
                      'post_count': post_count,
                      'author': author
                  })


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author=author, id=post_id)
    return render(request, 'post.html',
                  {
                      'author': author, 'post': post
                  })


@login_required
def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id)
    if profile == post.author:
        if request.method == "POST":
            form = PostForm(request.POST)
            if form.is_valid():
                edit_post = form.save(commit=False)
                edit_post.author = post.author
                edit_post.id = post.id
                edit_post.pub_date = post.pub_date
                edit_post.save()
                return redirect("post", username=username, post_id=post_id)
        else:
            form = PostForm(instance=post)
        context = {
            "form": form,
            "post": post,
            "username": username,
            "post_id": post_id,
        }
        return render(request, "new.html", context)
    return render(request, "index.html")


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)

