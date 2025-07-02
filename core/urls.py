from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('cases/', views.DiseaseCaseCreateView.as_view(), name='create-case'),
    path('inventory/<int:hospital_id>/', views.InventoryListView.as_view(), name='inventory-list'),
    path('inventory/add/', views.AddInventoryView.as_view(), name='inventory-add'),
    path('inventory/remove/', views.RemoveInventoryView.as_view(), name='inventory-remove'),
    path('inventory/suggestions/', views.InventorySuggestionView.as_view(), name='inventory-suggestions'),
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('disease-resources/', views.DiseaseResourceView.as_view(), name='disease-resources'),
]