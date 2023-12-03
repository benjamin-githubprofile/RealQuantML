from django.urls import include, path

urlpatterns = [
    path('graphapp/', include('graphapp.urls')),
]
