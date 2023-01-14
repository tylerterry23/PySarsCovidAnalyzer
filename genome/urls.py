from django.urls import path
from . import views

urlpatterns = [
    path("", views.UploadTxt.as_view(), name="upload_txt")
]
