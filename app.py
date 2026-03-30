import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from models import db, Paciente, Cita, NotaClinica

app = Flask(__name__)

# --- SEGURIDAD Y CONEXIÓN A SUPABASE ---
app.secret_key = 'Pavel_Secret_Key_2026_Secure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:PavelKong31@db.mgqognqhtituwqerhumj.supabase.co:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

PASSWORD_MAESTRA = 'admin123'

# ==========================================
# CANDADO DE SESIÓN
# ==========================================
def login_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logeado' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# RUTAS: LOGIN Y LOGOUT
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logeado' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        if request.form.get('password') == PASSWORD_MAESTRA:
            session['logeado'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Contraseña incorrecta', 'error')
            return redirect(url_for('login'))
    
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('logeado', None)
    return redirect(url_for('login'))

# ==========================================
# RUTA PRINCIPAL: EL SISTEMA
# ==========================================
@app.route('/')
@app.route('/dashboard')
@login_requerido
def dashboard():
    pacientes = Paciente.query.order_by(Paciente.id.desc()).all()
    hoy = datetime.now().strftime('%Y-%m-%d')
    citas_hoy = Cita.query.filter_by(fecha=hoy).order_by(Cita.hora.asc()).all()

    return render_template('dashboard.html', 
                           pacientes=pacientes, 
                           total_pacientes=len(pacientes),
                           citas_hoy=citas_hoy,
                           total_citas_hoy=len(citas_hoy))

# ==========================================
# RUTA: PESTAÑA INDIVIDUAL DEL EXPEDIENTE
# ==========================================
@app.route('/expediente/<int:id_paciente>')
@login_requerido
def ver_expediente(id_paciente):
    # Busca al paciente por ID; si no existe, lanza error 404
    paciente = Paciente.query.get_or_404(id_paciente)
    return render_template('expediente.html', paciente=paciente)

# ==========================================
# API: GUARDAR Y EDITAR DATOS EN SUPABASE
# ==========================================
@app.route('/api/pacientes', methods=['POST'])
@login_requerido
def guardar_paciente():
    try:
        nuevo = Paciente(
            nombre=request.form['nombre'],
            num_expediente=request.form.get('num_expediente'),
            edad=request.form.get('edad'),
            sexo=request.form.get('sexo'),
            telefono=request.form.get('telefono'),
            motivo_consulta=request.form.get('motivo'),
            diagnostico=request.form.get('diagnostico')
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Paciente registrado con éxito', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al guardar en base de datos', 'error')
        
    return redirect(url_for('dashboard'))

@app.route('/api/editar_paciente/<int:id_paciente>', methods=['POST'])
@login_requerido
def editar_paciente(id_paciente):
    paciente = Paciente.query.get_or_404(id_paciente)
    try:
        paciente.nombre = request.form['nombre']
        paciente.edad = request.form.get('edad')
        paciente.telefono = request.form.get('telefono')
        paciente.motivo_consulta = request.form.get('motivo')
        paciente.diagnostico = request.form.get('diagnostico')
        db.session.commit()
        flash('Expediente actualizado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar el expediente', 'error')
        
    # Regresa a la pestaña del expediente, no al dashboard
    return redirect(url_for('ver_expediente', id_paciente=id_paciente))

@app.route('/api/citas', methods=['POST'])
@login_requerido
def guardar_cita():
    try:
        nueva_cita = Cita(
            paciente_id=request.form['paciente_id'],
            fecha=request.form['fecha'],
            hora=request.form['hora'],
            modalidad=request.form.get('modalidad', 'presencial')
        )
        db.session.add(nueva_cita)
        db.session.commit()
        flash('Cita agendada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al agendar la cita', 'error')
        
    return redirect(url_for('dashboard'))

@app.route('/api/notas', methods=['POST'])
@login_requerido
def guardar_nota():
    paciente_id = request.form['paciente_id']
    try:
        nueva_nota = NotaClinica(
            paciente_id=paciente_id,
            contenido=request.form['contenido']
        )
        db.session.add(nueva_nota)
        db.session.commit()
        flash('Sesión registrada en el expediente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al guardar la nota', 'error')
        
    # Regresa a la pestaña del expediente
    return redirect(url_for('ver_expediente', id_paciente=paciente_id))

if __name__ == '__main__':
    app.run(debug=True, port=5000)