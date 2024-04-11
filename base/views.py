from django.shortcuts import render, redirect
from django.db.models import Q
from .models import Room, Topic, Message
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .forms import RoomForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm


def login_page(req):
    page = 'login'
    if req.user.is_authenticated:
        return redirect('home')
    if req.method == 'POST':
        username = req.POST.get('username')
        password = req.POST.get('password')
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(req, 'User Does Not Exist')
            redirect('login')
        user = authenticate(req, username=username, password=password)
        if user is not None:
            login(req, user)
            return redirect('home')
        else:
            messages.error(req, 'Username or password does not exist')

    context = {'page': page}
    return render(req, 'base/login_register.html', context)


def logout_page(req):
    logout(req)
    return redirect('home')


def register_page(req):
    form = UserCreationForm()
    if req.method == 'POST':
        form = UserCreationForm(req.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(req, user)
            return redirect('home')
        else:
            messages.error(req, 'Error occured in registration')
    context = {'form': form}
    return render(req, 'base/login_register.html', context)


def home(req):
    q = req.GET.get('q', '')
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q) | Q(host__username__icontains=q))
    comments = Message.objects.filter(
        Q(room__topic__name__icontains=q)).order_by('-created')

    topics = Topic.objects.all()
    context = {'rooms': rooms, 'topics': topics,
               'room_count': rooms.count(), 'comments': comments}
    return render(req, 'base/home.html', context)


def room(req, pk):
    room = Room.objects.get(id=pk)
    comments = room.message_set.all().order_by(
        '-created')  # add meta class to Message object
    participants = room.participants.all()
    if req.method == 'POST':
        message = Message.objects.create(
            user=req.user,
            room=room,
            body=req.POST.get('body')
        )
        room.participants.add(req.user)
        # it actually making get request to the /room/id to get all comments
        return redirect('room', pk=room.id)
    context = {'room': room, 'comments': comments,
               'participants': participants}
    return render(req, 'base/room.html', context)


def user_profile(req, pk):
    user = User.objects.get(id=pk)
    topics = Topic.objects.all()
    try:
        comments = Message.objects.filter(user=user)
    except:
        comments = []
    try:
        rooms = Room.objects.filter(host=user)
    except:
        rooms = []
    context = {'user': user, 'comments': comments,
               'rooms': rooms, 'topics': topics}
    return render(req, 'base/profile.html', context)


@login_required(login_url='login')
def create_room(req):
    form = RoomForm()
    topics = Topic.objects.all()
    if req.method == 'POST':
        topic, created = Topic.objects.get_or_create(
            name=req.POST.get('topic'))
        Room.objects.create(
            host=req.user,
            topic=topic,
            description=req.POST.get('description'),
            name=req.POST.get('name')
        )
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(req, 'base/room_form.html', context)


@login_required(login_url='login')
def update_room(req, pk):
    room = Room.objects.get(id=pk)
    topics = Topic.objects.all()
    if req.user != room.host:
        return HttpResponse("You are not allowed to update this room")
    if req.method == 'POST':
        topic, created = Topic.objects.get_or_create(
            name=req.POST.get('topic'))
        room.name = req.POST.get('name')
        room.description = req.POST.get('description')
        room.host = req.user
        room.topic = topic
        room.save()
        return redirect('home')
    context = {'form': RoomForm(instance=room), 'topics': topics}
    return render(req, 'base/room_form.html', context)


@login_required(login_url='login')
def delete_room(req, pk):
    room = Room.objects.get(id=pk)
    if req.user != room.host:
        return HttpResponse("You are not allowed to delete")
    if req.method == 'POST':
        room.delete()
        return redirect('home')
    context = {'obj': room}
    return render(req, 'base/delete.html', context)


@login_required(login_url='login')
def delete_comment(req, pk):
    comment = Message.objects.get(id=pk)
    if req.user != comment.user:
        return HttpResponse("You are not allowed to delete")
    if req.method == 'POST':
        comment.delete()
        return redirect('room', pk=comment.room.id)
    context = {'obj': comment}
    return render(req, 'base/delete.html', context)
