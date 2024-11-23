"""Routes for module protected endpoints"""
import firebase_admin.exceptions
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from helper.jwt_helper import get_roles
from helper.fcm_helper import send_fcm


firebase_messaging = Blueprint('firebase_messaging', __name__)


@firebase_messaging.route('/send', methods=['POST'])
@jwt_required()
def send():
    """
    Routes for demonstrate protected data endpoints, 
    need jwt to visit this endpoint
    """
    try:
        title = request.form['title']
        body = request.form['body']
        aux_data = request.form['aux_data']
        fcm_token = request.form['fcm_token']
        response_fcm = send_fcm(title=title, body=body, aux_data={
                                "payload": aux_data}, fcm_token=fcm_token)

        if response_fcm:
            return {'message': 'Notification sent successfully!'}

        current_user = get_jwt_identity()
        roles = get_roles()
        return jsonify({"message": "Notification sent successfully!",
                        "user_logged": current_user['username'],
                        "roles": roles}), 200
    except firebase_admin.exceptions.FirebaseError as e:
        print(e)
        return {'error': 'Failed to send notification'}, 500
