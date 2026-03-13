import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import User
from tasks.models import Project, Task
from django.utils import timezone
from datetime import timedelta

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def professor_user(db):
    return User.objects.create_user(username='prof', password='password', role='Professeur')

@pytest.fixture
def student_user(db):
    return User.objects.create_user(username='student', password='password', role='Etudiant')

@pytest.mark.django_db
def test_bonus_calculation(professor_user):
    # Créer un projet et une tâche terminée à temps
    project = Project.objects.create(title="Test Project", creator=professor_user)
    deadline = timezone.now() + timedelta(days=1)
    Task.objects.create(
        project=project,
        title="Task 1",
        description="Desc",
        deadline=deadline,
        status='terminé',
        assigned_to=professor_user
    )
    
    from tasks.views import calculate_bonus
    assert calculate_bonus(professor_user, period='trimestriel') == 100000

@pytest.mark.django_db
def test_student_cannot_assign_professor(api_client, student_user, professor_user):
    api_client.force_authenticate(user=student_user)
    project = Project.objects.create(title="Student Project", creator=student_user)
    
    url = reverse('project-taches', args=[project.id])
    data = {
        "title": "Invalid Task",
        "description": "Student assigning Prof",
        "deadline": timezone.now() + timedelta(days=1),
        "assigned_to": professor_user.id
    }
    response = api_client.post(url, data)
    assert response.status_code == 400
    assert "Un étudiant ne peut pas assigner un professeur !" in str(response.data)

@pytest.mark.django_db
def test_project_permissions(api_client, student_user, professor_user):
    project = Project.objects.create(title="Prof Project", creator=professor_user)
    api_client.force_authenticate(user=student_user)
    
    url = reverse('project-detail', args=[project.id])
    response = api_client.delete(url)
    assert response.status_code == 403 # Only creator can delete
