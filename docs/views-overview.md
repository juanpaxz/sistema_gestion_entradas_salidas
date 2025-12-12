# Views Overview — app.control

This document summarizes the views implemented in `app/control/views.py` to provide quick context: responsibilities, inputs/outputs, templates, permissions, edge cases and recommended follow-ups.

---

## General notes
- File: `app/control/views.py`
- Main responsibilities: employee management (CRUD) and attendance (registro, entrada, salida, historial, reportes).
- Uses models: `Empleado`, `Asistencia`.
- Uses forms: `EmpleadoCreationForm`, `EmpleadoForm`.
- Authentication: `@login_required` on protected views; group-based permissions (`administracion`, `empleado`).
- Messaging: uses `django.contrib.messages` for user feedback.

---

## Views (detailed)

### 1) home(request)
- Path: project root includes an app-level route to verify the app responds.
- Returns: simple `HttpResponse` text "Control app: funciona correctamente.".
- Permissions: public.

### 2) listar_empleados(request)
- Purpose: render list of `Empleado` records for admins.
- Template: `control/administracion/listar_empleados.html` (context: `empleados`).
- Permissions: requires logged-in user and group `administracion`; otherwise returns `HttpResponseForbidden`.
- Query: `Empleado.objects.select_related('user').all().order_by('nombre','apellido')`.
- Edge cases: empty queryset handled by template `{% empty %}`.

### 3) dashboard(request)
- Purpose: admin dashboard with simple stats (total empleados, activos).
- Template: `control/administracion/dashboard.html` (context: `total_empleados`, `empleados_activos`).
- Permissions: admin group only.

### 4) crear_empleado(request)
- Purpose: create a new `User` and `Empleado`. Uses `EmpleadoCreationForm`.
- Flow:
  - POST: validate form, `form.save()` creates the `User` (via UserCreationForm logic), then an `Empleado` record is created. If group `empleado` exists, the new user is added to it.
  - On IntegrityError (e.g., duplicate RFC): delete created user, add form error on `rfc`.
  - On unexpected exception: deletes created user and shows an error message.
- Template: `control/administracion/crear_empleado.html` (context: `form`).
- Permissions: admin only.
- Edge cases & notes:
  - If the group `empleado` does not exist, it logs a warning but proceeds.
  - `new_user` is deleted on error to avoid orphan users.

### 5) editar_empleado(request, empleado_id)
- Purpose: update `Empleado` fields via `EmpleadoForm`.
- Template: `control/administracion/editar_empleado.html` (context: `form`, `empleado`).
- Permissions: admin only.
- Flow: if POST and valid -> save and redirect to `control:listar` with success message.

### 6) eliminar_empleado(request, empleado_id)
- Purpose: confirm & delete an employee. On POST, deletes the related `User` (preferred) or `Empleado` fallback, then redirects to `control:listar` with success message.
- Template: `control/administracion/confirm_delete_empleado.html`.
- Permissions: admin only.

### 7) registro_asistencia(request)
- Purpose: show the attendance registration page for the current user.
- Template: `control/asistencias/registro.html` (context: `asistencia`, `empleado`).
- Permissions: currently allows users in either `empleado` or `administracion` groups.
- Behavior: obtains `Empleado` for `request.user` and `get_or_create` today's `Asistencia`.
- Edge case: if no `Empleado` exists for the user -> shows error message and redirects to dashboard.

### 8) registrar_entrada(request)
- Purpose: AJAX/POST endpoint to register an entry.
- Method: expects POST; otherwise returns 405 JSON.
- Flow:
  - Gets `Empleado` for `request.user` (404 JSON if not found).
  - `get_or_create` today's Asistencia.
  - If `hora_entrada` already set -> JSON with error message.
  - Calls `asistencia.registrar_entrada()` (model method expected), computes if `retardo` by comparing with `09:00`, may set `asistencia.tipo='retardo'` and save.
  - Returns JSON success with `hora`.
- Note: no explicit admin allowance here — function relies on `Empleado` lookup; if an admin has no Empleado record, it returns 404 JSON.

