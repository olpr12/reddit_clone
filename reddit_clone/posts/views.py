from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import Like, Comment, Post, Article, Category, Tag, ArticleImage, ArticleVideo
from .forms import CustomUserCreationForm, ArticleForm
from django.core.mail import send_mail
from .models import Subscription
from django.contrib.admin.views.decorators import staff_member_required
from .models import Announcement
# --- Допоміжна функція для обробки тегів ---
def handle_tags(article, tags_raw):
    tags_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
    final_tags = []
    for tag_name in tags_list:
        tag, created = Tag.objects.get_or_create(name=tag_name)
        final_tags.append(tag)
    article.tags.set(final_tags)

# ---------------------------
# ГОЛОВНА СТРІЧКА (Показує опубліковані статті)
# ---------------------------
@login_required
def feed(request):
    # Усі статті
    articles = Article.objects.order_by('-created_at')

    # 🟦 Оголошення (ТОП-5)
    announcements = Announcement.objects.order_by('-created_at')[:5]

    # 🟧 Популярні статті (ТОП-3 за лайками)
    from django.db import models
    popular_articles = Article.objects.annotate(
        likes_count=models.Count('likes')
    ).order_by('-likes_count')[:3]

    # 🟨 Усі категорії
    categories = Category.objects.all()

    # 🟩 Усі теги
    tags = Tag.objects.all()

    return render(request, "feed.html", {
        "articles": articles,
        "announcements": announcements,
        "popular_articles": popular_articles,
        "categories": categories,
        "tags": tags,
    })

# ---------------------------
# Реєстрація
# ---------------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect('feed')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('feed')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})

# ---------------------------
# Логін
# ---------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('feed')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('feed')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

# ---------------------------
# Логаут
# ---------------------------
@login_required
def logout_view(request):
    logout(request)
    return redirect('register')

# ---------------------------
# Профіль
# ---------------------------
@login_required
def profile_view(request):
    my_articles = Article.objects.filter(author=request.user)
    return render(request, 'profile.html', {
        'user': request.user,
        'my_articles': my_articles
    })

# ---------------------------
# Список статей з фільтрами по категоріях і тегах
# ---------------------------
@login_required
def article_list(request):
    articles = Article.objects.filter(status="published")

    category_id = request.GET.get("category")
    if category_id:
        articles = articles.filter(category_id=category_id)

    tag_id = request.GET.get("tag")
    if tag_id:
        articles = articles.filter(tags__id=tag_id)

    categories = Category.objects.all()
    tags = Tag.objects.all()

    return render(request, 'article_list.html', {
        'articles': articles,
        'categories': categories,
        'tags': tags
    })

# ---------------------------
# Детальна стаття
# ---------------------------
@login_required
def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if article.status == "draft" and article.author != request.user:
        return redirect("article_list")

    return render(request, 'article_detail.html', {'article': article})

# ---------------------------
# Створення статті
# ---------------------------
@login_required
def article_create(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")

        # 1. Створюємо статтю
        article = Article.objects.create(
            author=request.user,
            title=title,
            content=content
        )

        # 2. Зберігаємо фото
        for img in request.FILES.getlist("images"):
            ArticleImage.objects.create(article=article, image=img)

        # 3. Зберігаємо відео
        for vid in request.FILES.getlist("videos"):
            ArticleVideo.objects.create(article=article, video=vid)

        # 4. Надсилаємо email усім підписникам
        subs = Subscription.objects.all()

        for s in subs:
            if s.user.email:  # Перевіряємо що є email
                send_mail(
                    subject=f"Нова стаття: {article.title}",
                    message=f"{article.content[:150]}...\n"
                            f"Деталі: http://localhost:8000/article/{article.pk}/",
                    from_email=None,
                    recipient_list=[s.user.email],
                )

        # 5. Показуємо повідомлення
        messages.success(request, "Стаття створена та розіслана!")

        return redirect("article_detail", pk=article.pk)

    return render(request, "article_create.html")

# ---------------------------
# Редагування статті
# ---------------------------
@login_required
def article_edit(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if article.author != request.user:
        return redirect('article_list')

    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES, instance=article)

        if form.is_valid():
            form.save()

            # Обробка тегів
            tags_raw = request.POST.get("tags_list", "")
            handle_tags(article, tags_raw)

            # Нові фото
            new_images = request.FILES.getlist("images")
            for img in new_images:
                ArticleImage.objects.create(article=article, image=img)

            # Нові відео
            new_videos = request.FILES.getlist("videos")
            for vid in new_videos:
                ArticleVideo.objects.create(article=article, video=vid)

            messages.success(request, "Стаття успішно відредагована!")
            return redirect('article_detail', pk=article.pk)
        else:
            messages.error(request, "Помилка при редагуванні статті!")

    else:
        form = ArticleForm(instance=article)

    return render(request, 'article_form.html', {'form': form})

# ---------------------------
# Видалення статті
# ---------------------------
@login_required
def article_delete(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if article.author != request.user:
        return redirect('article_list')

    article.delete()
    messages.success(request, "Стаття видалена.")
    return redirect('article_list')

# ---------------------------
# Лайк статті
# ---------------------------
from django.views.decorators.http import require_POST

@login_required
def like_article(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if request.method == "POST":
        like, created = Like.objects.get_or_create(article=article, user=request.user)

        if not created:
            like.delete()  # Якщо вже є лайк — видаляємо (переключення)

    return redirect('article_detail', pk=pk)


# ---------------------------
# Коментар до статті
# ---------------------------
@login_required
def comment_article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    text = request.POST.get("text")

    if text:
        Comment.objects.create(
            article=article,
            author=request.user,
            text=text,
            is_approved=False  # Після схвалення автором
        )

    return redirect('article_detail', pk=pk)

# ---------------------------
# Підтвердження коментаря
# ---------------------------
@login_required
def approve_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    if request.user != comment.article.author:
        return HttpResponseForbidden("Ви не автор статті")

    comment.is_approved = True
    comment.save()
    return redirect('article_detail', pk=comment.article.pk)

# ---------------------------
# Видалення коментаря
# ---------------------------
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    if request.user != comment.article.author:
        return HttpResponseForbidden("Ви не автор статті")

    comment.delete()
    return redirect('article_detail', pk=comment.article.pk)


@login_required
def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if article.status == "draft" and article.author != request.user:
        return redirect("article_list")

    # Кількість лайків
    likes_count = article.likes.count()
    # Чи лайкнув користувач цю статтю
    user_liked = article.likes.filter(user=request.user).exists()

    return render(request, 'article_detail.html', {
        'article': article,
        'likes_count': likes_count,
        'user_liked': user_liked,
    })

def toggle_subscribe(request):
    if not request.user.is_authenticated:
        return redirect('login')

    sub, created = Subscription.objects.get_or_create(user=request.user)

    if not created:
        sub.delete()
        messages.info(request, "Ви відписались від розсилки!")
    else:
        messages.success(request, "Ви підписалися на нові статті!")

    return redirect('feed')

@staff_member_required
def announcement_create(request):
    if request.method == "POST":
        Announcement.objects.create(
            title=request.POST["title"],
            text=request.POST["text"]
        )
        return redirect("feed")
    return render(request, "announcement_create.html")

@staff_member_required
def announcement_delete(request, pk):
    Announcement.objects.get(pk=pk).delete()
    return redirect("feed")



def create_post_view(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('article_list')  # или куда нужно
    else:
        form = ArticleForm()

    return render(request, 'article_form.html', {'form': form})
