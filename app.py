import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from models import db, Paciente, Cita, NotaClinica

app = Flask(__name__)

# ==========================================
# CONFIGURACIÓN PARA RENDER Y SUPABASE (IPv4)
# ==========================================
app.secret_key = os.environ.get('SECRET_KEY', 'Pavel_Secret_Key_2026_Secure')

# IMPORTANTE: Hemos cambiado el host a 'aws-0-us-east-1.pooler.supabase.com' 
# y el puerto a '6543' para que Render (IPv4) pueda conectar sin errores.
# Reemplaza la configuración anterior por esta línea exacta:
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.mgqognqhtituwqerhumj:PavelKong31@aws-0-us-east-1.pooler.supabase.com:6543/postgres'

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', URL_POOLER_SUPABASE)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Esto crea las tablas en Supabase automáticamente si no existen
with app.app_context():
    db.create_all()

PASSWORD_MAESTRA = 'admin123'

# ==========================================
# PROTECCIÓN DE SESIÓN
# ==========================================
def login_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logeado' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# RUTAS DE LOGIN (INDEX.HTML)
# ==========================================
@app.route('/')
def inicio():
    if 'logeado' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logeado' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        entrada = request.form.get('password')
        if entrada == PASSWORD_MAESTRA:
            session['logeado'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Contraseña incorrecta. Intenta de nuevo.', 'error')
            return redirect(url_for('login'))
    
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('logeado', None)
    return redirect(url_for('login'))

# ==========================================
# RUTA DEL DASHBOARD
# ==========================================
@app.route('/dashboard')
@login_requerido
def dashboard():
    try:
        pacientes = Paciente.query.order_by(Paciente.id.desc()).all()
        hoy = datetime.now().strftime('%Y-%m-%d')
        citas_hoy = Cita.query.filter_by(fecha=hoy).order_by(Cita.hora.asc()).all()

        return render_template('dashboard.html', 
                               pacientes=pacientes, 
                               total_pacientes=len(pacientes),
                               citas_hoy=citas_hoy,
                               total_citas_hoy=len(citas_hoy))
    except Exception as e:
        return f"""
        <div style="font-family: sans-serif; padding: 40px; text-align: center;">
            <h1 style="color: #e74c3c;">Error de conexión a la Base de Datos</h1>
            <p>El sistema no pudo conectar con Supabase (IPv4 Pooler).</p>
            <p style="background: #f8f9fa; padding: 15px; border-radius: 8px; color: #333; display: inline-block; text-align: left;">
                <b>Detalle técnico:</b> {str(e)}
            </p>
            <br><br>
            <a href="/logout" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">Volver al Login</a>
        </div>
        """

# ==========================================
# RUTAS DE EXPEDIENTES Y API
# ==========================================
@app.route('/expediente/<int:id_paciente>')
@login_requerido
def ver_expediente(id_paciente):
    paciente = Paciente.query.get_or_404(id_paciente)
    return render_template('expediente.html', paciente=paciente)

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
    return redirect(url_for('ver_expediente', id_paciente=paciente_id))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
