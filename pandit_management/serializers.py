from rest_framework import serializers
from .models import Pandit


class PanditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pandit
        fields = ['id', 'Pandit_name', 'phone', 'Location', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # Check if pandit with same name and location already exists
        if Pandit.objects.filter(
            Pandit_name=data['Pandit_name'], 
            Location=data['Location']
        ).exists():
            raise serializers.ValidationError(
                "Pandit with this name and location already exists"
            )
        return data


class PanditDeleteSerializer(serializers.Serializer):
    Pandit_name = serializers.CharField(max_length=100)
    Location = serializers.CharField(max_length=100)

    def validate(self, data):
        # Check if pandit exists
        if not Pandit.objects.filter(
            Pandit_name=data['Pandit_name'], 
            Location=data['Location']
        ).exists():
            raise serializers.ValidationError(
                "Pandit with this name and location does not exist"
            )
        return data
