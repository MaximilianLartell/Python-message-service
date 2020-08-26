from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import or_, func
from datetime import datetime
import re
import os

app=Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String, unique = False) 
    email = db.Column(db.String, unique = True) 
    phoneNumber = db.Column(db.String, unique=True)

    def __init__(self, userName, email, phoneNumber):
        self.userName = userName
        self.email = email
        self.phoneNumber = phoneNumber

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, unique=False)
    receiver_id = db.Column(db.Integer, unique=False)
    message = db.Column(db.String)
    status = db.Column(db.String)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'),
        nullable=False)
    created = db.Column(db.DateTime)

    def __init__(self, sender_id, receiver_id, message, status, conversation_id, created):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message = message
        self.status = status
        self.conversation_id = conversation_id
        self.created = created

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1 = db.Column(db.Integer)
    user2 = db.Column(db.Integer)
    # messages = db.relationship('Message', backref='chat')

    def __init__(self, user1, user2):
        self.user1 = user1
        self.user2 = user2

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'userName', 'email', 'phoneNumber')

class MessageSchema(ma.Schema):
    class Meta:
        fields = ('id', 'sender_id', 'receiver_id', 'message', 'status', 'conversation_id', 'created')

class ConversationSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user1', 'user2')

user_schema = UserSchema()
users_schema = UserSchema(many=True)
message_schema = MessageSchema()
messages_schema = MessageSchema(many=True)
conversation_schema = ConversationSchema()
conversations_schema = ConversationSchema(many=True)

def check_identifier_type(identifier):
    identifier_type = None
    is_phoneNumber = re.search(r"^[0-9]+$", identifier)
    is_email = re.search(r"@", identifier)
    if len(identifier) == 0:
        return None
    elif is_phoneNumber != None:
        return 'phoneNumber'
    elif is_email != None:
        return 'email'
    else: 
        return 'userName'

def get_user_id(identifier, identifier_type):
    if identifier_type == 'phoneNumber':
        user = User.query.filter_by(phoneNumber = identifier).first()
        if user == None:
            return None
        else: 
            return user.id 
    elif identifier_type == 'email':
        user = User.query.filter(func.lower(User.email) == func.lower(identifier)).first()
        if user == None:
            return None
        else: 
            return user.id 
    else:
        user = User.query.filter(func.lower(User.userName) == func.lower(identifier)).first()
        if user == None:
            return None
        else: 
            return user.id 

def check_conv(receiver_id, sender_id):
    conversation = Conversation.query.filter(or_(Conversation.user1 == sender_id, Conversation.user2 == sender_id)).filter(or_(Conversation.user1 == receiver_id, Conversation.user2 == receiver_id)).first()
    if conversation == None: 
        new_conversation = Conversation(sender_id, receiver_id)
        db.session.add(new_conversation)
        db.session.commit()
        return new_conversation
    else: 
        return conversation

def change_status(messages):
    for i in messages:
        if i.status == 'unread':
            i.status = 'read'
            db.session.commit()

def add_to_db(entry):
    db.session.add(entry)
    db.session.commit()

def check_get_query_string(args):
    regex = r"\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}"
    if args == None:
        return { 'error_message': 'No valid query string provided'}
    elif args.get('status') != 'all' and args.get('status') != 'unread':
        return { 'error_message': 'No valid status submitted in query string'}
    elif re.search(regex, args.get('from')) == None or re.search(regex, args.get('to')) == None:
        return { 'error_message': 'No valid date/time span submitted in query string'}
    else:
        return args

def check_delete_query_string(args):
    if args == None:
        return { 'error_message': 'No valid query string provided'}
    elif args.get('id') == None:
        return { 'error_message': 'No valid id submitted in query string'}
    else:
        return args

def check_new_user(username, email, phone_number):
    if re.search(r"[a-zA-Z]", username) == None or re.search(r"@", username) != None:
        return {'error_message': 'Username can not contain @ or only non letters'}
    elif re.search(r"(\w|\d|\W)[@]\w+[.]\w+", email) == None:
        return {'error_message': 'Invalid e-mail adress'}
    elif re.search(r"^[0-9]+$", phone_number) == None:
        return {'error_message': 'Invalid phone number'}
    else: 
        return None

def check_if_unique(username, email, phone_number):
    unique_username = User.query.filter(func.lower(User.userName) == func.lower(username)).first()
    unique_email = User.query.filter(func.lower(User.email) == func.lower(email)).first()
    unique_phone = User.query.filter(User.phoneNumber == phone_number).first()

    if unique_username != None: 
        return {'error_message': 'Username is already taken'}
    elif unique_email != None: 
        return {'error_message': 'Email is already taken'}
    elif unique_phone != None: 
        return {'error_message': 'Phone number is already taken'}
    else:
        return None

