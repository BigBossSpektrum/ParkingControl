# Configuración de Impresora Epson M244A

Este documento explica cómo configurar e integrar la impresora térmica Epson M244A con el sistema de control de parking.

## 📋 Características

- ✅ Impresión automática de tickets QR al registrar clientes
- ✅ Soporte para conexiones USB, Serial y Red
- ✅ Interface web para configuración
- ✅ Comandos de línea para gestión
- ✅ Registro de trabajos de impresión
- ✅ Pruebas de conectividad

## 🔧 Instalación de Dependencias

Las dependencias se instalan automáticamente, pero si necesita instalarlas manualmente:

```bash
pip install python-escpos pywin32 pyserial
```

## 🖨️ Configuración de Hardware

### Conexión USB (Recomendado)

1. **Conectar la impresora por USB**
2. **Instalar drivers oficiales de Epson**
   - Descargar desde: https://epson.com/support
   - Buscar modelo: TM-M244A o M244A
3. **Agregar impresora en Windows**
   - Panel de Control > Dispositivos e Impresoras
   - Agregar impresora > Seleccionar impresora USB
4. **Anotar el nombre exacto** como aparece en Windows

### Conexión Serial

1. **Conectar cable serial o adaptador USB-Serial**
2. **Identificar puerto COM**
   - Administrador de Dispositivos > Puertos (COM y LPT)
   - Anotar el puerto (ej: COM3)
3. **Configurar velocidad**: 9600 baudios (estándar)

### Conexión de Red

1. **Configurar IP estática en la impresora**
2. **Verificar conectividad de red**
3. **Usar puerto estándar**: 9100

## ⚙️ Configuración del Software

### Opción 1: Interface Web

1. Acceder al dashboard principal
2. Hacer clic en "Configurar Impresora" (solo administradores)
3. Completar el formulario:
   - **Nombre**: Nombre descriptivo
   - **Tipo de conexión**: USB/Serial/Red
   - **Cadena de conexión**: Según el tipo
   - **Configuración de papel**: 80mm (estándar)

### Opción 2: Línea de Comandos

```bash
# Ver impresoras configuradas
python manage.py setup_printer --list

# Configurar impresora USB
python manage.py setup_printer --type USB --connection "EPSON TM-M244A Receipt"

# Configurar impresora Serial
python manage.py setup_printer --type SERIAL --connection "COM3"

# Configurar impresora de Red
python manage.py setup_printer --type NETWORK --connection "192.168.1.100:9100"

# Configurar y probar
python manage.py setup_printer --type USB --connection "EPSON TM-M244A Receipt" --test
```

## 📝 Cadenas de Conexión por Tipo

### USB
```
Ejemplos válidos:
- "EPSON TM-M244A Receipt"
- "Epson M244A" 
- "TM-M244A"
```

### Serial
```
Ejemplos válidos:
- "COM1"
- "COM3"
- "COM5"
```

### Red
```
Ejemplos válidos:
- "192.168.1.100:9100"
- "192.168.0.50:9100"
- "10.0.0.100:9100"
```

## 🧪 Pruebas de Funcionamiento

### Desde la Interface Web
1. Ir a "Configurar Impresora"
2. Hacer clic en "Probar Impresora"
3. Verificar que se imprima una página de prueba

### Desde Línea de Comandos
```bash
python manage.py setup_printer --list
python manage.py setup_printer --type USB --connection "EPSON TM-M244A Receipt" --test
```

### Prueba Manual
1. Registrar un cliente en el sistema
2. Verificar que se imprima automáticamente el ticket QR
3. Comprobar que el ticket contenga:
   - Código QR
   - ID del cliente
   - Datos del vehículo
   - Fecha y hora de entrada

## 🔍 Solución de Problemas

### Error: "No se pudo conectar por USB"
- ✅ Verificar que la impresora esté encendida
- ✅ Reinstalar drivers de Epson
- ✅ Probar con nombre alternativo de impresora
- ✅ Verificar conexión USB

### Error: "Puerto COM no disponible"
- ✅ Verificar puerto en Administrador de Dispositivos
- ✅ Cerrar otros programas que usen el puerto
- ✅ Probar con otro puerto COM

### Error: "Conexión de red rechazada"
- ✅ Verificar IP y puerto
- ✅ Comprobar conectividad de red (ping)
- ✅ Verificar que el puerto 9100 esté abierto
- ✅ Revisar configuración de firewall

### La impresión automática no funciona
- ✅ Verificar que hay una impresora marcada como "Activa"
- ✅ Comprobar logs de Django
- ✅ Probar impresión manual desde el panel de impresora

## 📊 Monitoreo y Logs

### Ver Trabajos de Impresión
- Interface web: Panel de Impresora > Ver Todos los Trabajos
- Admin Django: Trabajos de Impresión

### Estados de Trabajos
- **PENDING**: En cola
- **PRINTING**: Enviando a impresora
- **SUCCESS**: Impreso exitosamente
- **FAILED**: Error en impresión

### Logs del Sistema
Los logs de la impresora se guardan en los logs de Django:
```bash
# Ver logs en tiempo real
tail -f debug.log
```

## 🔐 Permisos y Seguridad

- Solo **administradores** pueden configurar impresoras
- Todos los usuarios pueden ver el estado
- Los trabajos de impresión se registran con ID del usuario
- Las configuraciones se guardan en la base de datos

## 🚀 Uso en Producción

### Configuración Recomendada
- **Conexión**: USB (más estable)
- **Ubicación**: Cerca de la computadora
- **Papel**: Rollo térmico 80mm x 50mm
- **Drivers**: Siempre usar drivers oficiales de Epson

### Mantenimiento
- Limpiar cabezal de impresión regularmente
- Usar papel térmico de calidad
- Verificar conectividad diariamente
- Monitorear trabajos fallidos

## 📞 Soporte

Si tienes problemas con la configuración:

1. **Revisar este documento**
2. **Ejecutar pruebas de diagnóstico**
3. **Consultar logs del sistema**
4. **Verificar hardware y drivers**

### Comandos de Diagnóstico
```bash
# Estado actual
python manage.py setup_printer --list

# Prueba rápida
python manage.py setup_printer --type USB --connection "NombreImpresora" --test

# Ver trabajos recientes
python manage.py shell -c "from app_impresora.models import PrintJob; [print(f'{j.id}: {j.status} - {j.created_at}') for j in PrintJob.objects.all()[:10]]"
```
