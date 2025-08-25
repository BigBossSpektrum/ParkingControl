from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
import json
import logging
import subprocess
import re

from .models import PrinterConfiguration, PrintJob
from .printer_service import printer_service
from app_page.models import Cliente

logger = logging.getLogger(__name__)

@login_required
def printer_dashboard(request):
    """Dashboard principal para gestión de impresoras"""
    printers = PrinterConfiguration.objects.all()
    recent_jobs = PrintJob.objects.select_related('printer').order_by('-created_at')[:10]
    printer_status = printer_service.get_printer_status()
    simulation_mode = cache.get('printer_simulation_mode', True)
    
    context = {
        'printers': printers,
        'recent_jobs': recent_jobs,
        'printer_status': printer_status,
        'simulation_mode': simulation_mode,
    }
    
    return render(request, 'app_impresora/dashboard.html', context)

@login_required
def add_printer(request):
    """Vista para agregar nueva impresora"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            printer_type = request.POST.get('printer_type')
            connection_string = request.POST.get('connection_string')
            set_active = request.POST.get('set_active') == 'on'
            
            if not all([name, printer_type, connection_string]):
                return JsonResponse({
                    'success': False,
                    'message': 'Todos los campos son requeridos'
                })
            
            # Si se marca como activa, desactivar otras
            if set_active:
                PrinterConfiguration.objects.update(is_active=False)
            
            # Crear nueva impresora
            printer = PrinterConfiguration.objects.create(
                name=name,
                model='Epson Thermal',  # Modelo genérico
                printer_type=printer_type,
                connection_string=connection_string,
                is_active=set_active
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Impresora "{name}" agregada correctamente',
                'printer_id': printer.id
            })
            
        except Exception as e:
            logger.error(f"Error adding printer: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return render(request, 'app_impresora/add_printer.html')

@login_required
def quick_setup_printer(request):
    """Configuración rápida automática de impresora"""
    if request.method == 'POST':
        try:
            # Obtener impresoras Windows
            printers = get_windows_printers_info()
            
            # Buscar impresoras térmicas
            thermal_printers = [p for p in printers if is_thermal_printer(p['name'])]
            
            if not thermal_printers:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontraron impresoras térmicas'
                })
            
            # Usar la primera impresora térmica encontrada
            thermal_printer = thermal_printers[0]
            
            # Desactivar impresoras existentes
            PrinterConfiguration.objects.update(is_active=False)
            
            # Crear configuración automática
            printer = PrinterConfiguration.objects.create(
                name=f"{thermal_printer['name']} (Auto)",
                model='Epson Thermal',
                printer_type='USB',
                connection_string=thermal_printer['name'],
                is_active=True
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Impresora configurada automáticamente',
                'printer_name': printer.name,
                'printer_id': printer.id
            })
            
        except Exception as e:
            logger.error(f"Error in quick setup: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Error en la configuración automática'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def get_windows_printers(request):
    """Obtiene lista de impresoras Windows"""
    try:
        printers = get_windows_printers_info()
        return JsonResponse({
            'success': True,
            'printers': printers
        })
    except Exception as e:
        logger.error(f"Error getting Windows printers: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error obteniendo impresoras'
        })

def get_windows_printers_info():
    """Obtiene información de impresoras Windows usando PowerShell"""
    try:
        cmd = [
            'powershell', '-Command',
            'Get-Printer | Select-Object Name, DriverName, PortName | ConvertTo-Json'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            printers_data = json.loads(result.stdout) if result.stdout.strip() else []
            if not isinstance(printers_data, list):
                printers_data = [printers_data]
            
            return [
                {
                    'name': p.get('Name', ''),
                    'driver': p.get('DriverName', ''),
                    'port': p.get('PortName', ''),
                    'is_thermal': is_thermal_printer(p.get('Name', ''))
                }
                for p in printers_data
            ]
    except Exception as e:
        logger.error(f"Error getting Windows printers: {e}")
    
    return []

def is_thermal_printer(printer_name):
    """Detecta si una impresora es térmica basado en el nombre"""
    thermal_keywords = [
        'thermal', 'receipt', 'tm-', 'epson', 'star', 'citizen',
        'pos', 'ticket', 'tmu', 'tsp', 'térmica'
    ]
    
    printer_name_lower = printer_name.lower()
    return any(keyword in printer_name_lower for keyword in thermal_keywords)

@login_required
def toggle_simulation(request):
    """Alternar modo simulación"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            enable = data.get('enable', True)
            
            # Actualizar cache
            cache.set('printer_simulation_mode', enable, 86400)
            
            # Recargar servicio
            printer_service.reload_simulation_mode()
            
            return JsonResponse({
                'success': True,
                'message': f'Modo {"simulación" if enable else "real"} activado',
                'simulation_mode': enable
            })
            
        except Exception as e:
            logger.error(f"Error toggling simulation: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Error cambiando modo'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required 
def test_printer(request):
    """Prueba la impresora configurada"""
    if request.method == 'POST':
        success, message = printer_service.test_printer()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'message': message
            })
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
            
        return redirect('printer_dashboard')
    
    return HttpResponse('Método no permitido', status=405)

