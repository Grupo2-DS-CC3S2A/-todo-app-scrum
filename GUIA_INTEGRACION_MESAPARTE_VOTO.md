# Guia de integracion: MesaParteReniec + Voto Electronico

Esta version toma como base la estructura de `-todo-app-scrum` y migra la experiencia visual de `MesaParteReniec` a React + TypeScript + Vite, manteniendo FastAPI en backend.

## Cambios principales

1. La ventana inicial ahora es la de Mesa de Partes Virtual.
2. La validacion de ingreso usa `backend/data/validation.db`.
3. La barra de menu interna agrega la pestana `Voto Electronico`.
4. La interfaz de voto conserva el endpoint `POST /api/votar` del proyecto original.
5. La paleta visual se alinea con MesaParteReniec: guinda institucional, blanco, gris y naranja.

## Flujo funcional

1. El ciudadano abre el frontend en `http://localhost:5173`.
2. Ingresa por la pantalla de consulta de tramite.
3. Valida DNI, digito, fecha de emision, CAPTCHA y terminos.
4. El frontend llama a `POST /api/validate`.
5. FastAPI consulta `backend/data/validation.db`.
6. Si los datos coinciden, entra al dashboard de Mesa de Partes.
7. En la barra superior aparece `Voto Electronico`.
8. Al hacer clic, se abre la interfaz de voto.
9. El voto se procesa en `POST /api/votar` y se devuelve el hash SHA-256 con llave genetica.

## Datos de prueba

La base `validation.db` incluida trae el ciudadano original y 20 ciudadanos adicionales de prueba.

Ejemplo 1:

- DNI: `40392536`
- Digito: `1`
- Fecha de emision: `2024-07-25`
- CAPTCHA: `r8nm6`

Ejemplo 2:

- DNI: `81000001`
- Digito: `4`
- Fecha de emision: `2022-01-14`
- CAPTCHA: `r8nm6`

## Ejecutar backend

```powershell
cd backend
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

Probar:

```text
http://localhost:8000/docs
```

## Ejecutar frontend

En otra terminal:

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Abrir:

```text
http://localhost:5173
```

## Commits sugeridos

```bash
git checkout -b integracion-mesaparte-voto
```

### Commit 1

```bash
git add backend/data/validation.db backend/src/config.py backend/src/modelos/ciudadano.py backend/src/repositorios/ciudadano_repo.py backend/src/servicios/ciudadano_service.py backend/src/rutas/validacion.py backend/src/rutas/__init__.py backend/src/main.py
git commit -m "feat: agregar validacion ciudadana con validation.db"
```

### Commit 2

```bash
git add frontend/src/types/ciudadano.ts frontend/src/api/validationApi.ts
git commit -m "feat: conectar frontend con validacion de ciudadano"
```

### Commit 3

```bash
git add frontend/src/App.tsx frontend/src/styles.css frontend/src/main.tsx frontend/index.html
git commit -m "feat: migrar interfaz de Mesa de Partes a React"
```

### Commit 4

```bash
git add frontend/src/components/VotingForm.tsx frontend/src/components/VotingReceipt.tsx frontend/src/api/derivacionApi.ts
git commit -m "feat: integrar voto electronico al menu de Mesa de Partes"
```

### Commit 5

```bash
git add GUIA_INTEGRACION_MESAPARTE_VOTO.md
git commit -m "docs: documentar integracion Mesa de Partes y voto electronico"
```
