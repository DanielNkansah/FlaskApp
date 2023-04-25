import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
import json
from flask import Flask, request, jsonify
from flask import escape
from flask_cors import CORS
import datetime
import os
import smtplib
from email.message import EmailMessage


cred = credentials.Certificate("privateKey.json")
firebase_admin.initialize_app(cred)
db = firestore.Client()
app = Flask(__name__)
CORS(app)
students_collection = db.collection('Students')
posts_collection = db.collection('Posts')


# 1: Allowing a student to Log in
@app.route('/login_student', methods=['POST'])
def login():
    record = json.loads(request.data)
    stud_id = record['student_id']
    password = record['password']

    student_ref = students_collection.document(stud_id)
    student_data = student_ref.get()

    if student_data.exists:
        if student_data.to_dict()['password'] == password:
            print("Logged In")
            return jsonify(
                {
                    'success': True,
                    'message': 'student with id ' + stud_id + ' has been logged in',
                    'student_name': student_data.to_dict()["student_name"],
                    'student_email': student_data.to_dict()["email"]
                }
            ), 200, {'Access-Control-Allow-Origin': '*'}
        else:
            return jsonify({'success': False, 'message': 'Wrong id or password'})
    else:
        return jsonify({'Success': False, 'message': 'Wrong id or password'}), 404


# TODO: fix create profile, let it check for existing profile
# 2: Create a profile
@app.route('/create_profile', methods=['POST'])
def create_profile():
    record = json.loads(request.data)
    check_profile = students_collection.document(record['student_id']).get()
    if check_profile.exists:
        return ("This profile already exists")
    else:
        students_collection.document(record['student_id']).set(record)
        response = jsonify(record)
        response.status_code = 201
        return response


# 3: Updating a student’s profile
@app.route('/update_profile', methods=['PATCH'])
def update_profile():
    student_id = request.args.get('student_id')
    profile_document = students_collection.document(student_id)
    if profile_document.get().exists:
        info = request.json
        profile_document.update(info)
        updated_profile = profile_document.get().to_dict()
        return jsonify(updated_profile), 200
    else:
        return jsonify({"Error": "Profile not found"}), 404


# 4: Retrieving a profile
@app.route('/retrieve_profile')
def retrieve_profile():
    student_id = request.args.get('student_id')
    stud = db.collection('Students')
    student = stud.document(student_id).get()
    if student.exists:
        return jsonify(student.to_dict()), 200
    else:
        return jsonify({"Error": "Student not found"}), 404


# 5: Creating a post
@app.route('/create_post', methods=['POST'])
def create_post():
    data = request.json

    if 'post' not in data:
        return jsonify({"Error": "post field is required"}), 400

    post_doc = posts_collection.document()
    post_doc.set({
        'student_name': data['student_name'],
        'post': data['post'],
        'createdat': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%s')
    })

    email_all_students(data['student_name'])

    return jsonify({
        'id': post_doc.id,
        'student_name': data['student_name'],
        'post': data['post']


    }), 201

# 6: Sending out an email


def send_email(receiver_email, receiver_name):

    sender_email_address = 'theo.darkomensah2002@gmail.com'
    password = 'wvjuietofgusmewf'

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email_address, password)

        subject = 'New Post'
        body = receiver_name + ' has made a new post'

        message = f'Subject: {subject}\n\n\n{body}'

        smtp.sendmail(sender_email_address, receiver_email, message)

 # 7: Retrieving a profile


def email_all_students(sender_name):
    stud = db.collection('Students')

    for doc in stud.get():
        email = doc.get('email')
        send_email(email, sender_name)


# if __name__ == '__main__':
#     app.run()
