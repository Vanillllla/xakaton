# xakaton

TG-bot

На данный момент поддерживаются только модели базового инстанса Yandex Cloud
> Перед началом работы
> Чтобы начать работать в Yandex Cloud:
> 
> Войдите в консоль управления. Если вы еще не зарегистрированы, перейдите в консоль управления и следуйте инструкциям.
> В сервисе Yandex Cloud Billing убедитесь, что у вас подключен платежный аккаунт, и он находится в статусе ACTIVE или TRIAL_ACTIVE. Если платежного аккаунта нет, создайте его.
> Если у вас еще нет каталога, создайте его.

Для запуска требуется добавить .env файл со следующим содержимым:
'''
BOT_TOKEN=<BOT_TOKEN>
DB_HOST=<IP>
DB_USER=<USERNAME>
DB_PASSWORD=<PASSWORD>
DB_NAME=<DB_NAME>
API_KEY=<YANDEX_CLOUD_API>
CLOUD_FOLDER=<FOLDER_WITH_SERVICE_ACCOUNT>

MODEL=<MODEL_NAME>
'''
