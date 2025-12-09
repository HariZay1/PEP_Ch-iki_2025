from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
from models import db, Proyecto, Costo, Ingreso, FlujoEfectivo, Indicador
from services.calculator_service import CalculatorService
from services.gantt_service import GanttService
from services.sensibilidad_service import SensibilidadService


migrate = Migrate()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pep_vrash_2025_secret_key')

database_url = os.environ.get("DATABASE_URL")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url + "?sslmode=require"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones con la app
db.init_app(app)
migrate.init_app(app, db)


# ============================================
# FILTROS DE JINJA2
# ============================================

def format_percent(value):
    """Convierte un valor decimal a porcentaje con 2 decimales"""
    if value is None:
        return "0.00%"
    return f"{value*100:.2f}%"

def formatCurrency(value):
    """Formatea un valor como moneda (Bs)"""
    if value is None:
        return "Bs 0.00"
    return f"Bs {value:,.2f}"

def formatNumber(value):
    """Formatea un número con separadores de miles"""
    if value is None:
        return "0"
    return f"{value:,.0f}"

def formatPercent(value):
    """Formatea un valor como porcentaje con 2 decimales (ya almacenado como decimal)"""
    if value is None:
        return "0.00%"
    return f"{value*100:.2f}%"

app.jinja_env.filters['format_percent'] = format_percent
app.jinja_env.filters['formatCurrency'] = formatCurrency
app.jinja_env.filters['formatNumber'] = formatNumber

# Registrar como funciones globales en Jinja2
app.jinja_env.globals['formatCurrency'] = formatCurrency
app.jinja_env.globals['formatNumber'] = formatNumber
app.jinja_env.globals['formatPercent'] = formatPercent
app.jinja_env.globals['datetime'] = datetime
# ============================================
# RUTAS PRINCIPALES
# ============================================

@app.route('/')
def index():
    proyectos = Proyecto.query.all()
    return render_template('proyectos/list.html', proyectos=proyectos)

# ============================================
# RUTAS DE PROYECTOS
# ============================================

@app.route('/proyectos')
def list_proyectos():
    proyectos = Proyecto.query.all()
    return render_template('proyectos/list.html', proyectos=proyectos)

@app.route('/proyectos/create', methods=['GET', 'POST'])
def create_proyecto():
    if request.method == 'POST':
        # Manejar la subida del logo
        logo_path = None
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename != '':
                # Validar tipo de archivo
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                filename = secure_filename(logo_file.filename)
                if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Crear directorio si no existe
                    upload_dir = os.path.join(basedir, 'static', 'uploads')
                    os.makedirs(upload_dir, exist_ok=True)
                    # Crear nombre único para el archivo
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    filename = timestamp + filename
                    filepath = os.path.join(upload_dir, filename)
                    logo_file.save(filepath)
                    logo_path = f'/static/uploads/{filename}'
        
        proyecto = Proyecto(
            nombre=request.form['nombre'],
            descripcion=request.form['descripcion'],
            empresa=request.form.get('empresa', 'Gelatinas Ch\'iki'),
            producto=request.form.get('producto', 'Gelatinas Ch\'iki - Dulce que alegra tu día'),
            tasa_descuento=float(request.form['tasa_descuento']) / 100,
            tasa_impuestos=float(request.form.get('tasa_impuestos', 13.0)) / 100,
            periodos=int(request.form.get('periodos', 5)),
            inversion_inicial=float(request.form.get('inversion_inicial', 0)),
            unidades_produccion=int(request.form.get('unidades_produccion', 0)),
            precio_venta_unitario=float(request.form.get('precio_venta_unitario', 0)),
            estado=request.form.get('estado', 'planificacion'),
            fecha_inicio=datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d') if request.form.get('fecha_inicio') else None,
            logo=logo_path
        )
        db.session.add(proyecto)
        db.session.commit()
        flash('Proyecto creado exitosamente', 'success')
        return redirect(url_for('show_proyecto', id=proyecto.id))
    
    return render_template('proyectos/create.html')

@app.route('/proyectos/<int:id>')
def show_proyecto(id):
    proyecto = Proyecto.query.get_or_404(id)
    calculator = CalculatorService(proyecto)
    flujo = proyecto.flujo_efectivo
    indicador = proyecto.indicador
    
    # Calcular utilidades si no existen
    if not indicador:
        indicador = calculator.calcular_indicadores()
    
    return render_template('proyectos/show.html', 
                         proyecto=proyecto, 
                         flujo=flujo, 
                         indicador=indicador)

