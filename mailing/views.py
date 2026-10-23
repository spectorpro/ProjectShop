from .mixins import OwnerRequiredMixin
from .forms import MailingForm
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Recipient, Message, Mailing, EmailConfirmation, MailingAttempt
from .forms import RegisterForm
from .services import send_mailing, get_dashboard_stats, invalidate_dashboard_stats


def is_manager(user):
    return user.groups.filter(name='managers').exists()


# --- Регистрация и подтверждение ---
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            confirmation = EmailConfirmation.objects.create(user=user)
            confirm_url = f'http://127.0.0.1:8000/confirm/{confirmation.token}/'
            send_mail(
                subject='Подтверждение регистрации',
                message=f'Перейдите по ссылке: {confirm_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'mailing/register.html', {'form': form})


def confirm_email(request, token):
    confirmation = get_object_or_404(EmailConfirmation, token=token)
    if confirmation.is_confirmed:
        return render(request, 'mailing/confirm_done.html', {'message': 'Email уже подтверждён'})
    confirmation.is_confirmed = True
    confirmation.save()
    confirmation.user.is_active = True
    confirmation.user.save()
    return render(request, 'mailing/confirm_done.html', {'message': 'Email подтверждён! Войдите.'})


class CustomLoginView(LoginView):
    template_name = 'mailing/login.html'


class CustomLogoutView(LogoutView):
    next_page = '/'


@user_passes_test(is_manager, login_url='/login/')
def manager_dashboard(request):
    now = timezone.now()
    total_mailings = Mailing.objects.count()
    active_mailings = Mailing.objects.filter(
        start_time__lte=now,
        end_time__gte=now,
        status=Mailing.STATUS_RUNNING
    ).count()
    unique_recipients = Recipient.objects.count()
    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'unique_recipients': unique_recipients,
    }
    return render(request, 'mailing/manager_dashboard.html', context)


class ManagerMailingListView(UserPassesTestMixin, ListView):
    model = Mailing
    template_name = 'mailing/manager_list.html'
    context_object_name = 'mailings'
    paginate_by = 10

    def test_func(self):
        return is_manager(self.request.user)

    def get_queryset(self):
        return Mailing.objects.all()


# --- Дашборд пользователя (персональный) ---
def dashboard(request):
    now = timezone.now()
    total_mailings = Mailing.objects.filter(owner=request.user).count()
    active_mailings = Mailing.objects.filter(
        owner=request.user,
        start_time__lte=now,
        end_time__gte=now,
        status=Mailing.STATUS_RUNNING
    ).count()
    unique_recipients = Recipient.objects.count()  # если это общая статистика; если нужна по владельцу — фильтруй по owner

    stats = get_dashboard_stats(request.user)  # из сервиса с кэшем

    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'unique_recipients': unique_recipients,
        'stats': stats,
    }
    return render(request, 'mailing/dashboard.html', context)


# --- CRUD для Получателей (Recipient) ---
class RecipientListView(LoginRequiredMixin, ListView):
    model = Recipient
    template_name = 'mailing/recipient_list.html'
    context_object_name = 'recipients'
    paginate_by = 10


class RecipientCreateView(LoginRequiredMixin, CreateView):
    model = Recipient
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailing/recipient_form.html'
    success_url = reverse_lazy('recipient_list')


class RecipientUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipient
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailing/recipient_form.html'
    success_url = reverse_lazy('recipient_list')


class RecipientDeleteView(LoginRequiredMixin, DeleteView):
    model = Recipient
    template_name = 'mailing/recipient_confirm_delete.html'
    success_url = reverse_lazy('recipient_list')


# --- CRUD для Сообщений (Message) ---
class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'mailing/message_list.html'
    context_object_name = 'messages'
    paginate_by = 10


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    fields = ['subject', 'body']
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('message_list')


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    fields = ['subject', 'body']
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('message_list')


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('message_list')


# --- CRUD для Рассылок (Mailing) ---
class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = 'mailing/mailing_list.html'
    context_object_name = 'mailings'
    paginate_by = 10

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)


class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = 'mailing/mailing_detail.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('mailing_detail', kwargs={'pk': self.object.pk})


class MailingUpdateView(OwnerRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'

    def get_success_url(self):
        return reverse_lazy('mailing_detail', kwargs={'pk': self.object.pk})


class MailingDeleteView(OwnerRequiredMixin, DeleteView):
    model = Mailing
    template_name = 'mailing/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing_list')


# --- Действие: Запуск рассылки ---
def start_mailing(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    if not (mailing.owner == request.user or is_manager(request.user)):
        return render(request, 'mailing/mailing_detail.html', {
            'object': mailing,
            'error': 'Нет прав на запуск этой рассылки'
        })
    if request.method == 'POST':
        try:
            result = send_mailing(pk)
            # Если send_mailing создаёт MailingAttempt — тут нужно вызвать инвалидацию кэша
            invalidate_dashboard_stats(mailing.owner)
            return redirect('mailing_detail', pk=mailing.pk)
        except PermissionError as e:
            return render(request, 'mailing/mailing_detail.html', {
                'object': mailing,
                'error': str(e)
            })
        except Exception as e:
            return render(request, 'mailing/mailing_detail.html', {
                'object': mailing,
                'error': f"Произошла непредвиденная ошибка: {str(e)}"
            })
    return render(request, 'mailing/mailing_confirm_start.html', {'mailing': mailing})


# Отдельный эндпоинт статистики (если нужен отдельно)
def mailing_stats(request):
    stats = MailingAttempt.objects.filter(
        mailing__owner=request.user
    ).aggregate(
        success_count=Count('id', filter=Q(status='Успешно')),
        fail_count=Count('id', filter=Q(status='Не успешно'))
    )
    # Можно вернуть JSON или рендер — зависит от задачи
    return render(request, 'mailing/dashboard.html', {'stats': stats})
