from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
import re
from projects.models import Project, Category, ProjectPicture, Tag
from django.http import HttpResponseNotFound
from django_countries import countries
from django.contrib import messages
import datetime
from datetime import timedelta
from django.conf import settings
import math


def is_valid_description(desc):
    return 20 <= len(desc) <= 200


def is_valid_title(title):
    return 5 <= len(title) <= 50 and re.search("^[a-zA-Z ]+$", title)


def is_valid_duration(duration):
    return re.search("^[0-9]+$", duration) and int(duration) <= 365


def is_valid_target(duration):
    return re.search("^[0-9]+$", duration)


def get_create_project_render_data():
    all_categories = Category.objects.all()
    all_tags = Tag.objects.all()
    render_data = {
        "categories": all_categories,
        "tags": all_tags,
        "countries": countries
    }
    return render_data


def handle_create_new_project_request(request):
    if settings.DEBUG:
        print(request)
        print(request.POST)
        print(request.FILES)

    if request.user.is_anonymous:
        return redirect('login')

    if request.method == "GET":
        return render(request, "projects/create_project.html", get_create_project_render_data())
    elif request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        country = request.POST.get("country")
        category = request.POST.get("category")
        duration = request.POST.get("duration")
        target = request.POST.get("target")

        error_detected = False
        if not is_valid_title(title):
            messages.error(request, 'Invalid Title [min_length: 5, max_length: 50, no digits]')
            error_detected = True

        if not is_valid_description(description):
            messages.error(request, 'Invalid Description [min_length: 20, max_length: 200]')
            error_detected = True

        if not is_valid_duration(duration):
            messages.error(request, 'Invalid Duration [No text, max_value: 365]')
            error_detected = True

        if not is_valid_target(target):
            messages.error(request, 'Invalid Target [No text]')
            error_detected = True

        if not request.FILES['ImageUpload']:
            messages.error(request, 'Need to select at least one project image')
            error_detected = True

        if error_detected:
            return render(request, "projects/create_project.html", get_create_project_render_data())
        else:
            new_project = Project()
            user = User.objects.get(id=request.user.id)
            new_project.owner = user
            new_project.title = title
            new_project.description = description
            new_project.category = Category.objects.get(id=int(category))
            new_project.country = country
            new_project.total_target = target
            new_project.start_date = datetime.date.today()
            new_project.end_date = datetime.date.today() + timedelta(days=int(duration))
            new_project.save()

            print(new_project)

            tags_ids = request.POST.getlist('tags')
            for tag_id in tags_ids:
                obj = Tag.objects.get(id=tag_id)
                new_project.tags.add(obj)

            images = request.FILES.getlist('ImageUpload')
            fs = FileSystemStorage()
            for file in images:
                filename = fs.save(file.name, file)
                uploaded_file_url = fs.url(filename)
                project_pic = ProjectPicture()
                project_pic.project = new_project
                project_pic.pic_path = uploaded_file_url
                project_pic.save()

            return redirect('list_projects')
    else:
        return HttpResponseNotFound("404")


def get_update_project_render_data(project: Project):
    all_categories = Category.objects.all()
    render_data = {
        "categories": all_categories,
        "countries": countries,
        "project_title": project.title,
        "project_description": project.description,
        "project_country": project.country,
        "project_category": project.category,
        "project_duration": (project.end_date - project.start_date).days,
        "project_target": math.ceil(project.total_target),
        "project_images": project.pictures.all(),
    }
    return render_data


def handle_update_project_request(request, project_id):
    if settings.DEBUG:
        print(request)
        print(request.POST)
        print(request.FILES)

    if request.user.is_anonymous:
        return redirect('login')

    project = Project.objects.get(id=project_id)
    if request.method == "GET":
        return render(request, "projects/update_project.html", get_update_project_render_data(project))
    elif request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        country = request.POST.get("country")
        category = request.POST.get("category")
        duration = request.POST.get("duration")
        target = request.POST.get("target")

        error_detected = False
        if not is_valid_title(title):
            messages.error(request, 'Invalid Title [min_length: 5, max_length: 50, no digits]')
            error_detected = True

        if not is_valid_description(description):
            messages.error(request, 'Invalid Description [min_length: 20, max_length: 200]')
            error_detected = True

        if not is_valid_duration(duration):
            messages.error(request, 'Invalid Duration [No text, max_value: 365]')
            error_detected = True

        if not is_valid_target(target):
            messages.error(request, 'Invalid Target [No text]')
            error_detected = True

        if not request.FILES['ImageUpload']:
            messages.error(request, 'Need to select at least one project image')
            error_detected = True

        if error_detected:
            return render(request, "projects/create_project.html", get_create_project_render_data())
        else:
            new_project = Project()
            user = User.objects.get(id=request.user.id)
            new_project.owner = user
            new_project.title = title
            new_project.description = description
            new_project.category = Category.objects.get(id=int(category))
            new_project.country = country
            new_project.total_target = target
            new_project.start_date = datetime.date.today()
            new_project.end_date = datetime.date.today() + timedelta(days=int(duration))
            new_project.save()

            print(new_project)

            images = request.FILES.getlist('ImageUpload')
            fs = FileSystemStorage()
            for file in images:
                filename = fs.save(file.name, file)
                uploaded_file_url = fs.url(filename)
                project_pic = ProjectPicture()
                project_pic.project = new_project
                project_pic.pic_path = uploaded_file_url
                project_pic.save()

            return redirect('list_projects')
    else:
        return HttpResponseNotFound("404")