@app.route('/proyectos/<int:id>/edit', methods=['GET', 'POST'])
def edit_proyecto(id):
    proyecto = Proyecto.query.get_or_404(id)
    
    if request.method == 'POST':
        proyecto.nombre = request.form['nombre']
        proyecto.descripcion = request.form['descripcion']
        proyecto.tasa_descuento = float(request.form['tasa_descuento']) / 100
        proyecto.tasa_impuestos = float(request.form['tasa_impuestos']) / 100
        proyecto.periodos = int(request.form['periodos'])
        proyecto.inversion_inicial = float(request.form['inversion_inicial'])
        proyecto.unidades_produccion = int(request.form['unidades_produccion'])
        proyecto.precio_venta_unitario = float(request.form['precio_venta_unitario'])
        proyecto.estado = request.form['estado']
        
        if request.form.get('fecha_inicio'):
            proyecto.fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d')
        
        db.session.commit()
        flash('Proyecto actualizado exitosamente', 'success')
        return redirect(url_for('show_proyecto', id=proyecto.id))
    
    return render_template('proyectos/edit.html', proyecto=proyecto)

@app.route('/proyectos/<int:id>/delete', methods=['POST'])
def delete_proyecto(id):
    proyecto = Proyecto.query.get_or_404(id)
    db.session.delete(proyecto)
    db.session.commit()
    flash('Proyecto eliminado exitosamente', 'success')
    return redirect(url_for('list_proyectos'))

@app.route('/proyectos/<int:id>/calcular', methods=['POST'])
def calcular_indicadores(id):
    proyecto = Proyecto.query.get_or_404(id)
    calculator = CalculatorService(proyecto)
    calculator.calcular_todo()
    flash('Indicadores calculados exitosamente', 'success')
    return redirect(url_for('show_proyecto', id=proyecto.id))

# ============================================
# RUTAS DE COSTOS
# ============================================

@app.route('/proyectos/<int:proyecto_id>/costos/create', methods=['GET', 'POST'])
def create_costo(proyecto_id):
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    
    if request.method == 'POST':
        costo = Costo(
            proyecto_id=proyecto_id,
            concepto=request.form['concepto'],
            tipo=request.form['tipo'],
            descripcion=request.form['descripcion'],
            periodo_0=float(request.form.get('periodo_0', 0)),
            periodo_1=float(request.form.get('periodo_1', 0)),
            periodo_2=float(request.form.get('periodo_2', 0)),
            periodo_3=float(request.form.get('periodo_3', 0)),
            periodo_4=float(request.form.get('periodo_4', 0)),
            costo_unitario=float(request.form.get('costo_unitario', 0)) if request.form.get('costo_unitario') else None
        )
        db.session.add(costo)
        db.session.commit()
        flash('Costo agregado exitosamente', 'success')
        return redirect(url_for('show_proyecto', id=proyecto_id))
    
    return render_template('costos/create.html', proyecto=proyecto)

@app.route('/costos/<int:id>/edit', methods=['GET', 'POST'])
def edit_costo(id):
    costo = Costo.query.get_or_404(id)
    
    if request.method == 'POST':
        costo.concepto = request.form['concepto']
        costo.tipo = request.form['tipo']
        costo.descripcion = request.form['descripcion']
        costo.periodo_0 = float(request.form.get('periodo_0', 0))
        costo.periodo_1 = float(request.form.get('periodo_1', 0))
        costo.periodo_2 = float(request.form.get('periodo_2', 0))
        costo.periodo_3 = float(request.form.get('periodo_3', 0))
        costo.periodo_4 = float(request.form.get('periodo_4', 0))
        costo.costo_unitario = float(request.form.get('costo_unitario', 0)) if request.form.get('costo_unitario') else None
        
        db.session.commit()
        flash('Costo actualizado exitosamente', 'success')
        return redirect(url_for('show_proyecto', id=costo.proyecto_id))
    
    return render_template('costos/edit.html', costo=costo)

@app.route('/costos/<int:id>/delete', methods=['POST'])
def delete_costo(id):
    costo = Costo.query.get_or_404(id)
    proyecto_id = costo.proyecto_id
    db.session.delete(costo)
    db.session.commit()
    flash('Costo eliminado exitosamente', 'success')
    return redirect(url_for('show_proyecto', id=proyecto_id))

# ============================================
# RUTAS DE INGRESOS
# ============================================

