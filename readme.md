# Python message app
This is a backend for a message app created using Python, Flask, SQLAlchemy and Marshmallow.

The application is a messaging app which works based on the assumption that users interacting with each other have existing profiles in the data base. When sending a message, this is done on behalf of a "signed in" user. 

## Setup
Clone directory.  
Install pipenv, and from inside of the working directorye run:    
$ pipenv install  
To install dependencies listed in Pipfile.  
Next, activate the Pipenv shell.  
$ pipenv shell

Create database.  
$ python3 
\>>> from app import db  
\>>> db.create_all()

Start server by running: 
$ pipenv run python app.py

## Create users
The database will initially be empty, start by populating it with some users by sending a POST request to the localhost:5000/user.
The endpoint takes a JSON-object containing "userName", "email", "phoneNumber". Username must contain at least one letter, and phonenumber can only contain numbers.

### Example request:
curl --header "Content-Type: application/json" --request POST --data "{\"userName\":\"{USERNAME}\",\"email\":\"{EMAIL}\", \"phoneNumber\": \"{PHONENUMBER}\"}" http://localhost:5000/user

## Send message
To send a message, send a POST request to http://localhost:5000/user/{id}/message, where id is the user id of the user sending the message. 
The endpoint accepts a JSON-object containing the properties "message", and "identifier". The message propertie is the actual message, and the identifier propertie is either the email, phonenumber or username of the receiver of the message. 

### Example request:
curl --header "Content-Type: application/json" --request POST --data "{\"message\":\"{MESSAGE}\",\"identifier\":\"{IDENTIFIER}\"}" http://localhost:5000/user/{id}/message

## Fetch message/messages
To retrieve messages for a specific user, send a GET request to http://localhost:5000/user/{id}/message?status={STATUS}&from={YYYY-MM-DD}+{hh:mm:ss}&to={YYYY-MM-DD}+{hh:mm:ss} 

The messages to be fetched is specified using a query string containing the arguments: status, from, to.
Status is set to "all" (fetch all messages), or "unread" (fetch only unread messages). When a message is fetched. The status is changed from unread to read. "from" and "to" define the time and date span from wich the messages should be fetched.

### Example request:
curl 'http://localhost:5000/user/{id}/message?status={STATUS}&from={YYYY-MM-DD}+{hh:mm:ss}&to={YYYY-MM-DD}+{hh:mm:ss}'

## Delete messages
To delet one or more messages, send a delete request to http://localhost:5000/user/{user_id}/message?id={id1}+{id2}+...+{idn}.
User_id defines which user is "signed in", and only messages received by this user can be deleted. The messages to be deleted is set in the query string using the argument "id", and one or more message id:s can be added here. 

### Example request:
curl -X "DELETE" 'http://localhost:5000/user/{user_id}/message?id=id={id1}+{id2}+{id3}'

## Other endpoints
http://localhost:5000/user [GET]
Get all users

http://localhost:5000/user/{id} [GET]
Get user by id

http://localhost:5000/user/{id} [DELETE]
Delete user by id