def user_is_receiver(id, message):
    if str(message.receiver_id) == id:
        return True
    else:
        return False

def user_exist(id):
    if User.query.get(id):
        return True
    else:
        return False

def message_exist(id):
    if Message.query.get(id):
        return True
    else:
        return False

def delete_error_checker(id, message_id, message):
    if user_exist(id) == False:
        return {'status_code': 404, 'error_message': f'User with id {id} does not exist'}
    elif message_exist(message_id) == False: 
        return {'status_code': 404, 'error_message': f'Message with id {message_id} does not exist'}
    elif user_is_receiver(id, message) == False:
        return {'status_code': 400, 'error_message': f'User with id {id} is not the receiver of message with id {message_id}'}
    else:
        return None

@app.route('/user/<id>/message', methods=['POST'])
def send_message(id):
    sender_id = id
    message = request.json['message']
    identifier = request.json['identifier']
    identifier_type = check_identifier_type(identifier)
    receiver_id = get_user_id(identifier, identifier_type)

    if receiver_id == None:
        return jsonify(error = f'No user with the {identifier_type} of {identifier}'), 404

    else: 
        conv_id = check_conv(receiver_id, sender_id).id
        new_message = Message(sender_id, receiver_id, message, 'unread', conv_id, datetime.today())
        add_to_db(new_message)
        return message_schema.jsonify(new_message), 201, {'Location': f'localhost:5000/user/{id}/message'}

@app.route('/user/<id>/message', methods=['GET'])
def get_message(id):
    args = check_get_query_string(request.args)
    if user_exist(id) == False:
        return {'Error': f'User with id {id} does not exist'}, 404

    elif args.get('error_message'): 
        return jsonify(error = f'{args.get("error_message")}'), 400

    else: 
        status = args.get('status')
        from_datetime = datetime.strptime(args.get('from'), '%Y-%m-%d %H:%M:%S')
        to_datetime = datetime.strptime(args.get('to'), '%Y-%m-%d %H:%M:%S')

        if status == 'all':
            fetched_messages = Message.query.filter(Message.receiver_id == id , Message.created >= from_datetime, Message.created <= to_datetime).all()
            result = messages_schema.dump(fetched_messages)
            change_status(fetched_messages)
            return jsonify(result)

        elif status == 'unread': 
            fetched_messages = Message.query.filter(Message.status == 'unread', Message.created >= from_datetime, Message.created <= to_datetime).all()
            result = messages_schema.dump(fetched_messages)
            change_status(fetched_messages)
            return jsonify(result)

@app.route('/user/<id>/message', methods=['DELETE'])
def delete_messages(id):
    args = check_delete_query_string(request.args)
    if args.get('error_message'):
        return jsonify(error = f'{args.get("error_message")}'), 400
    else:
        id_array = args.get('id').split(' ')
        valid_delete = ''
        for i in id_array:
            message = Message.query.get(i)
            check_response = delete_error_checker(id, i, message)
            if check_response != None:
                return jsonify({'Error': f'{check_response.get("error_message")}'}), f'{check_response.get("status_code")}'
            else:
                db.session.delete(message)
                db.session.commit()
                valid_delete += str(i) + ', '
        return jsonify({'Message': f'Messages with id: {valid_delete}deleted'}), 200

@app.route('/user', methods=['POST'])
def add_user():
    userName = request.json['userName']
    email = request.json['email']
    phoneNumber = request.json['phoneNumber']
    unique = check_if_unique(userName, email, phoneNumber)
    checked_input = check_new_user(userName, email, phoneNumber)
    if unique != None:
        return jsonify(error = f'{unique.get("error_message")}')
    elif checked_input != None:
        return jsonify(error = f'{checked_input.get("error_message")}')
    else:
        new_user = User(userName, email, phoneNumber)
        add_to_db(new_user)
        return user_schema.jsonify(new_user), 201, {'Location': f'localhost:5000/user/{new_user.id}'}

@app.route('/user', methods=['GET'])
def get_users():
    all_users = User.query.all()
    result = users_schema.dump(all_users)
    return jsonify(result)

@app.route('/user/<id>', methods=['GET'])
def get_user(id):
    user = User.query.get(id)
    return user_schema.jsonify(user)

@app.route('/user/<id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    return user_schema.jsonify(user)

if __name__ == "__main__":
    app.run(debug=True)
