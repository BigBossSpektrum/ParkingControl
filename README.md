# 🚗 ParkingControl - Sistema de Control de Estacionamiento

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.0+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

Sistema integral de control de estacionamiento con generación automática de códigos QR, códigos de barras, gestión de tarifas y control de acceso por roles.

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Requisitos del Sistema](#-requisitos-del-sistema)
- [Instalación](#-instalación)
- [Configuración Inicial](#-configuración-inicial)
- [Uso del Sistema](#-uso-del-sistema)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [API y Endpoints](#-api-y-endpoints)
- [Gestión de Roles](#-gestión-de-roles)
- [Configuración de Impresora](#-configuración-de-impresora)
- [Solución de Problemas](#-solución-de-problemas)
- [Contribución](#-contribución)
- [Licencia](#-licencia)

## 🚀 Características Principales

### ✨ Funcionalidades Core
- **Registro de Entrada/Salida:** Control automatizado de vehículos
- **Generación de Códigos:** QR y códigos de barras únicos por registro
- **Cálculo de Tarifas:** Sistema automático basado en tiempo de estancia
- **Impresión de Tickets:** Soporte para impresoras térmicas
- **Gestión de Usuarios:** Sistema de roles y permisos granular
- **Reportes en Tiempo Real:** Estadísticas y métricas actualizadas

### 🔧 Tecnologías Utilizadas
- **Backend:** Django 4.0+ (Python)
- **Base de Datos:** SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend:** Bootstrap 5, HTML5, CSS3, JavaScript
- **Códigos:** QRCode, python-barcode
- **Impresión:** python-escpos, Pillow
- **Autenticación:** Django Auth System

## 📋 Requisitos del Sistema

### Requisitos Mínimos
- **Sistema Operativo:** Windows 10/11, Linux Ubuntu 18.04+, macOS 10.14+
- **Python:** Versión 3.8 o superior
- **RAM:** Mínimo 4GB (8GB recomendado)
- **Almacenamiento:** 1GB libre para la aplicación + espacio para datos
- **Red:** Conexión a internet para instalación de dependencias

### Hardware Opcional
- **Impresora Térmica:** Compatible con ESC/POS (recomendada para tickets)
- **Lector de Códigos:** QR/Barcode scanner (opcional)
- **Cámara Web:** Para lectura de códigos QR (opcional)

## 🛠 Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/BigBossSpektrum/ParkingControl.git
cd ParkingControl
```

### 2. Crear Entorno Virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Base de Datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Crear Superusuario
```bash
python manage.py createsuperuser
```

### 6. Ejecutar el Servidor
```bash
python manage.py runserver
```

El sistema estará disponible en: `http://localhost:8000`

## ⚙️ Configuración Inicial

### 1. Acceso Administrativo
1. Navegue a `http://localhost:8000/admin`
2. Ingrese con las credenciales del superusuario
3. Configure los perfiles de usuario y roles

### 2. Configuración de Tarifas
```python
# En el admin de Django, configure:
# - Tarifas por hora
# - Tarifas especiales (nocturnas, fines de semana)
# - Descuentos y promociones
```

### 3. Configuración de Impresora (Opcional)
1. Conecte la impresora térmica al sistema
2. Acceda a la sección "Configurar Impresora"
3. Siga el asistente de configuración

## 🎯 Uso del Sistema

### 🔐 1. Login y Autenticación

#### Acceso al Sistema
```
URL: http://localhost:8000/login
```

**Proceso:**
1. **Usuario:** Ingrese su nombre de usuario asignado
2. **Contraseña:** Introduzca su contraseña personal
3. **Autenticación:** El sistema verificará credenciales y rol
4. **Redirección:** Acceso automático al dashboard según permisos

**Roles Disponibles:**
- `ADMIN`: Acceso completo al sistema
- `SUPERVISOR`: Gestión de operaciones y reportes
- `OPERADOR`: Registro de entrada/salida
- `VIEWER`: Solo visualización de datos

### 🏠 2. Dashboard Principal

#### Funcionalidades del Dashboard
```
URL: http://localhost:8000/dashboard
```

**Elementos Principales:**
- **Estadísticas en Tiempo Real:** Clientes hoy, vehículos en parking
- **Formulario de Registro:** Entrada rápida de vehículos
- **Búsqueda:** Localización rápida por placa o código
- **Acciones Rápidas:** Según rol del usuario

#### Registro de Entrada de Vehículo
```python
# Ejemplo de proceso:
1. Ingrese número de placa (formato: ABC-123)
2. Sistema genera automáticamente:
   - Código QR único
   - Código de barras
   - Timestamp de entrada
3. Se imprime ticket (si impresora configurada)
4. Registro guardado en base de datos
```

#### Proceso de Salida
```python
# Métodos de búsqueda:
1. Escaneo de código QR del ticket
2. Ingreso manual de placa
3. Búsqueda por ID de registro

# Cálculo automático:
- Tiempo de estancia
- Tarifa aplicable
- Total a pagar
```

### 📋 3. Lista de Clientes

#### Acceso y Permisos
```
URL: http://localhost:8000/lista-clientes
Requiere: Rol SUPERVISOR o superior
```

**Funcionalidades de Búsqueda:**
```python
# Filtros disponibles:
- Por placa de vehículo
- Por rango de fechas
- Por estado (activo/finalizado)
- Por código QR/ID
- Por método de pago
```

**Acciones Disponibles:**
- **Ver Detalles:** Información completa del registro
- **Finalizar Manualmente:** Para casos especiales
- **Reimprimir Ticket:** Generar duplicado
- **Exportar Datos:** CSV, PDF, Excel

### 🖨️ 4. Configuración de Impresora

#### Proceso de Configuración
```
URL: http://localhost:8000/configurar-impresora
Requiere: Rol ADMIN o SUPERVISOR
```

**Pasos de Configuración:**
```python
1. Detección automática de impresoras
2. Selección de modelo específico
3. Configuración de parámetros:
   - Tamaño de papel (58mm, 80mm)
   - Velocidad de impresión
   - Densidad de impresión
4. Prueba de impresión
5. Guardado de configuración
```

**Impresoras Compatibles:**
- Epson TM series
- Star Micronics
- Citizen
- Genéricas ESC/POS

### ⚙️ 5. Panel Administrativo

#### Gestión de Usuarios
```
URL: http://localhost:8000/admin
Requiere: Rol ADMIN
```

**Operaciones de Usuario:**
```python
# Crear nuevo usuario:
1. Datos personales (nombre, email)
2. Credenciales (username, password)
3. Asignación de rol
4. Permisos específicos

# Modificar usuario existente:
1. Cambiar información personal
2. Resetear contraseña
3. Modificar rol/permisos
4. Activar/desactivar cuenta
```

#### Configuración del Sistema
```python
# Configuraciones disponibles:
- Tarifas y precios
- Horarios de operación
- Capacidad del parking
- Políticas de tiempo máximo
- Configuración de reportes
- Backup automático
```

## 📁 Estructura del Proyecto

```
ParkingControl/
├── 📁 app_page/              # Aplicación principal
│   ├── 📁 templates/         # Templates HTML
│   ├── 📁 migrations/        # Migraciones de BD
│   ├── models.py            # Modelos de datos
│   ├── views.py             # Lógica de vistas
│   ├── urls.py              # URLs de la app
│   └── admin.py             # Configuración admin
├── 📁 app_impresora/         # Gestión de impresoras
├── 📁 app_qr/               # Generación de códigos
├── 📁 app_registration/      # Registro de usuarios
├── 📁 media/                # Archivos multimedia
│   ├── 📁 qr_codes/         # Códigos QR generados
│   └── 📁 barcodes/         # Códigos de barras
├── 📁 parking_site/         # Configuración principal
├── manage.py                # Comando principal Django
├── requirements.txt         # Dependencias Python
├── README.md               # Este archivo
├── WORKFLOW_SISTEMA.md     # Guía de uso detallada
└── SISTEMA_ROLES.md        # Documentación de roles
```

## 🔌 API y Endpoints

### Endpoints Principales
```python
# Autenticación
POST /login/                 # Iniciar sesión
POST /logout/                # Cerrar sesión

# Dashboard
GET  /dashboard/             # Panel principal
POST /registrar-entrada/     # Nuevo vehículo
POST /procesar-salida/       # Salida de vehículo

# Gestión
GET  /lista-clientes/        # Lista completa
GET  /cliente/<id>/          # Detalles específicos
POST /finalizar/<id>/        # Finalizar manualmente

# Códigos
GET  /qr/<codigo>/          # Información por QR
GET  /barcode/<codigo>/     # Información por barcode

# Impresión
POST /imprimir-ticket/      # Imprimir ticket
GET  /configurar-impresora/ # Config. impresora

# Admin
GET  /admin/                # Panel administrativo
```

### Ejemplo de Uso de API
```python
import requests

# Registrar entrada
data = {
    'placa': 'ABC-123',
    'tipo_vehiculo': 'auto'
}
response = requests.post('/registrar-entrada/', data=data)

# Procesar salida
data = {
    'codigo_qr': 'QR123456789'
}
response = requests.post('/procesar-salida/', data=data)
```

## 👥 Gestión de Roles

### Roles y Permisos

#### 🔴 ADMIN (Administrador)
```python
Permisos:
✅ Acceso completo al sistema
✅ Gestión de usuarios y roles
✅ Configuración de tarifas
✅ Backup y mantenimiento
✅ Reportes financieros
✅ Configuración de impresoras
```

#### 🟡 SUPERVISOR
```python
Permisos:
✅ Dashboard completo
✅ Lista de todos los clientes
✅ Finalizar registros manualmente
✅ Configurar impresoras
✅ Reportes operacionales
❌ Gestión de usuarios
❌ Configuración de tarifas
```

#### 🟢 OPERADOR
```python
Permisos:
✅ Dashboard básico
✅ Registrar entrada/salida
✅ Búsqueda de vehículos
✅ Imprimir tickets
❌ Lista completa de clientes
❌ Configuraciones del sistema
```

#### 🔵 VIEWER (Visualizador)
```python
Permisos:
✅ Dashboard solo lectura
✅ Búsqueda básica
❌ Registrar operaciones
❌ Modificar datos
❌ Configuraciones
```

### Asignación de Roles
```python
# En el admin de Django:
1. Crear perfil de usuario
2. Asignar rol específico
3. Configurar permisos adicionales si necesario
4. Activar/desactivar cuenta
```

## 🖨️ Configuración de Impresora

### Impresoras Compatibles
```python
# Marcas soportadas:
- Epson: TM-T20, TM-T82, TM-T88
- Star Micronics: TSP100, TSP650
- Citizen: CT-S310, CT-S4000
- Genéricas: ESC/POS compatibles
```

### Configuración Paso a Paso

#### 1. Conexión Física
```bash
# USB
- Conectar impresora al puerto USB
- Verificar que Windows reconoce el dispositivo
- Instalar drivers específicos del fabricante

# Red (Ethernet/WiFi)
- Configurar IP fija en la impresora
- Verificar conectividad: ping <ip_impresora>
- Configurar puerto de comunicación (9100)
```

#### 2. Configuración en el Sistema
```python
# Acceder a configuración:
1. Login como ADMIN o SUPERVISOR
2. Ir a "Configurar Impresora"
3. Seleccionar tipo de conexión
4. Elegir modelo de impresora
5. Configurar parámetros de impresión
6. Realizar prueba de impresión
7. Guardar configuración
```

#### 3. Parámetros de Configuración
```python
PRINTER_CONFIG = {
    'width': 80,              # Ancho en mm (58 o 80)
    'height': 'auto',         # Alto automático
    'dpi': 203,              # Resolución
    'speed': 'medium',        # Velocidad impresión
    'density': 'medium',      # Densidad de impresión
    'cut': True,             # Corte automático
    'encoding': 'utf-8'       # Codificación de texto
}
```

### Formato de Ticket
```
===============================
    PARKING CONTROL SYSTEM
===============================
Fecha: 25/08/2025 14:30:15
Placa: ABC-123
ID: #000123

[QR CODE]        [BARCODE]

Tarifa: $2.00/hora
Tiempo Max: 24 horas

Conserve este ticket
===============================
```

## 🔧 Solución de Problemas

### Problemas Comunes

#### 1. Error de Base de Datos
```bash
# Síntoma: "Database is locked" o errores de migración
# Solución:
python manage.py migrate --run-syncdb
python manage.py collectstatic
```

#### 2. Impresora No Detectada
```python
# Verificaciones:
1. Impresora encendida y conectada
2. Drivers instalados correctamente
3. Puerto USB/Red funcional
4. Permisos de sistema correctos

# Solución:
- Reinstalar drivers
- Cambiar puerto USB
- Verificar configuración de red
- Ejecutar como administrador
```

#### 3. Códigos QR No Generados
```python
# Verificar dependencias:
pip install qrcode[pil]
pip install python-barcode[images]

# Verificar permisos de carpeta:
chmod 755 media/qr_codes/
chmod 755 media/barcodes/
```

#### 4. Error de Permisos
```bash
# Linux/macOS:
sudo chown -R usuario:grupo .
chmod +x manage.py

# Windows:
# Ejecutar como administrador
```

### Logs del Sistema
```python
# Ubicación de logs:
debug.log                    # Log principal
logs/error.log              # Errores del sistema
logs/access.log             # Log de accesos
logs/printer.log            # Log de impresión

# Revisar logs:
tail -f debug.log
grep "ERROR" debug.log
```

### Comandos de Mantenimiento
```bash
# Limpiar cache
python manage.py clearcache

# Verificar integridad
python manage.py check

# Backup de base de datos
python manage.py dbbackup

# Restaurar backup
python manage.py dbrestore
```

## 📊 Reportes y Estadísticas

### Reportes Disponibles
```python
# Reportes diarios:
- Ingresos del día
- Vehículos registrados
- Tiempo promedio de estancia
- Ocupación máxima

# Reportes periódicos:
- Resumen semanal/mensual
- Análisis de tendencias
- Reportes financieros
- Estadísticas de operadores
```

### Exportación de Datos
```python
# Formatos soportados:
- CSV: Para análisis en Excel
- PDF: Para reportes impresos
- JSON: Para integración con otros sistemas
- Excel: Para análisis avanzado
```

## 🔄 Actualización del Sistema

### Proceso de Actualización
```bash
# 1. Backup de datos
python manage.py dbbackup

# 2. Actualizar código
git pull origin main

# 3. Actualizar dependencias
pip install -r requirements.txt

# 4. Ejecutar migraciones
python manage.py migrate

# 5. Recolectar archivos estáticos
python manage.py collectstatic

# 6. Reiniciar servidor
```

### Verificación Post-Actualización
```python
# Verificar:
1. Funcionalidad de login
2. Registro de vehículos
3. Generación de códigos
4. Impresión de tickets
5. Cálculo de tarifas
```

## 🚀 Despliegue en Producción

### Configuración para Producción
```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['tu-dominio.com', 'ip-servidor']

# Base de datos PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'parking_db',
        'USER': 'parking_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Servidor web (Nginx + Gunicorn)
# Configuración SSL/HTTPS
# Backup automático programado
```

### Consideraciones de Seguridad
```python
# Implementar:
- HTTPS obligatorio
- Autenticación de dos factores
- Logs de auditoría
- Backup encriptado
- Firewall configurado
- Actualizaciones de seguridad
```

## 📞 Soporte y Contacto

### Información de Contacto
- **Desarrollador:** BigBossSpektrum
- **Repositorio:** [GitHub - ParkingControl](https://github.com/BigBossSpektrum/ParkingControl)
- **Issues:** Reportar problemas en GitHub Issues
- **Documentación:** Ver archivos .md en el repositorio

### Recursos Adicionales
- **WORKFLOW_SISTEMA.md:** Guía detallada de uso
- **SISTEMA_ROLES.md:** Documentación de roles y permisos
- **CONFIGURACION_IMPRESORA.md:** Guía específica de impresoras

## 🤝 Contribución

### Cómo Contribuir
```bash
# 1. Fork del repositorio
git fork https://github.com/BigBossSpektrum/ParkingControl

# 2. Crear rama para feature
git checkout -b feature/nueva-funcionalidad

# 3. Realizar cambios y commit
git add .
git commit -m "Agregar nueva funcionalidad"

# 4. Push y crear Pull Request
git push origin feature/nueva-funcionalidad
```

### Estándares de Código
- **PEP 8:** Para código Python
- **Comentarios:** En español para código de negocio
- **Tests:** Incluir tests para nuevas funcionalidades
- **Documentación:** Actualizar README.md si es necesario

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 📈 Historial de Versiones

### v2025.08 (Actual)
- ✅ Sistema completo de control de parking
- ✅ Generación de códigos QR y barras
- ✅ Integración con impresoras térmicas
- ✅ Sistema de roles y permisos
- ✅ Dashboard en tiempo real
- ✅ Reportes y estadísticas

### Próximas Funcionalidades
- 🔄 API REST completa
- 🔄 App móvil para operadores
- 🔄 Integración con sistemas de pago
- 🔄 Reconocimiento automático de placas
- 🔄 Notificaciones push
- 🔄 Multi-idioma

---

## 🎯 Inicio Rápido

### Para Usuarios Nuevos
```bash
1. git clone https://github.com/BigBossSpektrum/ParkingControl.git
2. cd ParkingControl
3. python -m venv venv
4. source venv/bin/activate  # Linux/Mac
   # o venv\Scripts\activate  # Windows
5. pip install -r requirements.txt
6. python manage.py migrate
7. python manage.py createsuperuser
8. python manage.py runserver
9. Acceder a: http://localhost:8000
```

### Para Desarrollo
```bash
1. Seguir pasos de "Para Usuarios Nuevos"
2. python manage.py collectstatic
3. Configurar impresora (opcional)
4. Crear usuarios de prueba
5. Comenzar desarrollo
```

---

**¡Gracias por usar ParkingControl!** 🚗💚

*Para más información, consulte la documentación completa en los archivos .md del proyecto.*
