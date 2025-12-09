from datetime import datetime, timedelta
import json
from models import db

class GanttService:
    def __init__(self, proyecto):
        self.proyecto = proyecto
        self.dias_por_actividad = 1  # Configurable
    
    def generar_actividades(self, personalizadas=False):
        """Generar actividades del Gantt"""
        if personalizadas and hasattr(self.proyecto, 'gantt_data'):
            # Cargar actividades personalizadas desde BD
            return self._cargar_actividades_personalizadas()
        
        # Actividades por defecto (5 períodos = 5 días, 1 día cada uno)
        fecha_inicio = self.proyecto.fecha_inicio or datetime.now().date()
        # Convertir a datetime si es date para consistencia
        if isinstance(fecha_inicio, datetime):
            fecha_inicio = fecha_inicio.date()
        fecha_inicio = datetime.combine(fecha_inicio, datetime.min.time())
        
        actividades = [
            {
                'id': 1,
                'nombre': 'Período 1 - Análisis',
                'descripcion': 'Estudio de mercado y análisis técnico',
                'duracion': 1,
                'periodo': 0,
                'encargado': '',
                'dependencias': [],
                'color': '#3498db',
                'progreso': self._calcular_progreso(1)
            },
            {
                'id': 2,
                'nombre': 'Período 2 - Análisis',
                'descripcion': 'Análisis económico y financiero',
                'duracion': 1,
                'periodo': 1,
                'encargado': '',
                'dependencias': [1],
                'color': '#2ecc71',
                'progreso': self._calcular_progreso(2)
            },
            {
                'id': 3,
                'nombre': 'Período 3 - Análisis',
                'descripcion': 'Evaluación de indicadores',
                'duracion': 1,
                'periodo': 2,
                'encargado': '',
                'dependencias': [2],
                'color': '#f39c12',
                'progreso': self._calcular_progreso(3)
            },
            {
                'id': 4,
                'nombre': 'Período 4 - Análisis',
                'descripcion': 'Sensibilidad y escenarios',
                'duracion': 1,
                'periodo': 3,
                'encargado': '',
                'dependencias': [3],
                'color': '#9b59b6',
                'progreso': self._calcular_progreso(4)
            },
            {
                'id': 5,
                'nombre': 'Período 5 - Decisión',
                'descripcion': 'Conclusiones y decisión final',
                'duracion': 1,
                'periodo': 4,
                'encargado': '',
                'dependencias': [4],
                'color': '#e74c3c',
                'progreso': self._calcular_progreso(5)
            }
        ]
        
        # Calcular fechas
        return self._calcular_fechas_actividades(actividades, fecha_inicio)
    
    def _calcular_fechas_actividades(self, actividades, fecha_inicio):
        """Calcular fechas de inicio y fin para cada actividad (1 día por período)"""
        actividades_procesadas = []
        
        for actividad in actividades:
            # Cada actividad es un período: la fecha es fecha_inicio + número de período
            periodo = actividad.get('periodo', actividad['id'] - 1)
            inicio = fecha_inicio + timedelta(days=periodo)
            fin = inicio  # Mismo día (duración = 1 día)
            
            actividades_procesadas.append({
                **actividad,
                'fecha_inicio': inicio.strftime('%Y-%m-%d'),
                'fecha_fin': fin.strftime('%Y-%m-%d')
            })
        
        return actividades_procesadas
    
    def _calcular_progreso(self, actividad_id):
        """Calcular progreso según estado del proyecto"""
        estado = self.proyecto.estado
        
        progresos = {
            'planificacion': {1: 100, 2: 100, 3: 50, 4: 0, 5: 0},
            'en_ejecucion': {1: 100, 2: 100, 3: 100, 4: 100, 5: 50},
            'finalizado': {1: 100, 2: 100, 3: 100, 4: 100, 5: 100},
            'cancelado': {1: 100, 2: 100, 3: 100, 4: 0, 5: 0}
        }
        
        return progresos.get(estado, {}).get(actividad_id, 0)
    
    def guardar_actividades_personalizadas(self, actividades):
        """Guardar actividades personalizadas en la base de datos"""
        from models import db
        self.proyecto.gantt_data = json.dumps(actividades)
        db.session.commit()
        return True
    
    def _cargar_actividades_personalizadas(self):
        """Cargar actividades personalizadas desde BD"""
        if hasattr(self.proyecto, 'gantt_data') and self.proyecto.gantt_data:
            try:
                actividades_guardadas = json.loads(self.proyecto.gantt_data)
                # Calcular fechas para actividades guardadas
                fecha_inicio = self.proyecto.fecha_inicio or datetime.now().date()
                if isinstance(fecha_inicio, datetime):
                    fecha_inicio = fecha_inicio.date()
                fecha_inicio = datetime.combine(fecha_inicio, datetime.min.time())
                
                return self._calcular_fechas_actividades(actividades_guardadas, fecha_inicio)
            except:
                return []
        return []
    
    def obtener_estadisticas(self):
        """Obtener estadísticas del Gantt"""
        actividades = self.generar_actividades()
        
        duracion_total = sum(act['duracion'] for act in actividades)
        actividades_completadas = sum(1 for act in actividades if act['progreso'] >= 100)
        progreso_general = (actividades_completadas / len(actividades)) * 100 if actividades else 0
        
        return {
            'total_actividades': len(actividades),
            'duracion_total_dias': duracion_total,
            'actividades_completadas': actividades_completadas,
            'progreso_general': round(progreso_general, 1),
            'dias_por_actividad': self.dias_por_actividad,
            'fecha_inicio_proyecto': actividades[0]['fecha_inicio'] if actividades else None,
            'fecha_fin_proyecto': actividades[-1]['fecha_fin'] if actividades else None
        }