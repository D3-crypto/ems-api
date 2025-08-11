from django.urls import path
from . import views_mongo as views

urlpatterns = [
    path('add/', views.add_pandit, name='add_pandit'),
    path('delete/', views.delete_pandit, name='delete_pandit'),
    path('list/', views.list_pandits, name='list_pandits'),
    path('location/<str:location>/', views.get_pandit_by_location, name='get_pandit_by_location'),
]
