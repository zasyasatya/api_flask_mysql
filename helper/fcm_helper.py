"""Helper to send data with firebase messaging"""
import firebase_admin
from firebase_admin import credentials, messaging
import firebase_admin.exceptions

cred = credentials.Certificate("credentials/service_account.json")
firebase_admin.initialize_app(cred)


def send_fcm(title, body, aux_data: None, fcm_token):
    """Helper to send message using Firebase Cloud Messaging"""
    try:
        print(aux_data)
        if not all([title, body]):
            return {'error': 'Missing required fields: title or message'}

        messaging_notification = messaging.Notification(title=title, body=body)
        message_payload = messaging.Message(
            notification=messaging_notification,
            data=aux_data,
            # Replace with your logic to retrieve device tokens
            token=fcm_token
        )
        response_fcm = messaging.send(message_payload)
        if response_fcm:
            return True
    except firebase_admin.exceptions.FirebaseError as e:
        return {'error': e}
