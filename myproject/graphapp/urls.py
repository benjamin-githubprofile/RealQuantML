from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('export_pdf/', views.export_pdf, name='export_pdf'),
]