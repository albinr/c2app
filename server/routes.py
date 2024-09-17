from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Device, User

routes = Blueprint('routes', __name__)

@routes.route("/")
def main():
    return render_template("index.html")

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == "admin" and password == "admin":
            user = User(id=999, username="admin")
            login_user(user)
            flash('Login successful as admin!')
            return redirect(url_for('routes.devices'))

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!')
            return redirect(url_for('routes.devices'))
        else:
            flash('Invalid username or password')

    return render_template("login.html")

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('routes.login'))

@routes.route('/devices')
# @login_required
def devices():
    devices = Device.query.all()
    return render_template("devices.html", devices=devices)

@routes.route('/device/<int:id>/delete', methods=['POST'])
@login_required
def post_delete_device(id):
    device = Device.query.get_or_404(id)
    db.session.delete(device)
    db.session.commit()
    flash(f"Device {device.device_name} deleted successfully!")
    return redirect(url_for('routes.main'))

@routes.route('/device', methods=['POST'])
def api_add_device():
    try:
        data = request.json
        print(data)  # Print the received data for debugging

        # Add the new device to the database
        new_device = Device(device_name=data['device_name'], os_version=data['os_version'])
        db.session.add(new_device)
        db.session.commit()
        
        print(f"Device {new_device.device_name} added!")  # Debugging info
        return jsonify({"message": "Device added successfully!"}), 201
    except Exception as e:
        print(f"Error: {str(e)}")  # Log the error
        db.session.rollback()
        return jsonify({"error": "An error occurred."}), 400

@routes.route('/device/<int:id>', methods=['DELETE'])
def api_delete_device(id):
    device = Device.query.get_or_404(id)
    db.session.delete(device)
    db.session.commit()
    return jsonify({"message": f"Device {id} deleted successfully!"}), 200

@routes.route('/device/<int:id>', methods=['GET'])
def api_get_device(id):
    device = Device.query.get_or_404(id)
    return jsonify({
        'device_name': device.device_name,
        'os_version': device.os_version,
        'timestamp': device.timestamp
    }), 200

@routes.route('/device/<int:id>/heartbeat', methods=['POST'])
def api_device_heartbeat(id):
    device = Device.query.get_or_404(id)
    device.last_heartbeat = db.func.current_timestamp()
    db.session.commit()
    return jsonify({"message": f"Device {id}: Heartbeat received!"}), 200
