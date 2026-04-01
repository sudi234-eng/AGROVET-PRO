import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

class MpesaGateWay:
    def get_token(self):
        res = requests.get(
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            auth=HTTPBasicAuth(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET)
        )
        return res.json().get('access_token')

    def stk_push(self, phone, amount, order_id):
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        # Payload includes BusinessShortCode, Password, Timestamp, Amount, PhoneNumber, etc.
        # Reference Safaricom Daraja API docs for the full JSON structure