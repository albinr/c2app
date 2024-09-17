from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from models import db, Device


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devices.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route("/")
def main():
    devices = Device.query.all()
    return render_template("index.html", devices=devices)

@app.route('/device', methods=['POST'])
def add_device():
    data = request.json
    new_device = Device(device_name=data['device_name'], os_version=data['os_version'])
    db.session.add(new_device)
    db.session.commit()
    return jsonify({"message": "Device added successfully!"}), 201


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