@login_required
def print_client_qr(request, client_id):
    """Imprime el código QR de un cliente específico"""
    try:
        cliente = get_object_or_404(Cliente, id=client_id)
        
        # Verificar que el cliente tenga QR generado
        if not cliente.qr_image:
            # Intentar generar el QR si no existe
            cliente.generate_qr_with_data()
            cliente.save()
        
        success = printer_service.print_qr_ticket(cliente)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'message': 'Ticket impreso exitosamente' if success else 'Error al imprimir ticket'
            })
        
        if success:
            messages.success(request, f'Ticket impreso para {cliente.get_display_name()}')
        else:
            messages.error(request, 'Error al imprimir el ticket')
            
        return redirect('dashboard')
        
    except Exception as e:
        logger.error(f"Error imprimiendo QR para cliente {client_id}: {e}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
        
        messages.error(request, f'Error al imprimir: {str(e)}')
        return redirect('dashboard')

@login_required
def printer_config(request):
    """Configuración de impresoras"""
    if request.method == 'POST':
        # Aquí manejaremos la configuración de la impresora
        name = request.POST.get('name')
        printer_type = request.POST.get('printer_type')
        connection_string = request.POST.get('connection_string')
        
        # Desactivar otras impresoras si esta se marca como activa
        if request.POST.get('is_active'):
            PrinterConfiguration.objects.update(is_active=False)
        
        printer_config = PrinterConfiguration.objects.create(
            name=name,
            printer_type=printer_type,
            connection_string=connection_string,
            is_active=True
        )
        
        messages.success(request, 'Impresora configurada exitosamente')
        return redirect('printer_dashboard')
    
    return render(request, 'app_impresora/config.html')

@login_required
def printer_status(request):
    """Obtiene el estado de la impresora en formato JSON"""
    status = printer_service.get_printer_status()
    return JsonResponse(status)

@login_required
def print_jobs_list(request):
    """Lista todos los trabajos de impresión"""
    jobs = PrintJob.objects.all()[:50]  # Últimos 50 trabajos
    
    context = {
        'jobs': jobs
    }
    
    return render(request, 'app_impresora/jobs_list.html', context)

@login_required
def delete_printer(request):
    """Elimina una configuración de impresora (nueva versión JSON)"""
    if request.method == 'POST':
        try:
            logger.info(f"Delete printer request - Method: {request.method}")
            logger.info(f"Request body: {request.body}")
            logger.info(f"Content type: {request.content_type}")
            
            # Obtener datos desde JSON
            data = json.loads(request.body)
            printer_id = data.get('printer_id')
            
            logger.info(f"Parsed printer_id: {printer_id}")
            
            if not printer_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de impresora requerido'
                })
            
            printer = get_object_or_404(PrinterConfiguration, id=printer_id)
            printer_name = printer.name
            
            logger.info(f"Found printer: {printer_name}")
            
            # Verificar si es la única impresora activa
            active_printers = PrinterConfiguration.objects.filter(is_active=True).count()
            if printer.is_active and active_printers == 1:
                logger.warning(f"Attempting to delete only active printer: {printer_name}")
                return JsonResponse({
                    'success': False,
                    'message': 'No puedes eliminar la única impresora activa. Configura otra impresora primero.'
                })
            
            # Verificar si tiene trabajos de impresión asociados
            jobs_count = PrintJob.objects.filter(printer=printer).count()
            
            if jobs_count > 0:
                logger.info(f"Deleting {jobs_count} associated jobs")
                # Eliminar trabajos asociados automáticamente
                PrintJob.objects.filter(printer=printer).delete()
            
            # Eliminar la impresora
            printer.delete()
            logger.info(f"Printer {printer_name} deleted successfully")
            
            return JsonResponse({
                'success': True,
                'message': f'Impresora "{printer_name}" eliminada correctamente'
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Datos JSON inválidos'
            })
        except Exception as e:
            logger.error(f"Error eliminando impresora: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Error eliminando impresora: {str(e)}'
            })
    
    logger.warning(f"Invalid method for delete_printer: {request.method}")
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def delete_printer_old(request, printer_id):
    """Elimina una configuración de impresora (versión antigua)"""
    if request.method == 'POST':
        try:
            printer = get_object_or_404(PrinterConfiguration, id=printer_id)
            printer_name = printer.name
            
            # Verificar si es la única impresora activa
            active_printers = PrinterConfiguration.objects.filter(is_active=True).count()
            if printer.is_active and active_printers == 1:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'No puede eliminar la única impresora activa. Configure otra impresora primero.'
                    })
                
                messages.error(request, 'No puede eliminar la única impresora activa.')
                return redirect('printer_dashboard')
            
            # Verificar si tiene trabajos de impresión asociados
            jobs_count = PrintJob.objects.filter(printer=printer).count()
            
            if jobs_count > 0:
                # Preguntar si quiere eliminar también los trabajos
                force_delete = request.POST.get('force_delete') == 'true'
                if not force_delete:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': f'Esta impresora tiene {jobs_count} trabajos asociados. ¿Desea eliminarlos también?',
                            'needs_confirmation': True,
                            'jobs_count': jobs_count
                        })
                    
                    messages.warning(request, f'Esta impresora tiene {jobs_count} trabajos asociados.')
                    return redirect('printer_dashboard')
                else:
                    # Eliminar trabajos asociados
                    PrintJob.objects.filter(printer=printer).delete()
            
            printer.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Impresora "{printer_name}" eliminada correctamente'
                })
            
            messages.success(request, f'Impresora "{printer_name}" eliminada correctamente')
            return redirect('printer_dashboard')
            
        except Exception as e:
            logger.error(f"Error eliminando impresora {printer_id}: {e}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Error al eliminar la impresora: {str(e)}'
                })
            
            messages.error(request, f'Error al eliminar la impresora: {str(e)}')
            return redirect('printer_dashboard')
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def toggle_printer_status(request):
    """Activa o desactiva una impresora (nueva versión JSON)"""
    if request.method == 'POST':
        try:
            # Obtener datos desde JSON
            data = json.loads(request.body)
            printer_id = data.get('printer_id')
            activate = data.get('activate', True)
            
            if not printer_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de impresora requerido'
                })
            
            printer = get_object_or_404(PrinterConfiguration, id=printer_id)
            
            if activate:
                # Activar impresora (desactivar otras primero)
                PrinterConfiguration.objects.update(is_active=False)
                printer.is_active = True
                printer.save()
                message = f'Impresora "{printer.name}" activada'
            else:
                # Verificar que no sea la única activa
                active_count = PrinterConfiguration.objects.filter(is_active=True).count()
                if printer.is_active and active_count == 1:
                    return JsonResponse({
                        'success': False,
                        'message': 'No puedes desactivar la única impresora activa'
                    })
                
                # Desactivar impresora
                printer.is_active = False
                printer.save()
                message = f'Impresora "{printer.name}" desactivada'
            
            # Recargar configuración del servicio
            printer_service.reload_printer_config()
            
            return JsonResponse({
                'success': True,
                'message': message,
                'printer_id': printer.id,
                'is_active': printer.is_active
            })
            
        except Exception as e:
            logger.error(f"Error toggling printer status: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def toggle_printer_status_old(request, printer_id):
    """Activa o desactiva una impresora (versión antigua)"""
    if request.method == 'POST':
        try:
            printer = get_object_or_404(PrinterConfiguration, id=printer_id)
            
            if printer.is_active:
                # Desactivar impresora
                printer.is_active = False
                printer.save()
                message = f'Impresora "{printer.name}" desactivada'
            else:
                # Activar impresora (desactivar otras primero)
                PrinterConfiguration.objects.update(is_active=False)
                printer.is_active = True
                printer.save()
                message = f'Impresora "{printer.name}" activada'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'is_active': printer.is_active
                })
            
            messages.success(request, message)
            return redirect('printer_dashboard')
            
        except Exception as e:
            logger.error(f"Error cambiando estado de impresora {printer_id}: {e}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Error: {str(e)}'
                })
            
            messages.error(request, f'Error: {str(e)}')
            return redirect('printer_dashboard')
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def toggle_simulation_mode(request):
    """Habilita/deshabilita el modo simulación de impresora"""
    if request.method == 'POST':
        enable = request.POST.get('enable') == 'true'
        printer_service.enable_simulation_mode(enable)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'simulation_mode': printer_service.simulation_mode,
                'message': f'Modo simulación {"habilitado" if enable else "deshabilitado"}'
            })
        
        message = f'Modo simulación {"habilitado" if enable else "deshabilitado"}'
        messages.success(request, message)
        return redirect('printer_dashboard')
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

