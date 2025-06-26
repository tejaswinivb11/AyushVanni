from rest_framework import serializers
from .models import User ,DiseaseCase , Product , Inventory , Hospital

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'userName', 'password', 'role', 'hospitalId']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Custom creation logic if needed (like hashing password)
        user = User.objects.create(**validated_data)
        return user
 

class DiseaseCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiseaseCase
        fields = '__all__'

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)

    class Meta:
        model = Inventory
        fields = ['id', 'hospital', 'hospital_name', 'product', 'product_name', 'quantity', 'threshold']

class AddRemoveInventorySerializer(serializers.Serializer):
    hospital_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name'] 