### 9) registrar_salida(request)
- Purpose: POST endpoint to register a departure.
- Flow:
  - Gets `Empleado` (404 JSON if not found).
  - Attempts to retrieve today's `Asistencia`. If missing -> JSON error.
  - If no `hora_entrada` yet -> JSON error (must register entry first).
  - If `hora_salida` already present -> JSON error.
  - Calls `asistencia.registrar_salida()` and returns JSON success with `hora`.

### 10) ver_asistencias(request)
- Purpose: show history of attendances.
- Template: `control/asistencias/historial.html` (context: `asistencias`).
- Permissions:
  - If user in `administracion` -> returns all `Asistencia` rows.
  - Else attempts to fetch `Empleado` for the user and returns that employee's Asistencia; if not found -> `HttpResponseForbidden`.

### 11) reporte_asistencias(request)
- Purpose: admin-only page to view filtered attendance reports.
- Template: `control/asistencias/reporte.html` (context: `asistencias`, `empleados`, filter params).
- Permissions: admin only.
- Filtering params supported: `fecha_inicio`, `fecha_fin`, `empleado_id`, `tipo`.

---

## Common patterns & dependencies
- Many views assume a 1:1 relationship between `User` and `Empleado` and do `Empleado.objects.get(user=request.user)`.
- Group-based checks commonly use `user.groups.filter(name='...').exists()`.
- Views mix HTML render endpoints and JSON endpoints (AJAX) for attendance registration.
- Views rely on model methods like `Asistencia.registrar_entrada()` / `registrar_salida()` — inspect `models.py` for exact behavior.

---

## Edge cases and potential issues
1. Administrators without `Empleado` record: `registro_asistencia` now allows admin access, but all attendance endpoints (`registrar_entrada`, `registrar_salida`) expect an `Empleado` object and will return JSON errors or redirect. Decide if admins should have Empleado records or if admins should be allowed to register attendance for others.
2. Concurrency: `get_or_create` for Asistencia is used; consider transaction.atomic or select_for_update if concurrent requests may race.
3. Error handling: `crear_empleado` handles IntegrityError and deletes created `User`, which is good. In a few paths a message is duplicated (there is a stray `messages.success` after error handling — review that block).
4. HTTP methods: `registrar_entrada` strictly requires POST; `registrar_salida` does not check method and will accept GET — consider enforcing POST for symmetry.
5. API responses: `registrar_entrada` and `registrar_salida` return JSON with `status`/`message` strings — consider HTTP status codes and consistent error codes.

---

## Recommended improvements (low-risk, high value)
1. Enforce POST on `registrar_salida` (and possibly other write endpoints) to avoid accidental GET triggers.
2. Normalize permission checks with small helper (e.g. `def is_admin(user): return user.groups.filter(name='administracion').exists()`), or use decorators for group-based access.
3. Add explicit 403/404 JSON codes for `registrar_*` endpoints and use standard status codes (400/403/404/409) where appropriate.
4. Add unit tests:
   - `crear_empleado` happy path and IntegrityError path.
   - `registrar_entrada`/`registrar_salida` for normal, duplicate, missing entry, and permission cases.
   - `ver_asistencias` admin vs empleado.
5. Consider adding an admin interface or form to allow an admin to register attendees on behalf of employees (if desired).
6. Add docstrings for the AJAX endpoints describing request/response JSON structure.

---

## Quick test checklist (manual)
1. Login as admin: visit dashboard, create employee, list employees, edit, delete.
2. Login as employee: open registro_asistencia and call registrar_entrada/registerar_salida flows (use browser devtools or curl with POST).
3. Try registrar_entrada twice to ensure the error is returned.
4. As admin without Empleado: open registro_asistencia to confirm the redirect/behavior; decide desired outcome.

---

If you want, I can also:
- Extract a short OpenAPI-like spec for the attendance JSON endpoints.
- Add unit tests stubs (pytest/django testcases) to the repo.
- Implement stricter method checks and helper decorators for permission checks.

Created by the assistant to help provide context for future edits.
