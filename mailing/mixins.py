from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin

class OwnerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        # Если владелец не совпадает и пользователь не staff — 404
        if obj.owner != request.user and not request.user.is_staff:
            raise Http404("Не найдено")
        return super().dispatch(request, *args, **kwargs)
