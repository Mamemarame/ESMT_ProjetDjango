from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ProjectViewSet, TaskViewSet, StatisticsView

router = DefaultRouter()
router.register(r'projets', ProjectViewSet, basename='project')
router.register(r'taches', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/primes/', StatisticsView.as_view(), name='api_primes'),
]
