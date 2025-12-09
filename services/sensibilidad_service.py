from services.calculator_service import CalculatorService
import json

class SensibilidadService:
    def __init__(self, proyecto):
        self.proyecto = proyecto
        self.periodos = 5
    
    def calcular_sensibilidad(self):
        """
        Calcular sensibilidad con escenarios del informe
        
        Basados en análisis de precio y volumen (Informe, página 20):
        K = Flujo_Ventas_Normal / Flujo_Ventas_Afectado
        
        PESIMISTA: Precio Bs 2.00 (alto) → Volumen cae 26.83% → K = 0.7317
        NORMAL:    Precio Bs 1.50       → Volumen 100%        → K = 1.0000
        OPTIMISTA: Precio Bs 1.00 (bajo)→ Volumen sube 39.53% → K = 1.3953
        """
        escenarios = [
            {
                'nombre': 'PESIMISTA',
                'tasa_descuento': self.proyecto.tasa_descuento,
                'precio_venta': 2.00,  # Precio alto → demanda baja
                'costos': 100,         # Costos sin cambio
                'volumen': 73.17       # Reducción: 100 - 26.83 = 73.17
            },
            {
                'nombre': 'ESCENARIO BASE',
                'tasa_descuento': self.proyecto.tasa_descuento,
                'precio_venta': 1.50,  # Precio normal (actual)
                'costos': 100,         # Costos sin cambio
                'volumen': 100         # Volumen base
            },
            {
                'nombre': 'OPTIMISTA',
                'tasa_descuento': self.proyecto.tasa_descuento,
                'precio_venta': 1.00,  # Precio bajo → demanda alta
                'costos': 100,         # Costos sin cambio
                'volumen': 139.53      # Incremento: 100 + 39.53 = 139.53
            }
        ]
        
        return self._calcular_resultados_escenarios(escenarios)
    
    def calcular_sensibilidad_personalizada(self, escenarios):
        """Calcular sensibilidad con escenarios personalizados"""
        return self._calcular_resultados_escenarios(escenarios)
    
    def _calcular_resultados_escenarios(self, escenarios):
        """Calcular resultados para cada escenario"""
        resultados = {}
        
        for escenario in escenarios:
            # Simular proyecto con datos del escenario
            proyecto_simulado = self._crear_proyecto_simulado(escenario)
            calculator = CalculatorService(proyecto_simulado)
            
            # Calcular indicadores
            van = calculator.calcular_van()
            tir = calculator.calcular_tir()
            
            # Determinar viabilidad
            viabilidad = self._determinar_viabilidad(van, tir, escenario['tasa_descuento'])
            
            resultados[escenario['nombre']] = {
                'van': van,
                'tir': tir,
                'viabilidad': viabilidad,
                'datos': escenario
            }
        
        return resultados
    
    def _crear_proyecto_simulado(self, escenario):
        """Crear proyecto simulado para análisis"""
        class CostoSimulado:
            def __init__(self, costo_base, factor):
                self.tipo = costo_base.tipo
                self.costo_base = costo_base
                self.factor = factor
            
            def get_periodo(self, k):
                return self.costo_base.get_periodo(k) * self.factor
        
        class IngresoSimulado:
            def __init__(self, ingreso_base, factor_volumen, precio_venta, unidades_base):
                self.ingreso_base = ingreso_base
                self.factor_volumen = factor_volumen
                self.precio_venta = precio_venta
                self.unidades_base = unidades_base
            
            def get_periodo(self, k):
                # Ingresos = unidades ajustadas × precio ajustado
                unidades_ajustadas = self.unidades_base * self.factor_volumen
                ingreso = unidades_ajustadas * self.precio_venta
                return ingreso
        
        class ProyectoSimulado:
            def __init__(self, proyecto_base, escenario):
                self.id = proyecto_base.id
                self.nombre = proyecto_base.nombre
                self.tasa_descuento = escenario['tasa_descuento']
                self.tasa_impuestos = proyecto_base.tasa_impuestos
                self.periodos = proyecto_base.periodos
                self.inversion_inicial = proyecto_base.inversion_inicial
                self.unidades_produccion = proyecto_base.unidades_produccion * (escenario['volumen'] / 100.0)
                self.precio_venta_unitario = escenario['precio_venta']
                self.estado = proyecto_base.estado
                
                # Simular costos ajustados
                factor_costos = escenario['costos'] / 100.0
                self.costos = [
                    CostoSimulado(costo_base, factor_costos) 
                    for costo_base in proyecto_base.costos
                ]
                
                # Simular ingresos ajustados
                factor_volumen = escenario['volumen'] / 100.0
                precio_venta = escenario['precio_venta']
                
                self.ingresos = []
                for ingreso_base in proyecto_base.ingresos:
                    # Calcular unidades base: ingresos / precio original
                    if proyecto_base.precio_venta_unitario > 0:
                        unidades_base = ingreso_base.periodo_0 / proyecto_base.precio_venta_unitario
                    else:
                        unidades_base = ingreso_base.unidades_periodo_1 or 30
                    
                    ingreso_sim = IngresoSimulado(ingreso_base, factor_volumen, precio_venta, unidades_base)
                    self.ingresos.append(ingreso_sim)
                
                # Flujo de efectivo
                self.flujo_efectivo = None
        
        return ProyectoSimulado(self.proyecto, escenario)
    
    def _determinar_viabilidad(self, van, tir, tasa_descuento):
        if van > 0 and tir > tasa_descuento:
            return 'VIABLE'
        elif van < 0 or tir < tasa_descuento:
            return 'NO VIABLE'
        return 'INDIFERENTE'
    
    def guardar_analisis_sensibilidad(self, resultados):
        """Guardar análisis de sensibilidad en la base de datos"""
        # Implementar lógica de guardado
        self.proyecto.sensibilidad_data = json.dumps(resultados)
        return True