from rest_framework import serializers
from .models import Project, Task
from accounts.serializers import UserSerializer

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    statut = serializers.CharField(source='status', required=False)
    
    class Meta:
        model = Task
        fields = ['id', 'project', 'title', 'description', 'deadline', 'status', 'statut', 'assigned_to', 'assigned_to_details']
        extra_kwargs = {
            'status': {'required': False},
            'project': {'read_only': True}
        }

    def validate(self, data):
        request = self.context.get('request')
        assigned_to = data.get('assigned_to')
        
        if request and request.user.role == 'Etudiant' and assigned_to and assigned_to.role == 'Professeur':
            raise serializers.ValidationError({"assigned_to": "Un étudiant ne peut pas assigner un professeur !"})
        return data

class ProjectSerializer(serializers.ModelSerializer):
    creator_details = UserSerializer(source='creator', read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'creator', 'creator_details', 'tasks']
        read_only_fields = ['creator']
