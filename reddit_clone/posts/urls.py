from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    # Головна стрічка
    path('', views.feed, name='feed'),

    # Аутентифікація
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Пости
    path('create/', views.create_post_view, name='create_post'),
    path('article/<int:pk>/like/', views.like_article, name='like_article'),
    path('article/<int:pk>/comment/', views.comment_article, name='comment_article'),

    # Статті
    path('articles/', views.article_list, name='article_list'),
    path('article/<int:pk>/', views.article_detail, name='article_detail'),
    path('article/create/', views.article_create, name='article_create'),
    path('article/edit/<int:pk>/', views.article_edit, name='article_edit'),
    path('article/delete/<int:pk>/', views.article_delete, name='article_delete'),

    # Коментарі - Підтвердження та видалення
    path('comment/<int:comment_id>/approve/', views.approve_comment, name='approve_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('subscribe/', views.toggle_subscribe, name='toggle_subscribe'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
