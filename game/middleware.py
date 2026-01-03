# middleware.py
from django.utils import timezone
from .models import PlayerProfile

class UpdateLastOnlineMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated:
            try:
                # Обновляем время последней активности
                PlayerProfile.objects.filter(user=request.user).update(
                    last_online=timezone.now()
                )
            except Exception as e:
                # Логируем ошибку, но не прерываем выполнение
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error updating last_online: {str(e)}")
        
        return response