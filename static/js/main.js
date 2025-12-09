// Funciones JavaScript para PEP Vrash 2025

// Inicializar tooltips de Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    // Tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Inicializar gráficos si existen
    initCharts();
    
    // Inicializar validación de formularios
    initFormValidation();
});

// Inicializar gráficos Chart.js
function initCharts() {
    // Gráfico de flujos
    const flujoCtx = document.getElementById('flujoChart');
    if (flujoCtx) {
        const flujoData = JSON.parse(flujoCtx.getAttribute('data-flujos') || '[]');
        new Chart(flujoCtx, {
            type: 'line',
            data: {
                labels: ['Día 1', 'Día 2', 'Día 3', 'Día 4', 'Día 5'],
                datasets: [{
                    label: 'Flujo de Efectivo',
                    data: flujoData,
                    borderColor: '#FF6B6B',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'Bs ' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Gráfico de sensibilidad
    const sensibilidadCtx = document.getElementById('sensibilidadChart');
    if (sensibilidadCtx) {
        const sensibilidadData = JSON.parse(sensibilidadCtx.getAttribute('data-sensibilidad') || '{}');
        
        new Chart(sensibilidadCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(sensibilidadData),
                datasets: [{
                    label: 'VAN (Bs)',
                    data: Object.values(sensibilidadData).map(d => d.van),
                    backgroundColor: '#4ECDC4',
                    borderColor: '#4ECDC4',
                    borderWidth: 1
                }, {
                    label: 'TIR (%)',
                    data: Object.values(sensibilidadData).map(d => d.tir),
                    backgroundColor: '#FFD166',
                    borderColor: '#FFD166',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'VAN (Bs)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'TIR (%)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }
}

// Validación de formularios
function initFormValidation() {
    // Validación de números positivos
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.min && parseFloat(this.value) < parseFloat(this.min)) {
                this.value = this.min;
            }
            if (this.max && parseFloat(this.value) > parseFloat(this.max)) {
                this.value = this.max;
            }
        });
    });
    
    // Validación de fechas
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            const today = new Date().toISOString().split('T')[0];
            input.value = today;
        }
    });
}

// Cálculos en tiempo real
function calcularVANRapido() {
    const inversion = parseFloat(document.getElementById('inversion_inicial').value) || 0;
    const tasa = parseFloat(document.getElementById('tasa_descuento').value) || 12;
    const flujos = [];
    
    // Obtener flujos estimados
    for (let i = 0; i < 5; i++) {
        const flujo = parseFloat(document.getElementById(`flujo_estimado_${i}`).value) || 0;
        flujos.push(flujo);
    }
    
    // Calcular VAN
    let van = -inversion;
    for (let k = 0; k < flujos.length; k++) {
        van += flujos[k] / Math.pow(1 + (tasa/100), k);
    }
    
    // Mostrar resultado
    const resultadoElement = document.getElementById('van_rapido_resultado');
    if (resultadoElement) {
        resultadoElement.textContent = 'Bs ' + van.toLocaleString('es-BO', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        
        resultadoElement.className = van >= 0 ? 'text-success fw-bold' : 'text-danger fw-bold';
    }
}

// Exportar datos
function exportarExcel() {
    alert('Función de exportación a Excel en desarrollo');
}

function exportarPDF() {
    alert('Función de exportación a PDF en desarrollo');
}

// Actualizar Gantt en tiempo real
function actualizarGantt() {
    const actividades = [];
    
    for (let i = 1; i <= 6; i++) {
        const nombre = document.getElementById(`actividad_nombre_${i}`).value;
        const fechaInicio = document.getElementById(`fecha_inicio_${i}`).value;
        const duracion = parseInt(document.getElementById(`duracion_${i}`).value) || 5;
        const progreso = parseInt(document.getElementById(`progreso_${i}`).value) || 0;
        
        if (nombre && fechaInicio) {
            actividades.push({
                nombre: nombre,
                fecha_inicio: fechaInicio,
                duracion: duracion,
                progreso: progreso
            });
        }
    }
    
    // Enviar al servidor
    fetch(window.location.href, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'actividades': JSON.stringify(actividades)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    });
}

// Cálculo automático de ingresos
function calcularIngresosAutomaticos() {
    const unidades = parseInt(document.getElementById('unidades_produccion').value) || 0;
    const precio = parseFloat(document.getElementById('precio_venta_unitario').value) || 0;
    
    if (unidades > 0 && precio > 0) {
        // Calcular ingresos por período (asumiendo crecimiento del 10% anual)
        for (let i = 1; i <= 4; i++) {
            const crecimiento = Math.pow(1.10, i); // 10% de crecimiento anual
            const ingresosPeriodo = unidades * precio * crecimiento;
            
            const inputIngreso = document.getElementById(`periodo_${i}`);
            if (inputIngreso && !inputIngreso.value) {
                inputIngreso.value = ingresosPeriodo.toFixed(2);
            }
            
            const inputUnidades = document.getElementById(`unidades_periodo_${i}`);
            if (inputUnidades && !inputUnidades.value) {
                inputUnidades.value = Math.round(unidades * crecimiento);
            }
        }
    }
}

// Formatear moneda en tiempo real
function formatCurrencyInput(input) {
    const value = parseFloat(input.value.replace(/[^0-9.-]+/g, ""));
    if (!isNaN(value)) {
        input.value = value.toLocaleString('es-BO', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
}

// Cargar datos de ejemplo
function cargarDatosEjemplo() {
    if (confirm('¿Cargar datos de ejemplo? Se sobrescribirán los datos actuales.')) {
        // Datos de ejemplo para Gelatinas con Chips
        document.getElementById('empresa').value = 'Vrash';
        document.getElementById('producto').value = 'Gelatinas con chips de colores en vaso';
        document.getElementById('tasa_descuento').value = '12.00';
        document.getElementById('tasa_impuestos').value = '13.00';
        document.getElementById('periodos').value = '5';
        document.getElementById('inversion_inicial').value = '50000';
        document.getElementById('unidades_produccion').value = '10000';
        document.getElementById('precio_venta_unitario').value = '6.50';
        
        alert('Datos de ejemplo cargados. Recuerda guardar el proyecto.');
    }
}