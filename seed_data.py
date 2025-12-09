"""
Script para poblar la base de datos con los datos del proyecto Gelatinas Ch'iki
Ejecutar: python seed_data.py
"""

import os
import sys
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Proyecto, Costo, Ingreso

def seed_database():
    """Popula la base de datos con los datos del proyecto Gelatinas Ch'iki"""
    
    with app.app_context():
        # Limpiar datos existentes
        print("🗑️  Limpiando datos existentes...")
        db.session.query(Ingreso).delete()
        db.session.query(Costo).delete()
        db.session.query(Proyecto).delete()
        db.session.commit()
        
        # 1. Crear Proyecto
        print("📝 Creando proyecto...")
        fecha_inicio = datetime.now()
        
        proyecto = Proyecto(
            nombre="Gelatinas Ch'iki",
            descripcion="Evaluación financiera en la venta de gelatina como práctica popular de subsistencia en niños de bajos recursos de El Alto, Bolivia",
            empresa="Gelatinas Ch'iki",
            producto="Gelatina de 150 ml en vaso con chispas de dulce y cucharilla",
            tasa_descuento=0.04,  # 4%
            tasa_impuestos=0.00,  # 0%
            periodos=5,
            inversion_inicial=52.00,
            unidades_produccion=30,
            precio_venta_unitario=1.50,
            estado="terminado",
            fecha_inicio=fecha_inicio
        )
        db.session.add(proyecto)
        db.session.flush()  # Para obtener el ID
        
        print(f"✅ Proyecto creado: ID {proyecto.id}")
        
        # 2. Agregar Ingresos
        print("\n💰 Agregando ingresos...")
        
        ingreso = Ingreso(
            proyecto_id=proyecto.id,
            concepto="Venta de gelatinas Ch'iki",
            descripcion="Venta directa de gelatinas de 150 ml en vaso, acompañadas de chispas de dulce y cucharilla",
            periodo_0=45.00,
            periodo_1=45.00,
            periodo_2=45.00,
            periodo_3=45.00,
            periodo_4=45.00,
            unidades_periodo_1=30,
            unidades_periodo_2=30,
            unidades_periodo_3=30,
            unidades_periodo_4=30
        )
        db.session.add(ingreso)
        db.session.flush()
        print(f"✅ Ingreso agregado: {ingreso.concepto}")
        
        # 3. Agregar Costos Variables
        print("\n🛒 Agregando costos variables...")
        
        costos_variables = [
            {
                "concepto": "Bolsa de Gelatina",
                "descripcion": "2 bolsas/día a 7.00 Bs/bolsa",
                "dias": [14.00, 14.00, 14.00, 14.00, 14.00]
            },
            {
                "concepto": "Vasos de plástico 150 ml",
                "descripcion": "30 unidades/día a 0.07 Bs/unidad",
                "dias": [2.10, 2.10, 2.90, 2.10, 2.10]
            },
            {
                "concepto": "Cucharillas",
                "descripcion": "30 unidades/día a 0.05 Bs/unidad",
                "dias": [1.50, 1.50, 1.50, 1.50, 1.50]
            },
            {
                "concepto": "Chispas de dulces",
                "descripcion": "0.25 lb/día a 12.00 Bs/libra",
                "dias": [3.00, 3.00, 3.00, 3.00, 3.00]
            },
            {
                "concepto": "Transporte",
                "descripcion": "2 viajes/día a 1.50 Bs/viaje",
                "dias": [3.00, 3.91, 2.91, 4.91, 5.91],
                "tipo": "variable"
            }
        ]
        
        for costo_data in costos_variables:
            costo = Costo(
                proyecto_id=proyecto.id,
                concepto=costo_data["concepto"],
                descripcion=costo_data["descripcion"],
                tipo="variable",
                periodo_0=costo_data["dias"][0],
                periodo_1=costo_data["dias"][1],
                periodo_2=costo_data["dias"][2],
                periodo_3=costo_data["dias"][3],
                periodo_4=costo_data["dias"][4]
            )
            db.session.add(costo)
            total = sum(costo_data["dias"])
            print(f"  ✅ {costo.concepto}: {costo_data['dias']} → Total: Bs {total:.2f}")
        
        # 4. Agregar Costos Fijos
        print("\n🏠 Agregando costos fijos...")
        
        costos_fijos = [
            {
                "concepto": "Alquiler Nevera",
                "descripcion": "Alquiler diario",
                "dias": [2.00, 2.00, 2.00, 2.00, 2.00]
            },
            {
                "concepto": "Alquiler Cocina",
                "descripcion": "Alquiler diario",
                "dias": [1.00, 1.00, 1.00, 1.00, 1.00]
            },
            {
                "concepto": "Agua",
                "descripcion": "6 litros/día a 0.01 Bs/litro",
                "dias": [0.04, 0.04, 0.04, 0.04, 0.04]
            },
            {
                "concepto": "Gas",
                "descripcion": "0.2 litros/día a 0.23 Bs/litro",
                "dias": [0.05, 0.05, 0.05, 0.05, 0.05]
            }
        ]
        
        for costo_data in costos_fijos:
            costo = Costo(
                proyecto_id=proyecto.id,
                concepto=costo_data["concepto"],
                descripcion=costo_data["descripcion"],
                tipo="fijo",
                periodo_0=costo_data["dias"][0],
                periodo_1=costo_data["dias"][1],
                periodo_2=costo_data["dias"][2],
                periodo_3=costo_data["dias"][3],
                periodo_4=costo_data["dias"][4]
            )
            db.session.add(costo)
            total = sum(costo_data["dias"])
            print(f"  ✅ {costo.concepto}: {costo_data['dias']} → Total: Bs {total:.2f}")
        
        # 5. Guardar todos los cambios
        print("\n💾 Guardando cambios en la base de datos...")
        db.session.commit()
        
        print("\n" + "="*60)
        print("✅ BASE DE DATOS POBLADA EXITOSAMENTE")
        print("="*60)
        print(f"\n📊 Proyecto: {proyecto.nombre}")
        print(f"   ID: {proyecto.id}")
        print(f"   Inversión: Bs {proyecto.inversion_inicial}")
        print(f"   TMAR: {proyecto.tasa_descuento*100:.2f}%")
        print(f"   Tasa Impuestos: {proyecto.tasa_impuestos*100:.2f}%")
        print(f"\n💰 Ingresos: 1 concepto")
        print(f"🛒 Costos Variables: 5 items")
        print(f"🏠 Costos Fijos: 4 items")
        print(f"\n🔗 Accede a: http://127.0.0.1:5000/proyectos/{proyecto.id}")
        print("="*60 + "\n")

if __name__ == '__main__':
    print("\n🚀 Iniciando población de base de datos...\n")
    seed_database()
    print("✨ ¡Listo! Ahora puedes acceder a la aplicación Flask.")
