from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from mongo_models import MongoPandit


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_pandit(request):
    """Add a new pandit using MongoDB"""
    pandit_name = request.data.get('Pandit_name')
    phone = request.data.get('phone')
    location = request.data.get('Location')
    
    if not all([pandit_name, phone, location]):
        return Response({
            'error': 'Pandit_name, phone, and Location are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        pandit = MongoPandit.create_pandit(
            pandit_name=pandit_name,
            phone=phone,
            location=location
        )
        
        return Response({
            'message': 'Pandit added successfully',
            'pandit': pandit.to_dict()
        }, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_pandit(request):
    """Delete a pandit by name and location using MongoDB"""
    pandit_name = request.data.get('Pandit_name')
    location = request.data.get('Location')
    
    if not all([pandit_name, location]):
        return Response({
            'error': 'Pandit_name and Location are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    pandit = MongoPandit.get_by_name_and_location(pandit_name, location)
    
    if not pandit:
        return Response({
            'error': 'Pandit not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    pandit.delete()
    
    return Response({
        'message': 'Pandit deleted successfully'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_pandits(request):
    """List all pandits using MongoDB"""
    pandits = MongoPandit.get_all()
    pandit_data = [pandit.to_dict() for pandit in pandits]
    
    return Response({
        'message': 'Pandits retrieved successfully',
        'pandits': pandit_data,
        'count': len(pandit_data)
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pandit_by_location(request, location):
    """Get pandits by location using MongoDB"""
    pandits = MongoPandit.get_by_location(location)
    pandit_data = [pandit.to_dict() for pandit in pandits]
    
    return Response({
        'message': f'Pandits in {location} retrieved successfully',
        'pandits': pandit_data,
        'count': len(pandit_data),
        'location': location
    }, status=status.HTTP_200_OK)