# Vista API para imprimir automáticamente cuando se registra un cliente
@csrf_exempt
def auto_print_qr(request):
    """API para impresión automática de QR al registrar cliente"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            client_id = data.get('client_id')
            
            if not client_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de cliente requerido'
                })
            
            cliente = get_object_or_404(Cliente, id=client_id)
            success = printer_service.print_qr_ticket(cliente)
            
            return JsonResponse({
                'success': success,
                'message': 'Ticket impreso automáticamente' if success else 'Error en impresión automática'
            })
            
        except Exception as e:
            logger.error(f"Error en impresión automática: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def test_specific_printer(request, printer_id):
    """Probar una impresora específica"""
    if request.method == 'POST':
        try:
            printer = get_object_or_404(PrinterConfiguration, id=printer_id)
            
            # Temporalmente activar esta impresora para la prueba
            original_active = PrinterConfiguration.objects.filter(is_active=True).first()
            
            PrinterConfiguration.objects.update(is_active=False)
            printer.is_active = True
            printer.save()
            
            # Recargar servicio
            printer_service.reload_printer_config()
            
            # Probar impresión
            success, message = printer_service.test_printer()
            
            # Restaurar impresora activa original
            if original_active:
                PrinterConfiguration.objects.update(is_active=False)
                original_active.is_active = True
                original_active.save()
                printer_service.reload_printer_config()
            
            return JsonResponse({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"Error testing printer {printer_id}: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def retry_print_job(request, job_id):
    """Reintentar un trabajo de impresión fallido"""
    if request.method == 'POST':
        try:
            job = get_object_or_404(PrintJob, id=job_id)
            
            if job.status != 'FAILED':
                return JsonResponse({
                    'success': False,
                    'message': 'Solo se pueden reintentar trabajos fallidos'
                })
            
            # Obtener cliente asociado
            try:
                cliente = Cliente.objects.get(id=job.client_id)
            except Cliente.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Cliente no encontrado'
                })
            
            # Intentar imprimir nuevamente
            success = printer_service.print_qr_ticket(cliente)
            
            return JsonResponse({
                'success': success,
                'message': 'Ticket reenviado a impresora' if success else 'Error al reintentar impresión'
            })
            
        except Exception as e:
            logger.error(f"Error retrying print job {job_id}: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def save_design_config(request):
    """Guardar configuración de diseño de tickets"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validar datos
            font = data.get('font', 'courier')
            if font not in ['courier', 'arial', 'times']:
                font = 'courier'
            
            font_size = int(data.get('fontSize', 12))
            if font_size < 8 or font_size > 16:
                font_size = 12
                
            ticket_width = int(data.get('ticketWidth', 80))
            if ticket_width < 58 or ticket_width > 80:
                ticket_width = 80
            
            # Obtener o crear configuración activa
            from .models import TicketDesignConfiguration
            config, created = TicketDesignConfiguration.objects.get_or_create(
                is_active=True,
                defaults={
                    'name': 'Configuración personalizada',
                    'font': font,
                    'font_size': font_size,
                    'ticket_width': ticket_width,
                    'show_logo': data.get('showLogo', True),
                    'show_fecha': data.get('showFecha', True),
                    'show_qr': data.get('showQr', True),
                    'show_footer': data.get('showFooter', True),
                    'header_text': data.get('headerText', 'SISTEMA DE PARKING\nControl de Acceso'),
                    'footer_text': data.get('footerText', 'Conserve este ticket\nGracias por su visita')
                }
            )
            
            if not created:
                # Actualizar configuración existente
                config.font = font
                config.font_size = font_size
                config.ticket_width = ticket_width
                config.show_logo = data.get('showLogo', True)
                config.show_fecha = data.get('showFecha', True)
                config.show_qr = data.get('showQr', True)
                config.show_footer = data.get('showFooter', True)
                config.header_text = data.get('headerText', 'SISTEMA DE PARKING\nControl de Acceso')
                config.footer_text = data.get('footerText', 'Conserve este ticket\nGracias por su visita')
                config.save()
            
            # También guardar en cache para compatibilidad
            design_config = config.to_dict()
            cache.set('printer_design_config', design_config, timeout=None)
            
            logger.info(f"Design configuration saved to database and cache: {design_config}")
            
            return JsonResponse({
                'success': True,
                'message': 'Configuración de diseño guardada exitosamente'
            })
            
        except Exception as e:
            logger.error(f"Error saving design config: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Error al guardar configuración: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required  
def get_design_config(request):
    """Obtener configuración de diseño actual"""
    try:
        from .models import TicketDesignConfiguration
        
        # Intentar obtener desde la base de datos primero
        active_config = TicketDesignConfiguration.objects.filter(is_active=True).first()
        
        if active_config:
            design_config = active_config.to_dict()
        else:
            # Fallback al cache si no hay configuración en BD
            design_config = cache.get('printer_design_config', {
                'font': 'courier',
                'fontSize': 12,
                'ticketWidth': 80,
                'showLogo': True,
                'showFecha': True,
                'showQr': True,
                'showFooter': True,
                'headerText': 'SISTEMA DE PARKING\nControl de Acceso',
                'footerText': 'Conserve este ticket\nGracias por su visita'
            })
        
        return JsonResponse({
            'success': True,
            'config': design_config
        })
        
    except Exception as e:
        logger.error(f"Error getting design config: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def print_preview(request):
    """Imprimir ticket de previsualización con datos personalizados"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            cedula = data.get('cedula', '12345678')
            nombre = data.get('nombre', 'Cliente de Prueba')
            vehiculo = data.get('vehiculo', 'auto')
            placa = data.get('placa', 'TEST-123')
            design_config = data.get('design_config', {})
            
            # Crear cliente temporal para la previsualización
            temp_cliente_data = {
                'cedula': cedula,
                'nombre': nombre,
                'tipo_vehiculo': vehiculo,
                'placa': placa,
                'is_preview': True
            }
            
            # Verificar que hay una impresora activa
            active_printer = PrinterConfiguration.objects.filter(is_active=True).first()
            if not active_printer:
                return JsonResponse({
                    'success': False,
                    'message': 'No hay impresoras activas configuradas'
                })
            
            # Guardar configuración de diseño temporalmente
            if design_config:
                cache.set('printer_design_config', design_config, timeout=300)  # 5 minutos
            
            # Imprimir usando el servicio de impresión con datos personalizados
            success = printer_service.print_preview_ticket(temp_cliente_data, design_config)
            
            # Crear registro del trabajo de impresión
            PrintJob.objects.create(
                printer=active_printer,
                client_id=f"preview_{cedula}",
                status='SUCCESS' if success else 'FAILED',
                details=f"Ticket de previsualización - {nombre} ({placa})"
            )
            
            logger.info(f"Preview ticket printed: {success} for {nombre}")
            
            return JsonResponse({
                'success': success,
                'message': f'Ticket de previsualización {"enviado a la impresora" if success else "falló al enviar"}'
            })
            
        except Exception as e:
            logger.error(f"Error printing preview: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Error al imprimir previsualización: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})
