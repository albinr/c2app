from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(50))
    os_version = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Device {self.device_name}>"
