from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer
from .views import calculate_bonus

class IsProjectCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Project):
            return obj.creator == request.user
        if isinstance(obj, Task):
            return obj.project.creator == request.user
        return False

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.all()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'taches']:
            return [permissions.IsAuthenticated(), IsProjectCreator()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['get', 'post'])
    def taches(self, request, pk=None):
        project = self.get_object()
        if request.method == 'GET':
            tasks = project.tasks.all()
            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data)
        
        # POST - Création d'une tâche dans ce projet
        if project.creator != request.user:
            return Response({"detail": "Seul le créateur peut ajouter des tâches."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = TaskSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from django.db.models import Q
        return Task.objects.filter(project__in=Project.objects.filter(
            Q(creator=self.request.user) | Q(tasks__assigned_to=self.request.user)
        ).distinct())

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Cas spécial : l'assigné peut changer le statut, le créateur peut tout faire.
            # Mais par simplicité et pour coller aux templates :
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if self.action in ['update', 'partial_update']:
            # Seul l'assigné peut modifier sa propre tâche (statut)
            # OU le créateur du projet peut modifier les détails.
            if obj.assigned_to != request.user and obj.project.creator != request.user:
                self.permission_denied(request, message="Permission refusée.")
        if self.action == 'destroy':
            if obj.project.creator != request.user:
                self.permission_denied(request, message="Seul le créateur du projet peut supprimer.")

from rest_framework.views import APIView

class StatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        prime_annuelle = calculate_bonus(request.user, period='annual')
        prime_trimestrielle = calculate_bonus(request.user, period='trimestriel')
        return Response({
            'prime_annuelle': prime_annuelle,
            'prime_trimestrielle': prime_trimestrielle
        })
