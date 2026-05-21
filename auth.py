import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']

def authenticate():
    creds = None
    
    # Проверка наличия сохраненного токена от предыдущих сессий
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # Если токена нет или он недействителен, инициируем процесс авторизации
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Чтение credentials.json
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # Запуск локального сервера. На Ubuntu это автоматически откроет браузер.
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
            
        # Сохранение полученного токена для будущих фоновых запусков
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    print("Авторизация успешна. Файл token.json готов к использованию.")

if __name__ == '__main__':
    authenticate()