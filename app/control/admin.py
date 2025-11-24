from django.contrib import admin
from .models import Empleado, Asistencia, Justificante, Horario, SystemConfig


@admin.register(Justificante)
class JustificanteAdmin(admin.ModelAdmin):
	list_display = ('id', 'empleado_nombre', 'asistencia_info', 'fecha_envio', 'estado_badge', 'ver_pdf')
	list_filter = ('estado', 'fecha_envio', 'empleado')
	search_fields = ('empleado__nombre', 'empleado__apellido', 'asistencia__fecha')
	actions = ['marcar_aprobado', 'marcar_rechazado']
	readonly_fields = ('empleado', 'asistencia', 'fecha_envio', 'ruta_archivo', 'archivo_url', 'pdf_link')
	fieldsets = (
		('Información del Justificante', {
			'fields': ('empleado', 'asistencia', 'fecha_envio', 'motivo')
		}),
		('Archivo', {
			'fields': ('ruta_archivo', 'archivo_url', 'pdf_link')
		}),
		('Validación', {
			'fields': ('estado', 'observacion')
		}),
	)

	def empleado_nombre(self, obj):
		return f"{obj.empleado.nombre} {obj.empleado.apellido}"
	empleado_nombre.short_description = 'Empleado'

	def asistencia_info(self, obj):
		return f"{obj.asistencia.fecha} ({obj.asistencia.tipo})"
	asistencia_info.short_description = 'Asistencia (Fecha/Tipo)'

	def estado_badge(self, obj):
		colors = {
			'pendiente': '#FFC107',
			'aprobado': '#28A745',
			'rechazado': '#DC3545'
		}
		color = colors.get(obj.estado, '#6C757D')
		return f'<span style="background-color:{color}; color:white; padding:3px 10px; border-radius:3px;">{obj.get_estado_display()}</span>'
	estado_badge.short_description = 'Estado'
	estado_badge.allow_tags = True

	def ver_pdf(self, obj):
		if obj.ruta_archivo:
			return f'<a href="{obj.ruta_archivo.url}" target="_blank">📄 Ver PDF</a>'
		return '-'
	ver_pdf.short_description = 'PDF'
	ver_pdf.allow_tags = True

	def pdf_link(self, obj):
		"""Mostrar enlace del PDF en la vista detallada"""
		if obj.ruta_archivo:
			return f'<a href="{obj.ruta_archivo.url}" target="_blank">📥 Descargar PDF</a>'
		return 'No hay archivo'
	pdf_link.short_description = 'Descargar Documento'
	pdf_link.allow_tags = True

	def marcar_aprobado(self, request, queryset):
		# Iterar y guardar para que se disparen señales y hooks relacionados
		for justificante in queryset:
			justificante.estado = 'aprobado'
			justificante.observacion = 'Aprobado por administrador'
			justificante.save()
		self.message_user(request, f'{queryset.count()} justificante(s) marcado(s) como aprobado(s).')
	marcar_aprobado.short_description = '✓ Marcar seleccionados como Aprobado'

	def marcar_rechazado(self, request, queryset):
		for justificante in queryset:
			justificante.estado = 'rechazado'
			justificante.save()
		self.message_user(request, f'{queryset.count()} justificante(s) marcado(s) como rechazado(s).', level='warning')
	marcar_rechazado.short_description = '✗ Marcar seleccionados como Rechazado'


admin.site.register(Empleado)
admin.site.register(Asistencia)
admin.site.register(Horario)
@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
	list_display = ('retardo_minutos',)
	fields = ('retardo_minutos',)
	# evitar añadir múltiples configuraciones desde admin: mostrar aviso asumiendo solo una fila
	def has_add_permission(self, request):
		# permitir añadir solamente si no existe ninguna
		return SystemConfig.objects.count() == 0
