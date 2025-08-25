# 🚗 Sistema de Control de Parking - Guía de Uso

## Tabla de Contenidos
- [Login - Acceso al Sistema](#login---acceso-al-sistema)
- [Dashboard - Panel Principal](#dashboard---panel-principal)
- [Lista de Clientes - Gestión de Registros](#lista-de-clientes---gestión-de-registros)
- [Configurar Impresora - Ajustes de Dispositivo](#configurar-impresora---ajustes-de-dispositivo)
- [Panel Administrativo - Gestión Avanzada](#panel-administrativo---gestión-avanzada)

---

## 🔐 Login - Acceso al Sistema

### Proceso de Autenticación
1. **Ingrese su nombre de usuario** asignado por el administrador
2. **Introduzca su contraseña personal** de forma segura
3. **Haga clic en "Iniciar Sesión"** para acceder al sistema

### ⚠️ Consideraciones Importantes
- ✅ Use únicamente las credenciales proporcionadas por el administrador
- 📝 El sistema registra todos los accesos por motivos de seguridad
- 🆘 En caso de problemas de acceso, contacte inmediatamente al supervisor
- 🔒 No comparta sus credenciales con otros usuarios

---

## 🏠 Dashboard - Panel Principal

### Vista General del Sistema
- 📊 **Estadísticas en tiempo real:** Visualización de clientes registrados hoy y vehículos actualmente en el parking
- 🎯 **Acciones rápidas:** Funcionalidades disponibles según el rol del usuario
- 👤 **Información del usuario:** Nombre y rol actual en la esquina superior

### Funciones Principales

#### 1. 🚗 Registro de Entrada
- Ingrese la placa del vehículo en el formulario
- El sistema genera automáticamente el código QR y código de barras
- Se imprime el ticket de entrada (si la impresora está configurada)

#### 2. 🚪 Proceso de Salida
- Escanee el código QR del ticket o ingrese manualmente la placa
- El sistema calcula automáticamente el tiempo y costo
- Procese el pago y genere el comprobante de salida

#### 3. 🔍 Búsqueda Rápida
- Localice vehículos por número de placa
- Busque por código QR o ID de registro
- Consulte el estado actual de cualquier vehículo

### 💡 Consejos de Uso
- Utilice los badges superiores para monitorear la ocupación actual del parking
- Las estadísticas se actualizan en tiempo real
- Mantenga siempre visible el panel para un control eficiente

---

## 📋 Lista de Clientes - Gestión de Registros

### Funcionalidades Principales

#### 🔍 Búsqueda Avanzada
- **Por placa:** Ingrese número completo o parcial
- **Por fecha:** Seleccione rango de fechas específico
- **Por estado:** Filtre entre activos, finalizados, etc.
- **Por código QR:** Búsqueda directa por código único

#### 📊 Sistema de Filtros
- **Registros Activos:** Vehículos actualmente en el parking
- **Registros Finalizados:** Estancias completadas y pagadas
- **Por fecha específica:** Registros de un día particular
- **Por rango de tiempo:** Análisis de períodos específicos

#### 👁️ Visualización de Datos
- Información completa de cada registro
- Tiempo de estancia calculado automáticamente
- Estado de pago y método utilizado
- Códigos QR y de barras asociados

### Acciones Disponibles

#### 1. 📄 Ver Detalles Completos
- Información detallada del cliente y vehículo
- Historial completo de la estancia
- Códigos generados y métodos de pago

#### 2. ✅ Finalizar Estancia Manual
- Para casos especiales o emergencias
- Cálculo manual del tiempo y costo
- Generación de comprobante especial

#### 3. 🖨️ Imprimir Comprobantes
- Reimprimir tickets de entrada
- Generar comprobantes de pago
- Imprimir reportes de estancia

### ⚡ Control de Acceso
> **Importante:** Solo usuarios con rol autorizado pueden acceder a la lista completa de clientes

---

## 🖨️ Configurar Impresora - Ajustes de Dispositivo

### Proceso de Configuración Paso a Paso

#### 1. 🔍 Detectar Impresora
- El sistema busca automáticamente dispositivos conectados
- Verifica la compatibilidad con impresoras térmicas
- Lista todos los dispositivos disponibles

#### 2. 📋 Seleccionar Modelo
- Elija su impresora específica de la lista detectada
- Configure los parámetros de impresión
- Ajuste el tamaño de papel y resolución

#### 3. 🧪 Probar Conexión
- Imprima un ticket de prueba
- Verifique la calidad de impresión
- Confirme que todos los elementos se imprimen correctamente

#### 4. 💾 Guardar Configuración
- Confirme todos los ajustes realizados
- Establezca la impresora como predeterminada
- Active la impresión automática si es necesario

### ✅ Lista de Verificación Pre-configuración
- [ ] Impresora encendida y correctamente conectada al sistema
- [ ] Papel térmico cargado en la orientación correcta
- [ ] Drivers de impresora instalados y actualizados
- [ ] Puerto USB o conexión de red funcional
- [ ] Suficiente papel para operación continua

### 🔧 Solución de Problemas
1. **Impresora no detectada:**
   - Verifique conexiones físicas (USB/Red)
   - Reinicie la impresora y el sistema
   - Confirme instalación de drivers

2. **Calidad de impresión deficiente:**
   - Limpie el cabezal de impresión
   - Verifique el tipo de papel térmico
   - Ajuste la configuración de densidad

3. **Errores de comunicación:**
   - Revise la configuración del puerto
   - Verifique permisos del sistema
   - Contacte soporte técnico si persiste

---

## ⚙️ Panel Administrativo - Gestión Avanzada

> **🚨 ACCESO RESTRINGIDO:** Solo para usuarios con rol de Administrador

### 👥 Gestión de Usuarios

#### Administración de Cuentas
- **Crear nuevos operadores:** Registro de personal autorizado
- **Modificar cuentas existentes:** Actualización de datos y permisos
- **Desactivar usuarios:** Control de acceso por seguridad
- **Resetear contraseñas:** Gestión de credenciales

#### 🔐 Asignación de Roles y Permisos
- **Operador Básico:** Registro de entrada/salida únicamente
- **Operador Avanzado:** Acceso a lista de clientes y reportes
- **Supervisor:** Control de configuraciones y personal
- **Administrador:** Acceso completo al sistema

#### 📊 Monitoreo de Actividad
- Registro de todas las acciones del personal
- Tiempos de sesión y actividad por usuario
- Identificación de patrones y anomalías
- Reportes de productividad

### 💰 Configuración del Sistema

#### Gestión de Tarifas
- **Configurar precios:** Por hora, día, o períodos especiales
- **Horarios especiales:** Tarifas nocturnas, fines de semana
- **Descuentos:** Para clientes frecuentes o promociones
- **Tarifas por zona:** Diferentes precios según ubicación

#### 🏗️ Configuración del Parking
- **Capacidad total:** Número máximo de vehículos
- **Zonas especiales:** Áreas VIP, discapacitados, etc.
- **Horarios de operación:** Configuración de apertura/cierre
- **Políticas de tiempo:** Tiempo máximo de estancia

#### 📈 Generación de Reportes
- **Reportes diarios:** Ingresos, ocupación, transacciones
- **Análisis semanal/mensual:** Tendencias y patrones
- **Reportes financieros:** Estados de cuenta y facturación
- **Reportes de operaciones:** Eficiencia y rendimiento

### 🔧 Mantenimiento del Sistema

#### 🔄 Respaldo de Datos
- Copias de seguridad automáticas programadas
- Respaldo manual bajo demanda
- Verificación de integridad de datos
- Procedimientos de recuperación

#### 📋 Logs del Sistema
- Registro detallado de todas las operaciones
- Monitoreo de errores y excepciones
- Análisis de rendimiento del sistema
- Auditoría de seguridad

#### ⚡ Configuraciones Avanzadas
- Parámetros de conexión de base de datos
- Configuración de servicios externos
- Ajustes de rendimiento y optimización
- Integraciones con sistemas externos

### ⚠️ Advertencias Críticas
> **IMPORTANTE:** Los cambios realizados en el panel administrativo afectan todo el sistema y todos los usuarios. Realice modificaciones con extrema precaución y siempre mantenga respaldos actualizados.

---

## 📞 Soporte y Contacto

### 🆘 En Caso de Emergencia
- **Problemas técnicos críticos:** Contacte inmediatamente al administrador del sistema
- **Fallas de impresora:** Verifique conexiones físicas antes de reportar
- **Errores de cálculo:** Documente el caso y reporte para revisión

### 📧 Información de Contacto
- **Soporte Técnico:** [Información de contacto]
- **Administrador del Sistema:** [Información de contacto]
- **Manual Técnico Completo:** [Ubicación del manual detallado]

---

## 🔄 Actualizaciones del Sistema
**Última actualización:** Agosto 25, 2025  
**Versión del documento:** 1.0  
**Sistema:** Parking Control v2025.08

---

*© 2025 Parking Control System. Todos los derechos reservados.*
