from django.urls import path
from .views import OutBoxMailList
urlpatterns = [
    path('outbox/', OutBoxMailList.as_view() )
]
