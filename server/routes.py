from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Device, User
from nominatim import get_location_from_coordinates

routes = Blueprint('routes', __name__)

@routes.route("/")
def main():
    return render_template("index.html")

@routes.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another one.')
            return redirect(url_for('routes.signup'))
        
        new_user = User(username=username)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('User created successfully! You can now log in.')
        return redirect(url_for('routes.login'))
    
    return render_template("signup.html")

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!')
            current_app.logger.info(f"User {user.username} logged in.")
            return redirect(url_for('routes.devices'))
        else:
            flash('Invalid username or password')
            current_app.logger.info(f"Failed logg in with {username}")

    return render_template("login.html")

@routes.route('/logout')
@login_required
def logout():
    current_app.logger.info(f"User {current_user.username} logged out.")
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('routes.login'))

@routes.route('/devices')
@login_required
def devices():
    devices = Device.query.all()
    return render_template("devices.html", devices=devices)

@routes.route('/devices/<int:id>')
@login_required
def single_device(id):
    device = Device.query.get_or_404(id)
    if device.geo_location:
        device.country, device.city = get_location_from_coordinates(device.geo_location)
    else:
        device.address = "Location not available"
    return render_template("single-device.html", device=device)

@routes.route('/device/<int:id>/delete', methods=['POST'])
@login_required
def post_delete_device(id):
    device = Device.query.get_or_404(id)
    db.session.delete(device)
    db.session.commit()
    current_app.logger.info(f"User {current_user.username} deleted device {device.device_name}.")
    flash(f"Device {device.device_name} deleted successfully!")
    return redirect(url_for('routes.devices'))

@routes.route('/logs')
@login_required
def view_logs():
    try:
        with open('logs/server.log', 'r') as log_file:
            logs = log_file.readlines()
        return render_template('logs.html', logs=logs)
    except Exception as e:
        flash(f"Could not open log file: {str(e)}", 'error')
        return redirect(url_for('routes.main'))


@routes.route('/device', methods=['POST'])
def api_add_device():
    try:
        data = request.json
        existing_device = Device.query.filter_by(hardware_id=data['hardware_id']).first()
        if existing_device:
            return jsonify({"error": "A device with this hardware ID already exists."}), 400

        new_device = Device(
            device_name=data['device_name'],
            os_version=data['os_version'],
            hardware_id=data['hardware_id'],
            geo_location=data.get('geo_location'),
            installed_apps=','.join(data.get('installed_apps', []))
        )
        current_app.logger.info(f"New device: {new_device.device_name} added to database.")
        db.session.add(new_device)
        db.session.commit()

        return jsonify({"message": "Device added successfully."}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 400


@routes.route('/device/<int:id>', methods=['DELETE'])
def api_delete_device(id):
    device = Device.query.get_or_404(id)
    db.session.delete(device)
    db.session.commit()
    current_app.logger.info(f"Device {device.device_name} deleted from database with api call.")
    return jsonify({"message": f"Device {id} deleted successfully!"}), 200

@routes.route('/device/<int:id>', methods=['GET'])
def api_get_device(id):
    device = Device.query.get_or_404(id)
    return jsonify({
        'device_name': device.device_name,
        'os_version': device.os_version,
        'timestamp': device.timestamp
    }), 200

@routes.route('/device/heartbeat', methods=['POST'])
def api_device_heartbeat():
    try:
        data = request.json
        hardware_id = data.get('hardware_id')

        if not hardware_id:
            return jsonify({"error": "Hardware ID is required"}), 400

        device = Device.query.filter_by(hardware_id=hardware_id).first()
        if not device:
            current_app.logger.info(f"Recived hearbeat from unknown device.")
            return jsonify({"error": "Device not found"}), 404

        device.last_heartbeat = db.func.current_timestamp()
        db.session.commit()
        current_app.logger.info(f"Recived hearbeat from {device.device_name}.")

        return jsonify({"message": f"Heartbeat for device {device.device_name} received!"}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@routes.route('/ping', methods=['GET'])
def ping():
    current_app.logger.info(f"Server was pinged.")
    return jsonify({"message": "Server is running"}), 200