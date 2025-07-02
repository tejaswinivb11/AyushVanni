from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, DiseaseCase, Inventory, Hospital, Outbreak, Product, InventoryNotification
from .serializers import UserSerializer, DiseaseCaseSerializer, InventorySerializer, HospitalSerializer, AddRemoveInventorySerializer , ProductSerializer

class RegisterView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                # Check if the username already exists
                if User.objects.filter(userName=serializer.validated_data['userName']).exists():
                    return Response({'message': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
                # Create the user
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            userName = request.data.get('userName')
            password = request.data.get('password')

            # Hardcoded admin login
            if userName == 'admin' and password == 'admin@123':
                return Response({'response': 'admin'}, status=status.HTTP_200_OK)

            user = User.objects.get(userName=userName)
            if user.password == password:
                if user.role == 'hospitalAdmin':
                    if user.hospitalId:
                        return Response({'response': user.hospitalId}, status=status.HTTP_200_OK)
                    else:
                        return Response({'response': 'Hospital ID not linked'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'response': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'response': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'response': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# core/views.py
import joblib, numpy as np
from datetime import timedelta
from django.db.models import Avg

from geopy.distance import geodesic
from datetime import timedelta
import joblib
import numpy as np
from django.db.models import Avg
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.db.models import Sum

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta
from django.db.models import Avg, Sum
from geopy.distance import geodesic
import numpy as np
import joblib

from .models import DiseaseCase, DiseaseResourceRequirement, Inventory, Hospital, Outbreak
from .serializers import DiseaseCaseSerializer

class DiseaseCaseCreateView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            # Load ML model
            clf = joblib.load(r"I:\mini project\ayush\core\outbreak_global_model.pkl")
            data = request.data

            # Check if case already exists
            existing = DiseaseCase.objects.filter(
                hospital_id=data.get('hospital'),
                disease_id=data.get('disease'),
                date_reported=data.get('date_reported')
            ).first()

            if existing:
                existing.daily_cases += int(data.get('daily_cases', 0))
                existing.humidity = float(data.get('humidity', existing.humidity))
                existing.temperature = float(data.get('temperature', existing.temperature))
                case = existing
                case.save()
            else:
                serializer = DiseaseCaseSerializer(data=data)
                if not serializer.is_valid():
                    return Response({'response': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                case = serializer.save()

            # Compute 7-day average
            week_ago = case.date_reported - timedelta(days=7)
            avg = DiseaseCase.objects.filter(
                hospital=case.hospital,
                disease=case.disease,
                date_reported__gt=week_ago,
                date_reported__lt=case.date_reported
            ).aggregate(avg=Avg('daily_cases'))['avg'] or 0.0
            case.avg_7day_cases = avg
            case.save()

            # Step 1: Total cases of that disease in the hospital
            total_cases = DiseaseCase.objects.filter(
                hospital=case.hospital,
                disease=case.disease
            ).aggregate(total=Sum('daily_cases'))['total'] or 0

            # Step 2: Get required resources
            requirements = DiseaseResourceRequirement.objects.filter(disease=case.disease)
            if not requirements.exists():
                return Response({
                    'response': 'No resource requirements mapped for this disease. Please update DiseaseResourceRequirement.'
                }, status=status.HTTP_400_BAD_REQUEST)

            insufficient_resources = []
            suggestions = []

            for req in requirements:
                total_needed = req.quantity_per_patient * total_cases

                # Check inventory for this product
                inventory = Inventory.objects.filter(hospital=case.hospital, product=req.product).first()
                available = inventory.quantity if inventory else 0

                if available < total_needed:
                    insufficient_resources.append({
                        'product': req.product.name,
                        'required': total_needed,
                        'available': available
                    })

                    # Find suggestions from nearby hospitals
                    nearby = []
                    requester = case.hospital
                    for hospital in Hospital.objects.exclude(id=requester.id):
                        inv = Inventory.objects.filter(hospital=hospital, product=req.product).first()
                        if inv and inv.quantity > inv.threshold:
                            dist = geodesic(
                                (requester.latitude, requester.longitude),
                                (hospital.latitude, hospital.longitude)
                            ).km
                            nearby.append({
                                'hospital_id': hospital.id,
                                'hospital_name': hospital.name,
                                'available_quantity': inv.quantity,
                                'product': req.product.name,
                                'distance_km': round(dist, 2)
                            })

                    if nearby:
                        nearby.sort(key=lambda x: x['distance_km'])
                        suggestions.append({
                            'resource': req.product.name,
                            'required': total_needed,
                            'available': available,
                            'suggested_hospitals': nearby[:3]
                        })

            # Step 3: If shortages, return early before outbreak prediction
            if insufficient_resources:
                return Response({
                    'response': 'Insufficient resources!',
                    'shortages': insufficient_resources,
                    'suggestions': suggestions
                }, status=status.HTTP_200_OK)

            # Step 4: Predict outbreak (only if resources are sufficient)
            features = np.array([[
                case.hospital.id,
                case.disease.id,
                case.daily_cases,
                case.humidity,
                case.temperature
            ]])
            pred = clf.predict(features)[0]

            if pred == 1:
                outbreak, created = Outbreak.objects.get_or_create(
                    hospital=case.hospital,
                    disease=case.disease,
                    status='active',
                    defaults={'start_date': case.date_reported}
                )
                if not created and outbreak.status != 'active':
                    outbreak.start_date = case.date_reported
                    outbreak.status = 'active'
                outbreak.save()
                return Response({'response': 'Resources are sufficient. Outbreak detected!'}, status=200)

            return Response({'response': 'Resources are sufficient. No outbreak detected.'}, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
from rest_framework.views import APIView


from core.models import Inventory, InventoryNotification

from geopy.distance import geodesic

class InventoryListView(APIView):
    def get(self, request, hospital_id):
        try:
            inventory = Inventory.objects.filter(hospital_id=hospital_id)
            serializer = InventorySerializer(inventory, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddInventoryView(APIView):
    def post(self, request):
        try:
            serializer = AddRemoveInventorySerializer(data=request.data)
            if serializer.is_valid():
                hospital_id = serializer.validated_data['hospital_id']
                product_id = serializer.validated_data['product_id']
                quantity = serializer.validated_data['quantity']

                inv, _ = Inventory.objects.get_or_create(
                    hospital_id=hospital_id,
                    product_id=product_id,
                    defaults={'quantity': 0}
                )
                inv.quantity += quantity
                inv.save()

                return Response({'message': 'Inventory added successfully!'}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RemoveInventoryView(APIView):
    def post(self, request):
        try:
            serializer = AddRemoveInventorySerializer(data=request.data)
            if serializer.is_valid():
                hospital_id = serializer.validated_data['hospital_id']
                product_id = serializer.validated_data['product_id']
                quantity = serializer.validated_data['quantity']

                try:
                    inv = Inventory.objects.get(hospital_id=hospital_id, product_id=product_id)
                    if inv.quantity < quantity:
                        return Response({'error': 'Not enough inventory available!'}, status=400)

                    # Subtract the quantity from the inventory
                    inv.quantity -= quantity
                    inv.save()

                    # If the inventory goes below the threshold or is emptied, trigger suggestions
                    if inv.quantity < inv.threshold or inv.quantity == 0:
                        msg = f"Inventory low for {inv.product.name} in {inv.hospital.name}"
                        InventoryNotification.objects.create(inventory=inv, message=msg)

                        # Now trigger Inventory suggestion logic for hospitals with surplus stock
                        suggestions = self.get_inventory_suggestions(hospital_id, product_id)

                        return Response({
                            'message': 'Inventory removed successfully!',
                            'suggestions': suggestions
                        }, status=200)

                    return Response({'message': 'Inventory removed successfully!'}, status=200)
                except Inventory.DoesNotExist:
                    return Response({'error': 'Inventory not found'}, status=404)
            return Response(serializer.errors, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_inventory_suggestions(self, requesting_hospital_id, product_id):
        try:
            requester = Hospital.objects.get(id=requesting_hospital_id)
            hospitals = Hospital.objects.exclude(id=requesting_hospital_id)
            suggestions = []

            for hospital in hospitals:
                try:
                    inv = Inventory.objects.get(hospital=hospital, product_id=product_id)
                    if inv.quantity > inv.threshold:
                        # Calculate distance between the hospitals
                        dist = geodesic(
                            (requester.latitude, requester.longitude),
                            (hospital.latitude, hospital.longitude)
                        ).km
                        suggestions.append({
                            'hospital_id': hospital.id,
                            'hospital_name': hospital.name,
                            'available_quantity': inv.quantity,
                            'distance_km': round(dist, 2)
                        })
                except Inventory.DoesNotExist:
                    continue

            suggestions.sort(key=lambda x: x['distance_km'])
            return suggestions
        except Hospital.DoesNotExist:
            return []

class InventorySuggestionView(APIView):
    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            requesting_hospital_id = request.data.get('hospital_id')

            try:
                requester = Hospital.objects.get(id=requesting_hospital_id)
                hospitals = Hospital.objects.exclude(id=requesting_hospital_id)
                suggestions = []

                for hospital in hospitals:
                    try:
                        inv = Inventory.objects.get(hospital=hospital, product_id=product_id)
                        if inv.quantity > inv.threshold:
                            dist = geodesic(
                                (requester.latitude, requester.longitude),
                                (hospital.latitude, hospital.longitude)
                            ).km
                            suggestions.append({
                                'hospital_id': hospital.id,
                                'hospital_name': hospital.name,
                                'available_quantity': inv.quantity,
                                'distance_km': round(dist, 2)
                            })
                    except Inventory.DoesNotExist:
                        continue

                suggestions.sort(key=lambda x: x['distance_km'])
                return Response({'suggestions': suggestions})
            except Hospital.DoesNotExist:
                return Response({'error': 'Invalid hospital ID'}, status=400)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ProductListView(APIView):
    
    # GET API to retrieve product(s)
    def get(self, request, *args, **kwargs):
        product_id = request.query_params.get('id', None)  # Getting the product ID from query parameters
        if product_id:
            try:
                # Retrieve the product by ID (either integer or string)
                product = Product.objects.get(id=product_id)
                serializer = ProductSerializer(product)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # If no ID is provided, retrieve all products
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST API to create a product
    def post(self, request, *args, **kwargs):
        product_name = request.data.get('name', None)  # Getting the product name from the request body
        if product_name:
            # Check if product already exists
            if Product.objects.filter(name=product_name).exists():
                return Response({'message': 'Product already exists'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create a new product
            product = Product.objects.create(name=product_name)
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response({'error': 'Product name is required'}, status=status.HTTP_400_BAD_REQUEST)
    

    # views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.models import Disease, Product, DiseaseResourceRequirement

class DiseaseResourceView(APIView):
    def post(self, request):
        disease_name = request.data.get("disease")
        resources = request.data.get("resources", {})

        if not disease_name or not isinstance(resources, dict):
            return Response({"error": "Invalid data."}, status=status.HTTP_400_BAD_REQUEST)

        disease, _ = Disease.objects.get_or_create(name=disease_name)

        for product_name, qty in resources.items():
            product, _ = Product.objects.get_or_create(name=product_name)
            DiseaseResourceRequirement.objects.update_or_create(
                disease=disease,
                product=product,
                defaults={"quantity_per_patient": qty}
            )

        return Response({"message": f"Resources mapped to disease '{disease_name}'."})
