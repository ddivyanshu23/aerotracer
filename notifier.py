import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config


class Notifier:

    @staticmethod
    def send_email(subject, body_html):
        if not Config.SMTP_EMAIL or not Config.SMTP_PASSWORD:
            return False
            
        try:
            msg = MIMEMultipart()
            msg["From"] = Config.SMTP_EMAIL
            msg["To"] = Config.NOTIFICATION_EMAIL
            msg["Subject"] = subject
            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
                server.sendmail(Config.SMTP_EMAIL, Config.NOTIFICATION_EMAIL, msg.as_string())
            print("   📧 Email sent!")
            return True
        except Exception as e:
            print(f"   ⚠️ Email failed: {e}")
            return False

    @staticmethod
    def send_telegram(message):
        if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
            return False
            
        try:
            url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
            resp = requests.post(url, json={
                "chat_id": Config.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            })
            if resp.status_code == 200:
                print("   📱 Telegram sent!")
                return True
        except Exception as e:
            print(f"   ⚠️ Telegram failed: {e}")
        return False

    @staticmethod
    def notify_deal(origin, destination, price, departure, return_date, airline, target=None):
        currency = Config.CURRENCY
        symbol = "₹" if currency == "INR" else "$"
        savings = f" ({symbol}{target - price} below target!)" if target else ""

        subject = f"🚨 Flight Deal: {origin}→{destination} {symbol}{price}{savings}"

        html = f'''
        <h2>✈️ Flight Deal Found!</h2>
        <table>
            <tr><td><b>Route:</b></td><td>{origin} → {destination}</td></tr>
            <tr><td><b>Price:</b></td><td style="color:green;font-size:20px"><b>{currency} {price}</b></td></tr>
            <tr><td><b>Dates:</b></td><td>{departure} → {return_date}</td></tr>
            <tr><td><b>Airline:</b></td><td>{airline}</td></tr>
            {f'<tr><td><b>Savings:</b></td><td style="color:green">{symbol}{target-price} below target</td></tr>' if target else ''}
        </table>
        <p><b>⚡ Book NOW in incognito mode!</b></p>
        '''

        telegram = f'''
🚨 <b>FLIGHT DEAL!</b>
✈️ {origin} → {destination}
💰 <b>{currency} {price}</b>{savings}
📅 {departure} → {return_date}
🏢 {airline}
⚡ Book in incognito NOW!
        '''

        Notifier.send_email(subject, html)
        Notifier.send_telegram(telegram)
