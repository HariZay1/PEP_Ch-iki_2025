
from datetime import datetime
from models import FlujoEfectivo, Indicador, db


class CalculatorService:
    def __init__(self, proyecto):
        self.proyecto = proyecto
        self.periodos = 5  # Siempre 5 días
        self.flujo = None  # Cache for calculated flows
    
    # ============================================
    # 1. FÓRMULA VAN (CONVENCIÓN MEZA OROZCO 2013)
    # VAN = -I₀ + Σ[Fₖ/(1+i)^k]
    # ============================================
    # TODOS los flujos se descuentan (incluso el del día 1)
    # k=1 (día 1): F₁/(1+i)¹
    # k=2 (día 2): F₂/(1+i)²
    # k=5 (día 5): F₅/(1+i)⁵
    # ============================================
    def calcular_van(self):
        if self.flujo is None:
            self.calcular_flujos()
        
        flujo = self.flujo
        i = self.proyecto.tasa_descuento  # Tasa diaria decimal (0.04 = 4%)
        I0 = self.proyecto.inversion_inicial
        
        # VAN = -I₀ + Σ[Fₖ/(1+i)^k]
        sum_descontado = 0
        for k in range(1, self.periodos + 1):
            Fk = getattr(flujo, f'periodo_{k-1}')  # periodo_0 es día 1
            sum_descontado += Fk / ((1 + i) ** k)  # Todos descuentan con exponente k
        
        van = -I0 + sum_descontado
        return round(van, 2)
    
    
    # ============================================
    # 2. FÓRMULA TIR (CONVENCIÓN MEZA OROZCO 2013)
    # TIR: Resolver 0 = -I₀ + Σ[Fₖ/(1+r)^k]
    # ============================================
    # Usa bisección para encontrar tasa r
    # Convención: TODOS los flujos descuentan
    # ============================================
    def calcular_tir(self):
        if self.flujo is None:
            self.calcular_flujos()
        
        flujo = self.flujo
        I0 = self.proyecto.inversion_inicial
        
        # Función para calcular VAN dado una tasa de retorno
        def calcular_van_con_tasa(tasa):
            """
            VAN = -I₀ + Σ[Fₖ/(1+tasa)^k]
            Todos los flujos con exponente k
            """
            van = -I0
            for k in range(1, self.periodos + 1):
                Fk = getattr(flujo, f'periodo_{k-1}')
                van += Fk / ((1 + tasa) ** k)
            return van
        
        # Algoritmo de bisección
        tasa_min, tasa_max = -0.99, 10.0  # Rango: -99% a 1000%
        tolerancia = 0.0001
        intentos = 1000
        
        for iteracion in range(intentos):
            tasa_prueba = (tasa_min + tasa_max) / 2
            van = calcular_van_con_tasa(tasa_prueba)
            
            # Si encontramos la raíz
            if abs(van) < tolerancia:
                return round(tasa_prueba, 4)
            
            # Ajustar rango según signo de VAN
            if van > 0:
                tasa_min = tasa_prueba
            else:
                tasa_max = tasa_prueba
            
            # Si el rango se vuelve muy pequeño, hemos convergido
            if abs(tasa_max - tasa_min) < tolerancia / 100:
                return round(tasa_prueba, 4)
        
        # Si no convergió, retornar None
        return None
    
    # ============================================
    # 3. FÓRMULA: I_BC = Σ[Bₖ/(1+i)ᵏ] / Σ[Cₖ/(1+i)ᵏ]
    # ============================================
    # ============================================
    # 8. FÓRMULA B/C (RELACIÓN BENEFICIO-COSTO)
    # ============================================
    # B/C = Σ[Iₖ/(1+i)^k] / (Σ[Cₖ/(1+i)^k] + I₀)
    #
    # CONVENCIÓN MEZA: Todos los flujos con exponente k
    # ============================================
    def calcular_relacion_bc(self):
        i = self.proyecto.tasa_descuento  # Tasa diaria decimal
        beneficios_descontados = 0.0
        costos_descontados = 0.0
        
        # Iterar k=1 a n (convención Meza Orozco)
        for k in range(1, self.periodos + 1):
            # Obtener ingresos y costos (índice k-1 en arrays 0-based)
            Bk = sum(ingreso.get_periodo(k-1) for ingreso in self.proyecto.ingresos)
            Ck = sum(costo.get_periodo(k-1) for costo in self.proyecto.costos)
            
            # Descontar con exponente k (CONSISTENTE con VAN)
            beneficios_descontados += Bk / ((1 + i) ** k)
            costos_descontados += Ck / ((1 + i) ** k)
        
        # Agregar inversión inicial
        costos_descontados += self.proyecto.inversion_inicial
        
        if costos_descontados == 0:
            return None
        
        relacion_bc = beneficios_descontados / costos_descontados
        return round(relacion_bc, 4)
    
    # ============================================
    # 4. FÓRMULA: IR = VAN / I₀
    # ============================================
    def calcular_ir(self):
        van = self.calcular_van()
        I0 = self.proyecto.inversion_inicial
        
        if I0 == 0:
            return None
        
        # Fórmula correcta: IR = (VAN + I₀) / I₀
        ir = (van + I0) / I0
        return round(ir, 4)
    
    # ============================================
    # 5. FÓRMULA PAYBACK: Día donde acumulado >= I₀
    # Payback = A₀ + (I₀ - FA₀) / F_{A₀+1}
    # ============================================
    def calcular_payback(self):
        if self.flujo is None:
            self.calcular_flujos()
        
        flujo = self.flujo
        I0 = self.proyecto.inversion_inicial
        
        # Buscar el período donde se recupera la inversión
        acumulado = 0
        A0_index = None  # Índice del período anterior a recuperarse
        
        for k in range(self.periodos):
            Fk = getattr(flujo, f'periodo_{k}')
            acumulado += Fk
            
            if acumulado >= I0:
                A0_index = k - 1
                break
        
        # Si no se recupera en 5 períodos
        if A0_index is None or A0_index < 0:
            return None
        
        # Calcular acumulado hasta período A0_index
        FA0 = 0
        for k in range(A0_index + 1):
            Fk = getattr(flujo, f'periodo_{k}')
            FA0 += Fk
        
        # Flujo del período siguiente (A0_index + 1)
        FA0_mas1 = getattr(flujo, f'periodo_{A0_index + 1}')
        
        if FA0_mas1 == 0:
            return A0_index + 2  # Retornar en días (1-indexed), no en períodos (0-indexed)
        
        # Payback en términos de períodos dentro del período A0+1
        # Convertir a días: A0_index + 1 es el día donde se recupera
        payback_periodo = A0_index + ((I0 - FA0) / FA0_mas1)
        
        # Convertir de índice (0-4) a día (1-5)
        payback_dias = payback_periodo + 1
        
        return round(payback_dias, 2)
    
    # ============================================
    # 6. FÓRMULA ROI: (Utilidad) / I₀
    # ROI = (Flujo_Neto_Total - I₀) / I₀
    # Retorna como decimal para formatPercent
    # ============================================
    def calcular_roi(self):
        I0 = self.proyecto.inversion_inicial
        
        if I0 == 0:
            return None
        
        # Flujo neto total = ingresos totales - costos totales
        flujo_neto_total = 0
        for k in range(self.periodos):
            ingresos_k = sum(ingreso.get_periodo(k) for ingreso in self.proyecto.ingresos)
            costos_k = sum(costo.get_periodo(k) for costo in self.proyecto.costos)
            flujo_neto_total += (ingresos_k - costos_k)
        
        # ROI = (Flujo_Neto_Total - I₀) / I₀  (CORRECT FORMULA)
        utilidad = flujo_neto_total - I0
        roi = utilidad / I0
        return round(roi, 4)
    
    # ============================================
    # 7. FÓRMULAS DE UTILIDAD
    # UB = I - CV
    # UN = UB × (1 - t)
    # ============================================
    def calcular_utilidades(self):
        ingresos_totales = 0
        costos_variables_totales = 0
        costos_fijos_totales = 0
        
        for k in range(self.periodos):
            # Ingresos totales
            ingresos_totales += sum(ingreso.get_periodo(k) for ingreso in self.proyecto.ingresos)
            
            # Costos variables
            costos_variables = sum(
                costo.get_periodo(k) for costo in self.proyecto.costos 
                if costo.tipo == 'variable'
            )
            costos_variables_totales += costos_variables
            
            # Costos fijos
            costos_fijos = sum(
                costo.get_periodo(k) for costo in self.proyecto.costos 
                if costo.tipo == 'fijo'
            )
            costos_fijos_totales += costos_fijos
        
        t = self.proyecto.tasa_impuestos  # Ya es decimal (0.13 = 13%)
        
        utilidad_bruta = ingresos_totales - costos_variables_totales  # UB = I - CV
        utilidad_neta = utilidad_bruta * (1 - t)  # UN = UB × (1 - t)
        
        return {
            'ingresos_totales': round(ingresos_totales, 2),
            'costos_variables_totales': round(costos_variables_totales, 2),
            'costos_fijos_totales': round(costos_fijos_totales, 2),
            'utilidad_bruta': round(utilidad_bruta, 2),
            'utilidad_neta': round(utilidad_neta, 2)
        }
    
    # ============================================
    # 8. CALCULAR FLUJOS DE EFECTIVO: Fₖ = (Iₖ - Eₖ) × (1 - t)
    # Aplicar impuestos a cada flujo diario
    # ============================================
    def calcular_flujos(self):
        # Query the database directly to ensure we get the existing flujo if it exists
        flujo = FlujoEfectivo.query.filter_by(proyecto_id=self.proyecto.id).first()
        if not flujo:
            flujo = FlujoEfectivo(proyecto_id=self.proyecto.id)
            db.session.add(flujo)
            db.session.flush()  # Flush to get the ID assigned
        
        i = self.proyecto.tasa_descuento  # Tasa descuento (0.04 = 4% diario)
        t = self.proyecto.tasa_impuestos  # Tasa impuestos (0.04 = 4%)
        
        for k in range(self.periodos):
            # Ingresos del período k
            ingresos_k = sum(ingreso.get_periodo(k) for ingreso in self.proyecto.ingresos)
            
            # Egresos del período k
            egresos_k = sum(costo.get_periodo(k) for costo in self.proyecto.costos)
            
            # Utilidad operativa: Uₖ = Iₖ - Eₖ
            utilidad_k = ingresos_k - egresos_k
            
            # Flujo neto después de impuestos: Fₖ = Uₖ × (1 - t)
            flujo_neto = utilidad_k * (1 - t)
            setattr(flujo, f'periodo_{k}', flujo_neto)
            
            # Flujo descontado: Fₖ/(1+i)^(k+1)
            # Consistencia con VAN donde período_k se descuenta con exponente (k+1)
            flujo_descontado = flujo_neto / ((1 + i) ** (k + 1))
            setattr(flujo, f'descontado_{k}', flujo_descontado)
            
            # Flujo acumulado
            if k == 0:
                flujo_acumulado = flujo_neto
            else:
                flujo_acumulado_anterior = getattr(flujo, f'acumulado_{k-1}')
                flujo_acumulado = flujo_acumulado_anterior + flujo_neto
            
            setattr(flujo, f'acumulado_{k}', flujo_acumulado)
        
        # Use merge to handle both new and existing records
        flujo = db.session.merge(flujo)
        db.session.commit()
        self.flujo = flujo  # Store flujo in instance variable
        return flujo
    
    # ============================================
    # 9. CALCULAR TODOS LOS INDICADORES
    # ============================================
    def calcular_indicadores(self):
        # Calcular flujos primero
        self.calcular_flujos()
        
        # Calcular indicadores
        van = self.calcular_van()
        tir = self.calcular_tir()
        ir = self.calcular_ir()
        relacion_bc = self.calcular_relacion_bc()
        payback = self.calcular_payback()
        roi = self.calcular_roi()
        utilidades = self.calcular_utilidades()
        
        # Determinar decisión
        decision = self._determinar_decision(van, tir)
        observaciones = self._generar_observaciones(van, tir, ir, relacion_bc, payback)
        
        # Crear o actualizar indicador
        indicador = self.proyecto.indicador
        if not indicador:
            indicador = Indicador(proyecto_id=self.proyecto.id)
        
        indicador.van = van
        indicador.tir = tir
        indicador.ir = ir
        indicador.relacion_bc = relacion_bc
        indicador.payback = payback
        indicador.roi = roi
        indicador.total_ingresos = utilidades['ingresos_totales']
        indicador.total_egresos = utilidades['costos_variables_totales'] + utilidades['costos_fijos_totales']
        indicador.utilidad_bruta = utilidades['utilidad_bruta']
        indicador.utilidad_neta = utilidades['utilidad_neta']
        indicador.decision = decision
        indicador.observaciones = observaciones
        indicador.calculado_at = datetime.utcnow()
        
        db.session.add(indicador)
        db.session.commit()
        return indicador
    
    def _determinar_decision(self, van, tir):
        i = self.proyecto.tasa_descuento
        if van > 0 and tir > i:
            return 'ACEPTAR'
        elif van < 0 or tir < i:
            return 'RECHAZAR'
        return 'EVALUAR'
    
    def _generar_observaciones(self, van, tir, ir, relacion_bc, payback):
        observaciones = []
        
        # VAN
        if van > 0:
            observaciones.append(f"VAN positivo (${van:,.2f}): genera valor.")
        elif van < 0:
            observaciones.append(f"VAN negativo (${van:,.2f}): destruye valor.")
        else:
            observaciones.append("VAN = 0: punto de equilibrio.")
        
        # TIR con niveles - ¡¡ERROR AQUÍ!!
        # TIR viene como 0.1966 (19.66% en decimal) pero en el texto muestra 0.20%
        
        # CORREGIR: Convertir TIR a porcentaje para la comparación
        tir_porcentaje = tir * 100  # 0.1966 → 19.66
        
        if tir_porcentaje > 20:
            observaciones.append(f"TIR {tir_porcentaje:.2f}% > 20%: BASTANTE ATRACTIVO.")
        elif tir_porcentaje > 10:
            observaciones.append(f"TIR {tir_porcentaje:.2f}% entre 10-20%: Atractivo con consideraciones.")
        else:
            tir_porcentaje = tir * 100
            if tir_porcentaje > 20:
                observaciones.append(f"TIR {tir_porcentaje:.2f}% > 20%: BASTANTE ATRACTIVO.")
            elif tir_porcentaje > 10:
                observaciones.append(f"TIR {tir_porcentaje:.2f}% entre 10-20%: Atractivo con consideraciones.")
            else:
                observaciones.append(f"TIR {tir_porcentaje:.2f}% < 10%: POCO ATRACTIVO.")

        
        # Comparación TIR vs TMAR (ambas en decimal)
        if tir > self.proyecto.tasa_descuento:
            observaciones.append("TIR > TMAR: proyecto aceptable.")
        else:
            observaciones.append("TIR < TMAR: proyecto no aceptable.")
        
        # IR
        if ir and ir > 0:
            observaciones.append(f"IR {ir:.4f} > 0: rentable.")
        elif ir and ir < 0:
            observaciones.append(f"IR {ir:.4f} < 0: no rentable.")
        
        # B/C
        if relacion_bc and relacion_bc > 1:
            observaciones.append(f"B/C {relacion_bc:.4f} > 1: beneficios superan costos.")
        
        # Payback
        if payback:
            observaciones.append(f"Payback: {payback:.2f} períodos.")
        
        return " ".join(observaciones)

    def calcular_todo(self):
        """Calcular todo el proyecto"""
        self.calcular_flujos()
        return self.calcular_indicadores()