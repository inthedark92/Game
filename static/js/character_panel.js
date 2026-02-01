function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    const addStatButtons = document.querySelectorAll('.cp-add-stat-btn');

    addStatButtons.forEach(button => {
        button.addEventListener('click', function() {
            const statName = this.getAttribute('data-stat');

            fetch('/api/profile/distribute_stat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    stat_name: statName
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Перезагружаем панель персонажа для обновления всех статов
                    if (window.parent && typeof window.parent.toggleCharacterPanel === 'function') {
                        // Просто переоткрываем панель (или вызываем обновление если оно есть)
                        // В текущей реализации toggleCharacterPanel просто переключает видимость
                        // Нам нужно обновить содержимое.
                        location.reload();
                    } else {
                        location.reload();
                    }
                } else {
                    alert(data.message || 'Ошибка при распределении характеристик');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ошибка при выполнении запроса');
            });
        });
    });
});
