# core/scripts/seed_resources.py

from core.models import Disease, Product, DiseaseResourceRequirement

def run():
    resources = [
        'IV Fluid', 'Paracetamol Tablet', 'Blood Test Kit',
        'Hospital Bed', 'Antimalarial Tablet', 'Mosquito Net'
    ]
    for name in resources:
        Product.objects.get_or_create(name=name)

    def map_resources(disease_name, product_map):
        try:
            disease = Disease.objects.get(name=disease_name)
        except Disease.DoesNotExist:
            print(f"❌ Disease '{disease_name}' not found. Please create it first.")
            return

        for product_name, qty in product_map.items():
            product = Product.objects.get(name=product_name)
            DiseaseResourceRequirement.objects.update_or_create(
                disease=disease, product=product,
                defaults={'quantity_per_patient': qty}
            )
        print(f"✅ Mapped resources for {disease_name}")

    map_resources("Dengue", {
        'IV Fluid': 2,
        'Paracetamol Tablet': 4,
        'Blood Test Kit': 1,
        'Hospital Bed': 1
    })

    map_resources("Malaria", {
        'Antimalarial Tablet': 3,
        'IV Fluid': 1,
        'Mosquito Net': 1,
        'Blood Test Kit': 1
    })

    print("✅ All done.")
