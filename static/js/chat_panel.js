// Переменные для polling и управления историей чата
let lastMessageIds = {
    world: 0,
    location: 0,
    private: 0,
    trade: 0,
    groupchat: 0,
    group: 0,
    clan: 0,
    alliance: 0
};

let currentTab = 'world';
let pollingInterval = 3000;
let pollingActive = true;
let pollingTimer = null;
let autoScrollEnabled = true; // Флаг автоматической прокрутки
let chatInitialized = false; // Флаг инициализации чата

// Флаг для отслеживания ручной прокрутки
let isManualScrolling = false;
let manualScrollTimer = null;

// Функция для очистки локальной истории чата при входе
function clearLocalChatHistory() {
    if (!sessionStorage.getItem('chat_history_cleared')) {
        // Очищаем все контейнеры сообщений
        document.querySelectorAll('.chat-messages > div').forEach(container => {
            container.innerHTML = '';
        });
        
        // Сбрасываем lastMessageIds
        Object.keys(lastMessageIds).forEach(tab => {
            lastMessageIds[tab] = 0;
        });
        
        // Устанавливаем флаг, что история очищена
        sessionStorage.setItem('chat_history_cleared', 'true');
        console.log('Локальная история чата очищена');
    }
}

// Функция для получения новых сообщений
function fetchNewMessages() {
    if (!pollingActive) return;

    fetch(`/chat/get_messages/?tab=${currentTab}&last_id=${lastMessageIds[currentTab]}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'ok') {
                if (data.messages && data.messages.length > 0) {
                    lastMessageIds[currentTab] = data.last_id;
                    appendMessages(data.messages, currentTab);
                }
            } else {
                console.error('Ошибка сервера:', data.error);
            }
        })
        .catch(error => {
            console.error('Ошибка при получении сообщений:', error);
            setTimeout(fetchNewMessages, 10000);
        });
}

// Функция для добавления сообщений в чат с умной прокруткой
function appendMessages(messages, tab) {
    const messagesContainer = document.querySelector(`.chat-messages > div[data-tab="${tab}"]`);
    if (!messagesContainer) return;

    const wasAtBottom = isAtBottom(messagesContainer);
    
    messages.forEach(msg => {
        const messageElement = document.createElement('p');
        messageElement.innerHTML = `[${msg.time}] ${msg.sender}: ${msg.text}`;
        messagesContainer.appendChild(messageElement);
    });

    // Автоматическая прокрутка только если пользователь был внизу
    // или если включена автоскролл
    if (autoScrollEnabled && wasAtBottom) {
        scrollToBottom(messagesContainer);
    }
}

// Проверка, находится ли пользователь внизу контейнера
function isAtBottom(container) {
    const threshold = 50; // Пикселей от нижнего края
    return container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
}

// Прокрутка вниз
function scrollToBottom(container) {
    container.scrollTop = container.scrollHeight;
}

// Обработчик скролла для отслеживания ручной прокрутки
function setupScrollTracking() {
    document.querySelectorAll('.chat-messages > div').forEach(container => {
        container.addEventListener('scroll', function() {
            if (!isAtBottom(this)) {
                // Пользователь прокручивает вверх
                isManualScrolling = true;
                autoScrollEnabled = false;
                
                // Сбрасываем таймер
                if (manualScrollTimer) {
                    clearTimeout(manualScrollTimer);
                }
                
                // Через 2 секунды если пользователь прокрутит вниз, включаем автоскролл обратно
                manualScrollTimer = setTimeout(() => {
                    if (isAtBottom(this)) {
                        isManualScrolling = false;
                        autoScrollEnabled = true;
                    }
                }, 2000);
            } else {
                // Пользователь прокрутил вниз
                if (isManualScrolling) {
                    isManualScrolling = false;
                    autoScrollEnabled = true;
                }
            }
        });
    });
}

// Функция для отправки сообщения
function sendMessage() {
    const input = document.querySelector('.chat-input');
    const message = input.value.trim();
    if (!message) return;

    fetch('/chat/send_message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            tab: currentTab,
            text: message
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'ok') {
            input.value = '';
            // Обновляем сообщения сразу после отправки
            setTimeout(fetchNewMessages, 500);
        } else {
            alert('Ошибка при отправке сообщения: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Ошибка при отправке сообщения:', error);
        alert('Ошибка при отправке сообщения');
    });
}

// Функция для получения CSRF токена
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

// Запуск polling
function startPolling() {
    if (pollingTimer) clearInterval(pollingTimer);
    fetchNewMessages(); // Сразу делаем первый запрос
    pollingTimer = setInterval(fetchNewMessages, pollingInterval);
}

// Остановка polling
function stopPolling() {
    if (pollingTimer) clearInterval(pollingTimer);
    pollingActive = false;
}

// Функция переключения вкладок с сохранением состояния скролла
function setupTabSwitching() {
    document.querySelectorAll('.chat-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            // Убираем активный класс у всех вкладок
            document.querySelectorAll('.chat-tab').forEach(t => {
                t.classList.remove('active');
            });
            
            // Добавляем активный класс текущей вкладке
            this.classList.add('active');

            // Скрываем все контейнеры сообщений
            document.querySelectorAll('.chat-messages > div').forEach(msg => {
                msg.style.display = 'none';
            });

            // Показываем соответствующий контейнер сообщений
            const tabName = this.getAttribute('data-tab');
            const target = document.querySelector(`.chat-messages > div[data-tab="${tabName}"]`);
            if (target) {
                target.style.display = 'block';
                // После показа контейнера проверяем нужно ли скроллить вниз
                setTimeout(() => {
                    if (autoScrollEnabled) {
                        scrollToBottom(target);
                    }
                }, 100);
            }

            // Обновляем текущую вкладку и запрашиваем новые сообщения
            currentTab = tabName;
            fetchNewMessages();

            // Отображение панели группы только на вкладке "Подземный мир"
            document.getElementById('group-panel').style.display = (tabName === 'group') ? 'block' : 'none';
        });
    });
}

// Обновление часов с датой
function updateRealClock() {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    const day = now.getDate();
    const month = now.getMonth() + 1;
    const year = now.getFullYear();
    
    const timeStr = `${pad(hours)}:${pad(minutes)}`;
    const dateStr = `${pad(day)}.${pad(month)}.${year}`;
    const period = getRealTimePeriod(hours);

    const info = document.getElementById('real-time-info');
    if (info) {
        info.textContent = `${timeStr} ${period} | ${dateStr}`;
        info.style.color = period === '🌞 День' ? '#ffffff' : '#99ccff';
    }
}

function pad(n) {
    return n < 10 ? '0' + n : n;
}

function getRealTimePeriod(hour) {
    return hour % 2 === 0 ? '🌞 День' : '🌙 Ночь';
}

// Инициализация всего при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Очистка локальной истории при входе в игру
    clearLocalChatHistory();
    
    // Инициализация переключения вкладок
    setupTabSwitching();
    
    // Настройка отслеживания скролла
    setupScrollTracking();
    
    // Запуск polling
    startPolling();
    
    // Инициализация системной панели
    const systemToggle = document.getElementById('system-toggle');
    const systemPanel = document.getElementById('system-panel');
    if (systemToggle && systemPanel) {
        systemToggle.addEventListener('click', function () {
            const isVisible = systemPanel.style.display === 'block';
            systemPanel.style.display = isVisible ? 'none' : 'block';
            this.innerHTML = isVisible ? 'Системные ▼' : 'Системные ▲';
        });
    }

    // Логика монстров по сложности
    const monsterCount = document.getElementById('player-count');
    const difficultySelect = document.getElementById('group-difficulty');
    const difficultyOptions = {
        "1": [4, 6, 8],
        "2": [6, 8, 10],
        "3": [8, 10, 12]
    };

    function updateMonsterCounts() {
        const selected = difficultySelect.value;
        const options = difficultyOptions[selected] || [];
        monsterCount.innerHTML = '';
        options.forEach(val => {
            const opt = document.createElement('option');
            opt.value = val;
            opt.textContent = val;
            monsterCount.appendChild(opt);
        });
    }

    // Открыть окно создания группы
    document.getElementById('create-group-btn').addEventListener('click', function () {
        updateMonsterCounts();
        document.getElementById('group-password').value = '';
        document.getElementById('group-modal').style.display = 'block';
    });

    if (difficultySelect) {
        difficultySelect.addEventListener('change', updateMonsterCounts);
    }

    document.getElementById('cancel-create-group').addEventListener('click', function () {
        document.getElementById('group-modal').style.display = 'none';
    });

    document.getElementById('confirm-create-group').addEventListener('click', function () {
        const difficulty = difficultySelect.value;
        const strength = document.getElementById('monster-strength').value;
        const count = monsterCount.value;
        const password = document.getElementById('group-password').value.trim();

        if (!/^\d{4}$/.test(password)) {
            alert('Пароль должен состоять ровно из 4 цифр!');
            return;
        }

        alert(`Группа создана!
Сложность: ${difficulty}
Сила монстров: ${strength}%
Количество Игроков: ${count}
Пароль: ${password}`);

        document.getElementById('group-modal').style.display = 'none';
    });

    // Функционал нижней панели
    document.getElementById('clan-button').addEventListener('click', function(e) {
        e.preventDefault();
        if (window.parent && typeof window.parent.toggleClanPanel === 'function') {
            window.parent.toggleClanPanel();
        }
    });

    document.getElementById('send-button').addEventListener('click', sendMessage);

    document.getElementById('clear-button').addEventListener('click', function () {
        document.querySelector('.chat-input').value = '';
    });

    document.querySelector('.chat-input').addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    document.getElementById('admin-button').addEventListener('click', function() {
        document.getElementById('admin-login-modal').style.display = 'block';
    });

    document.getElementById('admin-login-cancel').addEventListener('click', function() {
        document.getElementById('admin-login-modal').style.display = 'none';
        document.getElementById('admin-login-error').style.display = 'none';
    });

    document.getElementById('admin-login-submit').addEventListener('click', function() {
        const login = document.getElementById('admin-login').value.trim();
        const password = document.getElementById('admin-password').value.trim();
        
        fetch('/game/admin/authenticate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                username: login,
                password: password
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('admin-login-modal').style.display = 'none';
                document.getElementById('admin-login-error').style.display = 'none';
                if (window.parent && typeof window.parent.toggleAdminPanel === 'function') {
                    window.parent.toggleAdminPanel();
                }
            } else {
                document.getElementById('admin-login-error').style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('admin-login-error').style.display = 'block';
        });
    });

    // Закрытие модальных окон при клике вне их области
    window.addEventListener('click', function(event) {
        if (event.target === document.getElementById('admin-login-modal')) {
            document.getElementById('admin-login-modal').style.display = 'none';
            document.getElementById('admin-login-error').style.display = 'none';
        }
        
        if (event.target === document.getElementById('group-modal')) {
            document.getElementById('group-modal').style.display = 'none';
        }
    });

    // Инициализация часов с датой
    updateRealClock();
    setInterval(updateRealClock, 60000);

    // Обработчик кнопки торговли
    document.getElementById('trade-button').addEventListener('click', function(e) {
        e.preventDefault();
        
        const modal = document.createElement('div');
        modal.innerHTML = `
            <div style="position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); 
                       background:#e9d6b5; padding:20px; border:2px solid #000; z-index:1000;
                       border-radius:10px; box-shadow:0 0 10px rgba(0,0,0,0.5); width:300px;">
                <h3 style="margin-top:0;text-align:center;">Выберите игрока для сделки</h3>
                <label style="display:block;margin-bottom:5px;">Ник игрока:</label>
                <input type="text" id="trade-player-input" style="width:100%;padding:5px;margin-bottom:15px;" placeholder="Введите ник">
                <div style="text-align:center;">
                    <button id="trade-confirm-btn" style="padding:5px 15px;margin-right:10px;">Подтвердить</button>
                    <button id="trade-cancel-btn" style="padding:5px 15px;">Отмена</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        document.getElementById('trade-confirm-btn').addEventListener('click', function() {
            const playerName = document.getElementById('trade-player-input').value.trim();
            if (playerName) {
                document.body.removeChild(modal);
                
                if (window.parent && typeof window.parent.toggleTradePanel === 'function') {
                    window.parent.toggleTradePanel();
                    window.parent.postMessage({
                        type: 'setPlayerName',
                        name: playerName
                    }, '*');
                }
            } else {
                alert('Пожалуйста, введите ник игрока');
            }
        });

        document.getElementById('trade-cancel-btn').addEventListener('click', function() {
            document.body.removeChild(modal);
        });
    });
    
    // Кнопка для принудительной прокрутки вниз (опционально)
    // Можно добавить кнопку в интерфейс для ручной прокрутки вниз
});

// Очистка сессии при выходе
window.addEventListener('beforeunload', function() {
    sessionStorage.removeItem('chat_history_cleared');
});