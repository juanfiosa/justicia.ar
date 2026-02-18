# ⚡ INICIO RÁPIDO - JUSTICIA.ar

## 🎯 Para empezar en 3 pasos:

### Paso 1: Instalar dependencias
```bash
cd backend
pip install flask flask-cors
```

### Paso 2: Iniciar el servidor
```bash
cd backend
./start.sh
```

O manualmente:
```bash
cd backend
python3 app.py
```

### Paso 3: Abrir el frontend
- Abre el archivo `frontend/index.html` en tu navegador Chrome/Firefox
- O visita directamente si tienes un servidor web local

---

## 🧪 Probar el Sistema

### Caso de Prueba 1: Cobro Simple (Nivel 1)
1. Ve a "Nuevo Caso"
2. Ingresa:
   - **Tipo**: Cobro de Suma de Dinero
   - **Demandado**: Pedro Gómez
   - **Monto**: 150000
   - **Hechos**: Préstamo documentado en pagaré vencido hace 4 meses
   - **Pruebas**: pagaré firmado y certificado
3. Haz clic en "Enviar Caso"
4. Verás que se clasifica como **Nivel 1** (automático)
5. Haz clic en "Generar Decisión"
6. ¡Verás una sentencia completa generada automáticamente!

### Caso de Prueba 2: Accidente (Nivel 2-3)
1. Ve a "Nuevo Caso"
2. Ingresa:
   - **Tipo**: Daños y Perjuicios
   - **Demandado**: María López
   - **Monto**: 450000
   - **Hechos**: Accidente de tránsito en intersección. Hay versiones contradictorias sobre quién tenía prioridad de paso
   - **Pruebas**: Testigos con versiones encontradas, pericial mecánica
3. Verás que se clasifica como **Nivel 2 o 3** (más complejo)

---

## 📊 Explorar el Sistema

- **Lista de Casos**: Ver todos los casos ingresados
- **Estadísticas**: Métricas del sistema
- **Información**: Documentación del modelo de 4 niveles

---

## 🔧 Si algo no funciona:

### El servidor no inicia:
```bash
# Verificar que Flask está instalado
pip install flask flask-cors

# Verificar que la BD existe
cd backend
python3 init_db.py
```

### El frontend no se conecta:
- Verifica que el servidor está corriendo en http://localhost:5000
- Mira la consola del navegador (F12) para errores
- Verifica que no tengas un firewall bloqueando el puerto 5000

### Error de CORS:
- Asegúrate de que Flask-CORS está instalado: `pip install flask-cors`

---

## 📝 Notas Importantes

- **Puerto**: El backend corre en el puerto 5000 por defecto
- **Base de datos**: SQLite en `backend/justicia.db`
- **Logs**: Aparecen en la terminal donde corre el servidor
- **Datos**: Todos los datos son de prueba y pueden eliminarse borrando `justicia.db`

---

## 🎓 Para Aprender Más

1. Lee el `README.md` completo
2. Explora el código en:
   - `backend/clasificador.py` - Lógica de clasificación
   - `backend/motor_decision.py` - Generación de decisiones
   - `backend/app.py` - API endpoints
3. Mira la base de datos:
   ```bash
   sqlite3 backend/justicia.db
   .tables
   SELECT * FROM casos_precedentes;
   ```

---

¡Listo para experimentar! 🚀
