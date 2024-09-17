import traceback
import os
import re

from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from models import db, Device


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devices.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#Change location of key!!!!!
app.secret_key = re.sub(r"[^a-z\d]", "", os.path.realpath(__file__))
#Change location of key!!!!!
db.init_app(app)

@app.route("/")
def main():
    devices = Device.query.all()
    return render_template("index.html", devices=devices)

@app.route('/device', methods=['POST'])
def api_add_device():
    data = request.json
    new_device = Device(device_name=data['device_name'], os_version=data['os_version'])
    db.session.add(new_device)
    db.session.commit()
    return jsonify({"message": "Device added successfully!"}), 201

@app.route('/device/<int:id>', methods=['DELETE'])
def api_delete_device(id):
    device = Device.query.get_or_404(id)
    db.session.delete(device)
    db.session.commit()
    return jsonify({"message": f"Device {id} deleted successfully!"}), 200

@app.route('/device/<int:id>', methods=['GET'])
def get_device(id):
    device = Device.query.get_or_404(id)
    return jsonify({
        'device_name': device.device_name,
        'os_version': device.os_version,
        'timestamp': device.timestamp
    }), 200

@app.route('/device/<int:id>/heartbeat', methods=['POST'])
def api_device_heartbeat(id):
    device = Device.query.get_or_404(id)
    device.last_heartbeat = db.func.current_timestamp()
    db.session.commit()
    return jsonify({"message": f"Device {id}: Heartbeat received!"}), 200

@app.route('/device/<int:id>/delete', methods=['POST'])
def post_delete_device(id):
    device = Device.query.get_or_404(id)
    db.session.delete(device)
    db.session.commit()
    flash(f"Device {device.device_name} deleted successfully!")
    return redirect(url_for('main'))



with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
