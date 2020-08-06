from django.shortcuts import render, get_object_or_404
from .models import Post, Group
from .forms import PostForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def index(request):
    latest = Post.objects.order_by("-pub_date")[:11]
    return render(request, "index.html", {"posts": latest})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    return render(request, "group.html", {"group": group, "posts": posts})


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
