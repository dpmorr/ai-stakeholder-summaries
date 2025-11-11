"""URL configuration for summary app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SummaryViewSet, GeneratedSummaryViewSet

router = DefaultRouter()
router.register(r'summaries', SummaryViewSet, basename='summary')
router.register(r'generated-summaries', GeneratedSummaryViewSet, basename='generated-summary')

urlpatterns = [
    path('', include(router.urls)),
]
