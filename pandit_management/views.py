from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings

# Dynamic model imports based on database configuration
if getattr(settings, 'USE_MONGODB', False):
    from mongo_models import MongoPandit as Pandit
else:
    from .models import Pandit

from .serializers import PanditSerializer, PanditDeleteSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_pandit(request):
    """Add a new pandit"""
    serializer = PanditSerializer(data=request.data)
    if serializer.is_valid():
        pandit = serializer.save()
        return Response({
            'message': 'Pandit added successfully',
            'pandit': PanditSerializer(pandit).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_pandit(request):
    """Delete a pandit by name and location"""
    serializer = PanditDeleteSerializer(data=request.data)
    if serializer.is_valid():
        pandit_name = serializer.validated_data['Pandit_name']
        location = serializer.validated_data['Location']
        
        try:
            pandit = Pandit.objects.get(
                Pandit_name=pandit_name,
                Location=location
            )
            pandit.delete()
            
            return Response({
                'message': 'Pandit deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Pandit.DoesNotExist:
            return Response({
                'error': 'Pandit not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_pandits(request):
    """List all pandits"""
    pandits = Pandit.objects.all()
    serializer = PanditSerializer(pandits, many=True)
    return Response({
        'pandits': serializer.data,
        'count': len(serializer.data)
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pandit_by_location(request, location):
    """Get pandits by location"""
    pandits = Pandit.objects.filter(Location__icontains=location)
    serializer = PanditSerializer(pandits, many=True)
    return Response({
        'pandits': serializer.data,
        'count': len(serializer.data),
        'location': location
    }, status=status.HTTP_200_OK)
