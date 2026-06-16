# MC-LarenS ERP - API Documentation

## Base URL
```
http://localhost:8001
```

## Authentication
Todos los endpoints requieren autenticación JWT en el header:
```
Authorization: Bearer <token>
```

## Endpoints Principales

### Auth
- `POST /api/v1/auth/login` - Login con PIN y email
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Obtener usuario actual

### Ventas
- `GET /api/v1/ventas` - Listar ventas
- `POST /api/v1/ventas` - Crear venta
- `GET /api/v1/ventas/{id}` - Obtener venta por ID
- `PUT /api/v1/ventas/{id}` - Actualizar venta
- `DELETE /api/v1/ventas/{id}` - Eliminar venta

### Clientes
- `GET /api/v1/clientes` - Listar clientes
- `POST /api/v1/clientes` - Crear cliente
- `GET /api/v1/clientes/{id}` - Obtener cliente por ID
- `PUT /api/v1/clientes/{id}` - Actualizar cliente
- `DELETE /api/v1/clientes/{id}` - Eliminar cliente

### Inventario
- `GET /api/v1/inventario` - Listar productos
- `POST /api/v1/inventario` - Crear producto
- `GET /api/v1/inventario/{id}` - Obtener producto por ID
- `PUT /api/v1/inventario/{id}` - Actualizar producto
- `DELETE /api/v1/inventario/{id}` - Eliminar producto

### Usuarios
- `GET /api/v1/usuarios` - Listar usuarios
- `POST /api/v1/usuarios` - Crear usuario
- `GET /api/v1/usuarios/{id}` - Obtener usuario por ID
- `PUT /api/v1/usuarios/{id}` - Actualizar usuario
- `DELETE /api/v1/usuarios/{id}` - Eliminar usuario

### Reportes
- `GET /api/v1/reportes/ventas` - Reporte de ventas
- `GET /api/v1/reportes/inventario` - Reporte de inventario
- `GET /api/v1/reportes/clientes` - Reporte de clientes

## Documentación Interactiva
Accede a Swagger UI en:
```
http://localhost:8001/docs
```

O ReDoc en:
```
http://localhost:8001/redoc
```

## Ejemplos de Uso

### Login
```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "xinon@local",
    "pin": "0101"
  }'
```

### Listar ventas
```bash
curl -X GET http://localhost:8001/api/v1/ventas \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Crear venta
```bash
curl -X POST http://localhost:8001/api/v1/ventas \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": "123",
    "items": [
      {
        "producto_id": "456",
        "cantidad": 2,
        "precio": 100.00
      }
    ],
    "total": 200.00
  }'
```

## WebSockets

### Conexión
```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onmessage = (event) => {
  console.log('Mensaje recibido:', event.data);
};

ws.send('{"action": "subscribe", "channel": "ventas"}');
```

## Manejo de Errores

Todos los errores retornan JSON con estructura:
```json
{
  "detail": "Descripción del error",
  "status": 400,
  "error_code": "ERROR_CODE"
}
```

### Códigos de Error Comunes
- `401` - No autorizado
- `403` - Prohibido
- `404` - No encontrado
- `422` - Validación fallida
- `500` - Error interno del servidor

## Rate Limiting
- Máximo 100 requests por minuto por IP
- Máximo 1000 requests por hora por usuario

## Versiones API
- `v1` - Versión actual (en uso)

## Changelog

### v1.0.0 (2026-05-15)
- Release inicial
- Endpoints de CRUD básicos
- Autenticación PIN
- Reportes básicos
- WebSocket en tiempo real
