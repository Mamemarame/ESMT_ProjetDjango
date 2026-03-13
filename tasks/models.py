from django.db import models
from django.conf import settings
from django.utils import timezone
# Create your models here.

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects_created')

    def __str__(self):
        return self.title

class Task(models.Model):
    STATUS_CHOICES = (
        ('à faire', 'à faire'),
        ('en cours', 'en cours'),
        ('terminé', 'terminé'),
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='à faire')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks_assigned')
    completed_at = models.DateTimeField(null=True, blank=True)

    def is_completed_on_time(self):
        """Vérifie si la tâche a été finie avant la deadline."""
        if self.status != 'terminé':
            return True
        check_time = self.completed_at if self.completed_at else timezone.now()
        return check_time <= self.deadline

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Notif pour {self.recipient.username} : {self.message}"