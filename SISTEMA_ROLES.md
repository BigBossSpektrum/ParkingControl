# Sistema de Roles - Parking Control

## Descripción General

Se ha implementado un sistema de roles con dos niveles de acceso para el sistema de control de parqueadero:

### Roles Disponibles

#### 1. **Administrador**
- **Acceso completo** a todas las funcionalidades del sistema
- Puede realizar todas las operaciones CRUD (Crear, Leer, Actualizar, Eliminar)

**Permisos:**
- ✅ Agregar usuarios/clientes
- ✅ Registrar salida de vehículos
- ✅ Ver lista completa de clientes
- ✅ Editar información de clientes
- ✅ Eliminar registros de clientes
- ✅ Ver códigos QR y registros
- ✅ Acceso al panel de administración de Django

#### 2. **Empleado**
- **Acceso limitado** solo a funciones operativas básicas
- Enfocado en las tareas diarias del parqueadero

**Permisos:**
- ✅ Agregar usuarios/clientes
- ✅ Registrar salida de vehículos
- ✅ Ver códigos QR y registros individuales
- ❌ Ver lista completa de clientes
- ❌ Editar información de clientes
- ❌ Eliminar registros de clientes
- ❌ Acceso al panel de administración

## Usuarios de Prueba

### Usuario Administrador
- **Usuario:** `admin`
- **Contraseña:** (configurada previamente)
- **Rol:** Administrador

### Usuario Empleado
- **Usuario:** `empleado`
- **Contraseña:** `empleado123`
- **Rol:** Empleado

## Características Implementadas

### 1. **Autenticación Visual**
- La barra de navegación muestra el nombre del usuario y su rol
- Diferentes colores e iconos para identificar rápidamente el nivel de acceso

### 2. **Restricciones de Interface**
- Los botones de "Editar" y "Eliminar" solo son visibles para administradores
- El enlace "Lista de Usuarios" solo aparece para administradores
- Panel informativo en el dashboard que explica las funciones disponibles

### 3. **Seguridad a Nivel de Backend**
- Decoradores personalizados que validan permisos en cada vista
- Respuestas AJAX apropiadas para peticiones sin permisos
- Redirecciones automáticas cuando se accede sin autorización

### 4. **Gestión de Perfiles**
- Creación automática de perfiles para nuevos usuarios
- Panel de administración integrado para gestionar roles
- Comandos de gestión para configuración inicial

## Flujo de Trabajo por Rol

### Para Empleados:
1. **Login** → Dashboard con funciones limitadas
2. **Registro de Clientes** → Formulario completo disponible
3. **Registro de Salidas** → Escaneo de QR o ingreso manual
4. **Visualización de QR** → Solo al crear registros

### Para Administradores:
1. **Login** → Dashboard con acceso completo
2. **Gestión Completa** → Todas las operaciones CRUD
3. **Lista de Clientes** → Vista completa con filtros
4. **Administración** → Acceso al panel de Django Admin

## Configuración Técnica

### Modelos
- **Perfil:** Relacionado 1:1 con User de Django
- **Métodos de Permiso:** `puede_editar_cliente()`, `puede_eliminar_cliente()`, etc.

### Decoradores
- `@require_edit_permission`: Para vistas de edición
- `@require_delete_permission`: Para vistas de eliminación
- `@require_view_list_permission`: Para vista de lista completa

### Context Processor
- Disponibilidad automática del perfil en todos los templates
- Información del rol accesible desde cualquier vista

## Comandos de Gestión

```bash
# Configurar perfiles para usuarios existentes
python manage.py setup_perfiles

# Crear usuario empleado de prueba
python manage.py crear_empleado
```

## Consideraciones de Seguridad

1. **Validación Doble:** Frontend (visual) + Backend (decoradores)
2. **Respuestas AJAX:** Manejo apropiado de errores de permisos
3. **Redirecciones:** Usuarios sin permisos son redirigidos automáticamente
4. **Logs:** Sistema de auditoría mediante mensajes de Django

## Personalización

El sistema está diseñado para ser fácilmente extensible:

- **Nuevos Roles:** Agregar opciones al campo `ROLES_CHOICES`
- **Nuevos Permisos:** Crear métodos en el modelo `Perfil`
- **Nuevos Decoradores:** Basados en los permisos del perfil

## Testing

Para probar el sistema:

1. Ingresar como `admin` → Verificar acceso completo
2. Cerrar sesión e ingresar como `empleado` → Verificar restricciones
3. Intentar acceder directamente a URLs restringidas
4. Verificar comportamiento AJAX en lista de clientes
