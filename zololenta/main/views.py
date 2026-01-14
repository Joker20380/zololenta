import csv
import logging
import os
import random
import uuid
from django.views.generic import ListView, CreateView, DetailView, TemplateView
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

from users.models import UserProfile

from django.utils import timezone
from django.contrib.auth.decorators import login_required

# Локальные импорты
from .models import *
from .utils import *
from .forms import *


class Index(DataMixin, ListView):
	queryset = News.objects.order_by('-time_update')
	model = News
	template_name = 'zololenta/index.html'
	context_object_name = 'news'
	paginate_by = 6
	
	@staticmethod
	def news_examples():
		news_examples = News.objects.filter(cat_id=2)
		return news_examples

	@staticmethod
	def news_colors():
		news_colors = News.objects.filter(cat_id=3)
		return news_colors
		
	@staticmethod
	def news_fonts():
		news_fonts = News.objects.filter(cat_id=4)
		return news_fonts


class ShowNews(DataMixin, DetailView):
    paginate_by = 1
    model = News
    template_name = 'zololenta/news-view.html'
    slug_url_kwarg = 'news_slug'
    context_object_name = 'news'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title=context['news'])
        return dict(list(context.items()) + list(c_def.items()))

    @staticmethod
    def post_last3():
        post_last3 = News.objects.reverse()[:3]
        return post_last3

    @staticmethod
    def post_last6():
        post_last6 = News.objects.reverse()[:6]
        return post_last6

		

class Confidential_information(DataMixin, ListView):
    model = Documents
    template_name = 'zololenta/confidential_information.html'
    context_object_name = 'news'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Политика конфиденциальности")
        return dict(list(context.items()) + list(c_def.items()))  
        
    @staticmethod
    def post_last3():
        post_last3 = News.objects.reverse()[:3]
        return post_last3
	
	    
    @staticmethod
    def news_all_conf():
        news_all_conf = News.objects.filter(title='Политика конфиденциальности')
        return news_all_conf
        
        
def Subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        if Subscriber.objects.filter(email__iexact=email).exists():
            messages.info(request, 'Этот e-mail уже подписан на рассылку.')
            return redirect('index')

        form = SubscriberForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Вы успешно подписались на рассылку!')
            return redirect('index')
        else:
            messages.error(request, 'Проверьте форму: есть ошибки.')
            return redirect('index')

    # GET-запрос — показать форму
    form = SubscriberForm()
    return render(request, 'zololenta/index.html', {'form': form})


def Unsubscribe(request):
    if request.method == 'POST':
        form = UnsubscriberForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                subscriber = Subscriber.objects.get(email=email, is_active=True)
                # Генерация уникального токена для отписки
                subscriber.unsubscribe_token = uuid.uuid4().hex
                subscriber.save()
                # Отправка письма с подтверждением
                unsubscribe_url = request.build_absolute_uri(
                    f"/unsubscribe/confirm/{subscriber.unsubscribe_token}/"
                )
                send_mail(
                    'Подтверждение отписки',
                    f'Для подтверждения отписки перейдите по ссылке: {unsubscribe_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'На ваш email отправлено письмо с подтверждением отписки.')
            except Subscriber.DoesNotExist:
                messages.error(request, 'Подписка с таким email не найдена.')
            return redirect('unsubscribe_request')
    else:
        form = UnsubscriberForm()
    return render(request, 'zololenta/unsubscribe_form.html', {'form': form})  
    

def Unsubscribe_confirm(request, token):
    subscriber = get_object_or_404(Subscriber, unsubscribe_token=token, is_active=True)
    subscriber.is_active = False
    subscriber.unsubscribe_token = None  # Очищаем токен
    subscriber.save()
    messages.success(request, 'Вы успешно отписались от рассылки.')
    return render(request, 'zololenta/unsubscribe_success.html')
    

class ContactsView(TemplateView):
    template_name = 'zololenta/contacts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        main_contact = Contact.objects.filter(is_main=True).select_related('location').first()
        context.update({
            'main_contact': main_contact,
            'contact_groups': ContactGroup.objects.prefetch_related('contacts').all(),
        })

        # Добавим координаты, если они есть
        if main_contact and main_contact.location:
            lat = main_contact.location.lat
            lon = main_contact.location.lon
            context['location_lat'] = f'{lat:.6f}'  # строка с точкой
            context['location_lon'] = f'{lon:.6f}'
            context['location_name'] = main_contact.name

        return context

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        contact_id = request.POST.get('contact')

        if not all([name, email, message]):
            messages.error(request, 'Пожалуйста, заполните все обязательные поля')
            return self.get(request, *args, **kwargs)

        try:
            contact = Contact.objects.get(id=contact_id) if contact_id else None
        except Contact.DoesNotExist:
            contact = None

        ContactRequest.objects.create(
            name=name,
            email=email,
            phone=phone,
            message=message,
            contact=contact
        )

        messages.success(request, 'Ваше сообщение успешно отправлено!')
        return redirect('contacts')