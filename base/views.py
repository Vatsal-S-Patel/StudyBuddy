from django.shortcuts import render, redirect
from django.db.models import Q
# from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
# from django.contrib.auth.forms import UserCreationForm

from .models import Message, Room, Topic, User
from .forms import RoomForm, UserForm, MyUserCreationForm


def login_user(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User Doesnot Exist!')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Wrong Credentials!')

    context = {'page': page}
    return render(request, 'base/signin_up.html', context)


def register_user(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurr ed during Registration!')
    
    context = {'form': form}
    return render(request, 'base/signin_up.html', context)


def logout_user(request):
    logout(request)
    return redirect('home')


@login_required(login_url='login') 
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, create = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')
    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def update_room(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse("You're not Allowed to Update Room")
    
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, create = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def delete_room(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse("You're not allowed to Delete Room")
    
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    context = {'obj' : room}
    return render(request, 'base/delete.html', context)


def home(request):
    q = request.GET.get('q') \
        if request.GET.get('q') != None \
        else ''

    rooms = Room.objects.filter( \
                Q(topic__name__icontains=q) | \
                Q(name__icontains=q) | \
                Q(description__icontains=q)
            )

    topics = Topic.objects.all()[:7]
    total_room = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q)) # type: ignore

    context = {'rooms': rooms, 'topics': topics, 'total_room': total_room, 'room_messages': room_messages}
    return render(request, 'base/home.html', context)


def room(request, pk):
    room = Room.objects.get(id=pk)
    # can take all message for particular room So, {from_which_base_model}.{model_name}_set.all() 
    room_messages = room.message_set.all()# type: ignore
    participants = room.participants.all()
    if request.method == 'POST':
        message = Message.objects.create( \
                      user=request.user, \
                      room=room, \
                      body=request.POST.get('body') \
                  )
        room.participants.add(request.user)
        return redirect('room', pk=room.id) # type: ignore
        
    context = {'room': room, 'room_messages': room_messages, 'participants': participants}
    return render(request, 'base/room.html', context)


@login_required(login_url='login')
def delete_message(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse("You're not allowed to Delete Message")
    
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    context = {'obj' : message}
    return render(request, 'base/delete.html', context)


def user_profile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all() # type: ignore
    room_messages = user.message_set.all() # type: ignore
    topics = Topic.objects.all() 
    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/user_profile_page.html', context)


@login_required(login_url='login') # type: ignore
def update_user_profile(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    context = {'form': form}
    return render(request, 'base/update_user_profile.html', context)


def topics_page(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {'topics': topics}
    return render(request, 'base/topics.html', context)


def activity_page(request):
    room_messages = Message.objects.all()
    context = {'room_messages': room_messages}
    return render(request, 'base/activity.html', context)