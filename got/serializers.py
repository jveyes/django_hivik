from rest_framework import serializers
from .models import Asset, System 

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        
        # Convertir campos numéricos a float si es necesario
        for field in ['eslora', 'manga', 'puntal', 'calado_maximo']:
            if field in rep:
                rep[field] = float(rep[field])
        
        return rep
    

class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = '__all__'