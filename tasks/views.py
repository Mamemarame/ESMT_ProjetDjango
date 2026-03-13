from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Project, Task, Notification
from accounts.models import User
from django.utils import timezone
from django.db.models import Q


def calculate_bonus(user, period='annual'):
    if user.role != 'Professeur':
        return 0

    now = timezone.now()
    tasks = user.tasks_assigned.all()

    if period == 'trimestriel':
        # Déterminer le trimestre actuel (1-4)
        quarter = (now.month - 1) // 3 + 1
        months = [1,2,3] if quarter==1 else [4,5,6] if quarter==2 else [7,8,9] if quarter==3 else [10,11,12]
        tasks = tasks.filter(deadline__year=now.year, deadline__month__in=months)
    else:
        # Période annuelle par défaut
        tasks = tasks.filter(deadline__year=now.year)

    if not tasks.exists():
        return 0

    total = tasks.count()
    on_time = sum(1 for t in tasks if t.status == 'terminé' and t.is_completed_on_time())
    ratio = (on_time / total) * 100

    if ratio == 100:
        return 100000
    elif ratio >= 90:
        return 30000
    return 0


@login_required
def dashboard(request):

    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')

    projects = Project.objects.filter(
        Q(creator=request.user) | Q(tasks__assigned_to=request.user)
    ).distinct()

    status_filter = request.GET.get('status')
    tasks = Task.objects.all()

    if status_filter:
        tasks = tasks.filter(status=status_filter)


    if request.user.role == 'Etudiant':
        tasks = tasks.filter(
            Q(assigned_to=request.user) | Q(project__creator=request.user)
        ).distinct()

    context = {
        'projects': projects,
        'tasks': tasks,
        'prime_annuelle': calculate_bonus(request.user, period='annual'),
        'prime_trimestrielle': calculate_bonus(request.user, period='trimestriel'),
        'status_choices': Task.STATUS_CHOICES,
        'users': User.objects.all(),
        'now': timezone.now(),
        'today': date.today(),
        'notifications': notifications,
    }
    return render(request, 'tasks/dashboard.html', context)


@login_required
def create_project(request):
    if request.method == "POST":
        Project.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            creator=request.user
        )
        return redirect('dashboard')
    return render(request, 'tasks/create_project.html')


@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if project.creator != request.user:
        return render(request, 'tasks/error.html', {'msg': "Seul le créateur peut supprimer ce projet."})
    project.delete()
    return redirect('dashboard')


@login_required
def create_task(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if project.creator != request.user:
        return render(request, 'tasks/error.html', {'msg': "Permission refusée : vous n'êtes pas le créateur."})

    if request.method == "POST":
        assigned_id = request.POST.get('assigned_to')
        assigned_user = get_object_or_404(User, id=assigned_id)

        if request.user.role == 'Etudiant' and assigned_user.role == 'Professeur':
            return render(request, 'tasks/create_task.html', {
                'project': project,
                'users': User.objects.all(),
                'error': "Un étudiant ne peut pas assigner un professeur !"
            })

        Task.objects.create(
            project=project,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            deadline=request.POST.get('deadline'),
            assigned_to=assigned_user
        )
        return redirect('dashboard')

    return render(request, 'tasks/create_task.html', {'project': project, 'users': User.objects.all()})


@login_required
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.assigned_to != request.user:
        return render(request, 'tasks/error.html', {'msg': "Vous ne pouvez modifier que vos propres tâches !"})

    if request.method == "POST":
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES):
            if new_status == 'terminé' and task.status != 'terminé':
                task.completed_at = timezone.now()
            elif new_status != 'terminé':
                task.completed_at = None
            
            task.status = new_status
            task.save()

            if new_status == 'terminé':
                is_late = not task.is_completed_on_time()
                status_msg = "✅" if not is_late else "⚠️ (En retard)"
                late_suffix = " avec retard" if is_late else ""
                
                Notification.objects.update_or_create(
                    recipient=task.project.creator,
                    task=task,
                    defaults={
                        'message': f"{status_msg} {request.user.get_full_name() or request.user.username} a terminé la tâche « {task.title} »{late_suffix} dans le projet « {task.project.title} ».",
                        'is_read': False,
                        'created_at': timezone.now()
                    }
                )
            else:
                Notification.objects.filter(task=task, recipient=task.project.creator).delete()
        next_url = request.POST.get('next', '')
        return redirect(f'/dashboard/{next_url}')

    return redirect('dashboard')


@login_required
def mark_notifications_read(request):
    # ✅ CORRECTION : on marque comme lu via POST seulement
    if request.method == "POST":
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect('dashboard')


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if project.creator != request.user:
        return render(request, 'tasks/error.html', {'msg': "Seul le créateur peut modifier ce projet."})

    if request.method == "POST":
        project.title = request.POST.get('title')
        project.description = request.POST.get('description')
        project.save()
        return redirect('dashboard')

    return render(request, 'tasks/edit_project.html', {'project': project})


@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if task.project.creator != request.user:
        return render(request, 'tasks/error.html', {'msg': "Seul le créateur du projet peut modifier les tâches."})

    if request.method == "POST":
        assigned_id = request.POST.get('assigned_to')
        assigned_user = get_object_or_404(User, id=assigned_id)

        if request.user.role == 'Etudiant' and assigned_user.role == 'Professeur':
            return render(request, 'tasks/edit_task.html', {
                'task': task,
                'users': User.objects.all(),
                'error': "Un étudiant ne peut pas assigner un professeur !"
            })

        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.deadline = request.POST.get('deadline')
        task.assigned_to = assigned_user
        task.save()
        return redirect('dashboard')

    return render(request, 'tasks/edit_task.html', {'task': task, 'users': User.objects.all()})


@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if task.project.creator != request.user:
        return render(request, 'tasks/error.html', {'msg': "Seul le créateur du projet peut supprimer les tâches."})
    task.delete()
    return redirect('dashboard')