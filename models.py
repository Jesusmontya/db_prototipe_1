from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Paciente(db.Model):
    __tablename__ = 'pacientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    num_expediente = db.Column(db.String(50))
    edad = db.Column(db.Integer)
    sexo = db.Column(db.String(20))
    telefono = db.Column(db.String(20))
    motivo_consulta = db.Column(db.Text)
    diagnostico = db.Column(db.Text)
    estado = db.Column(db.String(50), default='Activo')
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ==========================================
    # NUEVOS CAMPOS CLÍNICOS (NOM-004-SSA3-2012)
    # ==========================================
    fecha_nacimiento = db.Column(db.Date)
    estado_civil = db.Column(db.String(50))
    ocupacion = db.Column(db.String(100))
    contacto_emergencia = db.Column(db.String(200))
    antecedentes_familiares = db.Column(db.Text)
    antecedentes_personales = db.Column(db.Text)
    plan_tratamiento = db.Column(db.Text)

    # Relaciones para que Flask traiga las citas y notas automáticamente
    citas = db.relationship('Cita', backref='paciente', lazy=True, cascade="all, delete-orphan")
    notas = db.relationship('NotaClinica', backref='paciente', lazy=True, cascade="all, delete-orphan")


class Cita(db.Model):
    __tablename__ = 'citas'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    modalidad = db.Column(db.String(50), default='presencial')
    estado = db.Column(db.String(50), default='Pendiente')


class NotaClinica(db.Model):
    __tablename__ = 'notas_clinicas'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    
    # --- NUEVO CAMPO PARA EL OBJETIVO DE LA SESIÓN ---
    objetivo_sesion = db.Column(db.Text) 
    
    fecha = db.Column(db.DateTime, default=datetime.utcnow)