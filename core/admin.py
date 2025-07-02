from django.contrib import admin

# Register your models here.
from .models import Hospital, Product, Inventory, Disease, DiseaseCase, Outbreak ,User, InventoryNotification,DiseaseResourceRequirement
admin.site.register(Hospital)
admin.site.register(Product)
# ... register others
admin.site.register(Inventory)
admin.site.register(Disease)
admin.site.register(DiseaseCase)
admin.site.register(Outbreak)
admin.site.register(User)
admin.site.register(InventoryNotification)
admin.site.register(DiseaseResourceRequirement)

