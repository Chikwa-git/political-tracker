from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("deputy/", views.deputy, name="deputy"),
    path("search/", views.search, name="search"),
    path("compare/", views.compare, name="compare"),
    path("deputy-data/", views.deputy_data, name="deputy_data"),
    path("ai-analysis/", views.ai_analysis, name="ai_analysis"),
]