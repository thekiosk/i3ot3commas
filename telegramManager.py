import telegram
import json
import requests

class telegramManager:
    def __init__(self):
        self.msgServices = {}

    def send_alert_message(self, msg):
        self.msgServices = json.loads(msg)
        if self.msgServices['type'] == 'group':
            self.send_group_alert_message()
        elif self.msgServices['type'] == 'individual':
            self.send_individual_alert_message()
                              
    def send_individual_alert_message(self):
        msgServices = self.msgServices
        tele_auth_token = msgServices['token']
        chat_id = msgServices['chat_id']
        message = msgServices['message']
        bot = telegram.Bot(token=tele_auth_token)    
        bot.send_message(text=message, chat_id=chat_id)    

    def send_group_alert_message(self):
        msgServices = self.msgServices
        tele_auth_token = msgServices['token']
        tel_group_id = msgServices['group_id']
        message = msgServices['message']
        telegram_api_url = f"https://api.telegram.org/bot{tele_auth_token}/sendMessage?chat_id=@{tel_group_id}&text={message}"
        tel_resp = requests.get(telegram_api_url)        
        if tel_resp.status_code == 200:
            print ("Notification has been sent on Telegram") 
        else:
            print ("Could not send Message")