@app.route('/proyectos/<int:proyecto_id>/ingresos/create', methods=['GET', 'POST'])
def create_ingreso(proyecto_id):
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    
    if request.method == 'POST':
        ingreso = Ingreso(
            proyecto_id=proyecto_id,
            concepto=request.form['concepto'],
            descripcion=request.form['descripcion'],
            periodo_0=float(request.form.get('periodo_0', 0)),
            periodo_1=float(request.form.get('periodo_1', 0)),
            periodo_2=float(request.form.get('periodo_2', 0)),
            periodo_3=float(request.form.get('periodo_3', 0)),
            periodo_4=float(request.form.get('periodo_4', 0)),
            unidades_periodo_1=int(request.form.get('unidades_periodo_1', 0)),
            unidades_periodo_2=int(request.form.get('unidades_periodo_2', 0)),
            unidades_periodo_3=int(request.form.get('unidades_periodo_3', 0)),
            unidades_periodo_4=int(request.form.get('unidades_periodo_4', 0))
        )
        db.session.add(ingreso)
        db.session.commit()
        flash('Ingreso agregado exitosamente', 'success')
        return redirect(url_for('show_proyecto', id=proyecto_id))
    
    return render_template('ingresos/create.html', proyecto=proyecto)

@app.route('/ingresos/<int:id>/edit', methods=['GET', 'POST'])
def edit_ingreso(id):
    ingreso = Ingreso.query.get_or_404(id)
    
    if request.method == 'POST':
        ingreso.concepto = request.form['concepto']
        ingreso.descripcion = request.form['descripcion']
        ingreso.periodo_0 = float(request.form.get('periodo_0', 0))
        ingreso.periodo_1 = float(request.form.get('periodo_1', 0))
        ingreso.periodo_2 = float(request.form.get('periodo_2', 0))
        ingreso.periodo_3 = float(request.form.get('periodo_3', 0))
        ingreso.periodo_4 = float(request.form.get('periodo_4', 0))
        ingreso.unidades_periodo_1 = int(request.form.get('unidades_periodo_1', 0))
        ingreso.unidades_periodo_2 = int(request.form.get('unidades_periodo_2', 0))
        ingreso.unidades_periodo_3 = int(request.form.get('unidades_periodo_3', 0))
        ingreso.unidades_periodo_4 = int(request.form.get('unidades_periodo_4', 0))
        
        db.session.commit()
        flash('Ingreso actualizado exitosamente', 'success')
        return redirect(url_for('show_proyecto', id=ingreso.proyecto_id))
    
    return render_template('ingresos/edit.html', ingreso=ingreso)

@app.route('/ingresos/<int:id>/delete', methods=['POST'])
def delete_ingreso(id):
    ingreso = Ingreso.query.get_or_404(id)
    proyecto_id = ingreso.proyecto_id
    db.session.delete(ingreso)
    db.session.commit()
    flash('Ingreso eliminado exitosamente', 'success')
    return redirect(url_for('show_proyecto', id=proyecto_id))

# ============================================
# RUTAS DE ANÁLISIS
# ============================================

@app.route('/proyectos/<int:id>/dashboard')
def dashboard_proyecto(id):
    proyecto = Proyecto.query.get_or_404(id)
    calculator = CalculatorService(proyecto)
    
    # Calcular todo si no existe
    if not proyecto.indicador:
        calculator.calcular_todo()
        proyecto = Proyecto.query.get_or_404(id)  # Recargar
    
    indicador = proyecto.indicador
    flujo = proyecto.flujo_efectivo
    utilidades = calculator.calcular_utilidades()
    
    # Datos para gráficos
    flujos_data = [flujo.periodo_0, flujo.periodo_1, flujo.periodo_2, flujo.periodo_3, flujo.periodo_4] if flujo else []
    
    return render_template('analisis/dashboard.html', 
                         proyecto=proyecto, 
                         indicador=indicador,
                         flujos_data=flujos_data,
                         utilidades=utilidades)

