from db import get_user, save_user
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, emit
from flask_login import current_user, login_user, login_required, logout_user, LoginManager

app = Flask(__name__)
app.secret_key = "lucifer"
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# List to store rooms and a dictionary to track users in each room
rooms = []
room_users = {}

@socketio.on('connect')
def handle_connect():
    emit('room_list', rooms)

@socketio.on('create_room')
def handle_create_room_event(data):
    room_name = data['room_name']
    if room_name not in rooms:
        rooms.append(room_name)
        room_users[room_name] = []  
        emit('room_list', rooms, broadcast=True)

@socketio.on('join_room')
def handle_join_room_event(data):
    username = data['username']
    room = data['room']
    
    join_room(room)
    if(username not in room_users[room]):
        room_users[room].append(username)  
    app.logger.info("{} has joined the room {}".format(username, room))
    
    # Emit to the room about the new user
    socketio.emit('join_room_announcement', data, room=room)

@socketio.on('leave_room')
def handle_leave_room_event(data):
    username = data['username']
    room = data['room']

    if room in room_users and username in room_users[room]:
        room_users[room].remove(username)  # Remove user from the room's user list
        app.logger.info("{} has left the room {}".format(username, room))

        # Check if the room is empty
        if not room_users[room]:  # If no users left in the room
            rooms.remove(room)  # Remove the room from the list
            del room_users[room]  # Remove the room's user list
            emit('room_list', rooms, broadcast=True)  # Update all clients about room list

@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room {}: {}".format(data['username'],
                                                                    data['room'],
                                                                    data['message']))
    socketio.emit('receive_message', data, room=data['room'])

@login_manager.user_loader
def load_user(username):
    return get_user(username)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/chat')
@login_required
def chat():
    username = request.args.get('username')
    room = request.args.get('room')
    print('*'*100)
    print(username , room )
    if username and room:
        return render_template('chat.html', username=username, room=room)
    else:
        return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    msg = ""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user = get_user(username)
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("home"))
    else:
        msg = "Failed to login"
    return render_template('login.html', msg=msg)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    msg = ""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        save_user(username, email, password)
        return redirect(url_for('login'))
    return render_template('signup.html', msg=msg)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True) 