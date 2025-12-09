from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Proyecto(db.Model):
    __tablename__ = 'proyectos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    empresa = db.Column(db.String(255), default="Gelatinas Ch'iki")
    producto = db.Column(db.String(255), default="Gelatinas Ch'iki - Dulce que alegra tu día")
    
    # Parámetros financieros
    tasa_descuento = db.Column(db.Float, nullable=False, default=0.12)  # i (12%)
    tasa_impuestos = db.Column(db.Float, default=0.13)  # t (13%)
    periodos = db.Column(db.Integer, default=5)  # n (siempre 5)
    inversion_inicial = db.Column(db.Float, default=0.0)  # I₀
    
    # Producción
    unidades_produccion = db.Column(db.Integer, default=0)  # Q
    precio_venta_unitario = db.Column(db.Float, default=0.0)  # P
    
    # Estado
    estado = db.Column(db.String(50), default='planificacion')
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    
    # Gantt y análisis
    gantt_data = db.Column(db.Text)  # JSON con actividades personalizadas del Gantt
    sensibilidad_data = db.Column(db.Text)  # JSON con resultados de sensibilidad
    logo = db.Column(db.String(500))  # Ruta del logo del proyecto
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    costos = db.relationship('Costo', backref='proyecto', cascade='all, delete-orphan', lazy=True)
    ingresos = db.relationship('Ingreso', backref='proyecto', cascade='all, delete-orphan', lazy=True)
    flujo_efectivo = db.relationship('FlujoEfectivo', backref='proyecto', uselist=False, cascade='all, delete-orphan')
    indicador = db.relationship('Indicador', backref='proyecto', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Proyecto {self.nombre}>'

class Costo(db.Model):
    __tablename__ = 'costos'
    
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=False)
    
    concepto = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # fijo, variable, inversion
    descripcion = db.Column(db.Text)
    
    # Montos por período (0-4 = 5 períodos)
    periodo_0 = db.Column(db.Float, default=0.0)
    periodo_1 = db.Column(db.Float, default=0.0)
    periodo_2 = db.Column(db.Float, default=0.0)
    periodo_3 = db.Column(db.Float, default=0.0)
    periodo_4 = db.Column(db.Float, default=0.0)
    
    costo_unitario = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def total(self):
        return self.periodo_0 + self.periodo_1 + self.periodo_2 + self.periodo_3 + self.periodo_4
    
    def get_periodo(self, k):
        """Obtiene el valor del período k (0-4)"""
        return getattr(self, f'periodo_{k}', 0.0) or 0.0
    
    def __repr__(self):
        return f'<Costo {self.concepto}>'

class Ingreso(db.Model):
    __tablename__ = 'ingresos'
    
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=False)
    
    concepto = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    
    # Ingresos por período
    periodo_0 = db.Column(db.Float, default=0.0)
    periodo_1 = db.Column(db.Float, default=0.0)
    periodo_2 = db.Column(db.Float, default=0.0)
    periodo_3 = db.Column(db.Float, default=0.0)
    periodo_4 = db.Column(db.Float, default=0.0)
    
    # Unidades vendidas
    unidades_periodo_1 = db.Column(db.Integer)
    unidades_periodo_2 = db.Column(db.Integer)
    unidades_periodo_3 = db.Column(db.Integer)
    unidades_periodo_4 = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def total(self):
        return self.periodo_0 + self.periodo_1 + self.periodo_2 + self.periodo_3 + self.periodo_4
    
    def get_periodo(self, k):
        """Obtiene el valor del período k (0-4)"""
        return getattr(self, f'periodo_{k}', 0.0) or 0.0
    
    def __repr__(self):
        return f'<Ingreso {self.concepto}>'

class FlujoEfectivo(db.Model):
    __tablename__ = 'flujo_efectivo'
    
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=False, unique=True)
    
    # Flujos netos
    periodo_0 = db.Column(db.Float, default=0.0)
    periodo_1 = db.Column(db.Float, default=0.0)
    periodo_2 = db.Column(db.Float, default=0.0)
    periodo_3 = db.Column(db.Float, default=0.0)
    periodo_4 = db.Column(db.Float, default=0.0)
    
    # Flujos descontados
    descontado_0 = db.Column(db.Float, default=0.0)
    descontado_1 = db.Column(db.Float, default=0.0)
    descontado_2 = db.Column(db.Float, default=0.0)
    descontado_3 = db.Column(db.Float, default=0.0)
    descontado_4 = db.Column(db.Float, default=0.0)
    
    # Flujos acumulados
    acumulado_0 = db.Column(db.Float, default=0.0)
    acumulado_1 = db.Column(db.Float, default=0.0)
    acumulado_2 = db.Column(db.Float, default=0.0)
    acumulado_3 = db.Column(db.Float, default=0.0)
    acumulado_4 = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FlujoEfectivo Proyecto {self.proyecto_id}>'

class Indicador(db.Model):
    __tablename__ = 'indicadores'
    
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=False, unique=True)
    
    # Indicadores financieros
    van = db.Column(db.Float)  # Valor Actual Neto
    tir = db.Column(db.Float)  # Tasa Interna de Retorno (%)
    ir = db.Column(db.Float)   # Índice de Rentabilidad
    relacion_bc = db.Column(db.Float)  # Beneficio/Costo
    payback = db.Column(db.Float)  # Período de recuperación
    roi = db.Column(db.Float)  # Return on Investment (%)
    
    # Totales
    total_ingresos = db.Column(db.Float, default=0.0)
    total_egresos = db.Column(db.Float, default=0.0)
    utilidad_bruta = db.Column(db.Float, default=0.0)
    utilidad_neta = db.Column(db.Float, default=0.0)
    
    # Interpretación
    decision = db.Column(db.String(50))
    observaciones = db.Column(db.Text)
    
    # Control
    calculado_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Indicador Proyecto {self.proyecto_id}>'