@app.route('/proyectos/<int:id>/sensibilidad', methods=['GET', 'POST'])
def sensibilidad_proyecto(id):
    proyecto = Proyecto.query.get_or_404(id)
    sensibilidad_service = SensibilidadService(proyecto)
    resultados = None
    sensibilidad_guardada = None
    
    if request.method == 'POST':
        # Guardar escenarios personalizados
        escenarios = []
        for i in range(1, 4):  # 3 escenarios
            nombre = request.form.get(f'escenario_nombre_{i}')
            # Convertir porcentaje a decimal (4% -> 0.04)
            tasa_descuento = float(request.form.get(f'tasa_descuento_{i}', proyecto.tasa_descuento * 100)) / 100
            precio_venta = float(request.form.get(f'precio_venta_{i}', proyecto.precio_venta_unitario))
            costos = float(request.form.get(f'costos_{i}', 100))
            volumen = float(request.form.get(f'volumen_{i}', proyecto.unidades_produccion))
            
            if nombre:
                escenarios.append({
                    'nombre': nombre,
                    'tasa_descuento': tasa_descuento,
                    'precio_venta': precio_venta,
                    'costos': costos,
                    'volumen': volumen
                })
        
        # Calcular sensibilidad
        resultados = sensibilidad_service.calcular_sensibilidad_personalizada(escenarios)
        
        # Guardar en base de datos
        proyecto.sensibilidad_data = json.dumps({
            'fecha': datetime.now().isoformat(),
            'escenarios': escenarios,
            'resultados': {k: {'van': v['van'], 'tir': v['tir'], 'viabilidad': v['viabilidad']} 
                          for k, v in resultados.items()}
        })
        db.session.commit()
        flash('Análisis de sensibilidad guardado exitosamente', 'success')
    else:
        # GET: Cargar datos guardados si existen
        if proyecto.sensibilidad_data:
            try:
                sensibilidad_guardada = json.loads(proyecto.sensibilidad_data)
                # Mostrar resultados guardados
                resultados = sensibilidad_service.calcular_sensibilidad()
            except:
                pass
        
        # Si no hay datos guardados, calcular por defecto
        if not resultados:
            resultados = sensibilidad_service.calcular_sensibilidad()
    
    return render_template('analisis/sensibilidad.html', 
                         proyecto=proyecto,
                         resultados=resultados,
                         sensibilidad_guardada=sensibilidad_guardada)

@app.route('/proyectos/<int:id>/gantt', methods=['GET', 'POST'])
def gantt_proyecto(id):
    proyecto = Proyecto.query.get_or_404(id)
    gantt_service = GanttService(proyecto)
    
    if request.method == 'POST':
        # Actualizar actividades del Gantt
        actividades = []
        for i in range(1, 6):  # 5 actividades
            nombre = request.form.get(f'actividad_nombre_{i}')
            fecha_inicio = request.form.get(f'fecha_inicio_{i}')
            duracion = int(request.form.get(f'duracion_{i}', 1))
            progreso = int(request.form.get(f'progreso_{i}', 0))
            color = request.form.get(f'color_{i}', '#3498db')
            encargado = request.form.get(f'encargado_{i}', '')
            dependencias = request.form.get(f'dependencias_{i}', '')
            
            if nombre and fecha_inicio:
                actividades.append({
                    'id': i,
                    'nombre': nombre,
                    'fecha_inicio': fecha_inicio,
                    'duracion': duracion,
                    'progreso': progreso,
                    'color': color,
                    'encargado': encargado,
                    'dependencias': [int(x.strip()) for x in dependencias.split(',') if x.strip().isdigit()]
                })
        
        # Guardar actividades personalizadas
        gantt_service.guardar_actividades_personalizadas(actividades)
        flash('Diagrama Gantt actualizado', 'success')
        return redirect(url_for('gantt_proyecto', id=id))
    
    # Obtener actividades
    actividades = gantt_service.generar_actividades()
    estadisticas = gantt_service.obtener_estadisticas()
    
    return render_template('analisis/gantt.html', 
                         proyecto=proyecto,
                         actividades=actividades,
                         estadisticas=estadisticas)

# ============================================
# API PARA CÁLCULOS EN TIEMPO REAL
# ============================================

@app.route('/api/calcular_van', methods=['POST'])
def api_calcular_van():
    data = request.json
    proyecto_data = data.get('proyecto')
    costos_data = data.get('costos', [])
    ingresos_data = data.get('ingresos', [])
    
    # Simular cálculo
    calculator = CalculatorService(None)
    van = calculator.calcular_van_rapido(proyecto_data, costos_data, ingresos_data)
    
    return jsonify({'van': van})

@app.route('/api/calcular_tir', methods=['POST'])
def api_calcular_tir():
    data = request.json
    proyecto_data = data.get('proyecto')
    costos_data = data.get('costos', [])
    ingresos_data = data.get('ingresos', [])
    
    calculator = CalculatorService(None)
    tir = calculator.calcular_tir_rapido(proyecto_data, costos_data, ingresos_data)
    
    return jsonify({'tir': tir})

# ============================================
# INICIAR APLICACIÓN
# ============================================

if __name__ == '__main__':
    app.run(debug=True, port=5000)