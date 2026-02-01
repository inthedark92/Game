# middleware.py
from django.utils import timezone
from .models import PlayerProfile

class UpdateLastOnlineMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                # Получаем профиль и обновляем ресурсы до обработки запроса
                profile = PlayerProfile.objects.filter(user=request.user).first()
                if profile:
                    profile.update_resources()
                    # last_online обновится автоматически при save() благодаря auto_now=True
                    # Используем update_fields чтобы не перезаписать изменения из других запросов
                    profile.save(update_fields=['last_online', 'current_hp', 'current_mp'])
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in UpdateLastOnlineMiddleware: {str(e)}")
        
        response = self.get_response(request)
        return response