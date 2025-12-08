"""
Utilidades para generar PDFs de pases de entrada/salida
Superpone datos sobre los templates PDF existentes
"""
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.conf import settings
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.utils import timezone
import datetime as _dt
from datetime import datetime, date
import calendar
from reportlab.lib.styles import ParagraphStyle
from .models import Empleado


def generar_pase_pdf(pase):
    """
    Genera un PDF del pase superponiendo los datos sobre el template existente.
    
    Args:
        pase: Instancia del modelo Pase
    
    Returns:
        BytesIO con el PDF generado
    """
    
    # Seleccionar template según tipo de pase
    if pase.tipo == 'salida':
        template_path = os.path.join(settings.MEDIA_ROOT, 'pases_form', 'PASE-DE-SALIDA.pdf')
    else:
        template_path = os.path.join(settings.MEDIA_ROOT, 'pases_form', 'pase-de-entrada.pdf')
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template no encontrado: {template_path}")
    
    # Leer PDF template
    with open(template_path, 'rb') as f:
        reader = PdfReader(f)
        writer = PdfWriter()
        
        # Obtener tamaño real de la primera página
        first_page = reader.pages[0]
        media_box = first_page.mediabox
        page_width = float(media_box.width)
        page_height = float(media_box.height)
        
        # Procesar cada página
        for page_idx, page in enumerate(reader.pages):
            # Crear overlay con reportlab usando el tamaño exacto
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=(page_width, page_height))
            
            # Configurar fuente y tamaño
            can.setFont("Helvetica", 11)
            
            # Preparar datos
            empleado_nombre = f"{pase.empleado.nombre} {pase.empleado.apellido}".upper()
            hora_str = pase.hora.strftime("%H:%M")
            
            meses_es = {
                1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
                5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
                9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
            }
            dia = pase.fecha.day
            mes = meses_es[pase.fecha.month]
            ano = pase.fecha.year
            fecha_str = f"{dia} DE {mes} DE {ano}"
            
            asunto_str = str(pase.asunto).upper()
            observaciones_str = str(pase.observaciones or "NINGUNA").upper()
            
            # Usar porcentajes del tamaño de página para posicionar elementos
            # Esto hace que sea adaptable a cualquier tamaño de PDF
            
            if pase.tipo == 'entrada':
                # FOLIO - sobre la línea en blanco a la derecha de "FOLIO:"
                folio_x = page_width * 0.78
                folio_y = page_height * 0.82
                can.drawString(folio_x, folio_y, str(pase.folio))
                
                # NOMBRE - sobre la línea en blanco después de "NOMBRE:"
                nombre_x = page_width * 0.26
                nombre_y = page_height * 0.808
                can.drawString(nombre_x, nombre_y, empleado_nombre)
                
                # HORA DE ENTRADA - sobre la línea en blanco
                hora_x = page_width * 0.26
                hora_y = page_height * 0.788
                can.drawString(hora_x, hora_y, hora_str)
                
                # FECHA - sobre la línea en blanco lado derecho
                fecha_x = page_width * 0.72
                fecha_y = page_height * 0.788
                can.drawString(fecha_x, fecha_y, fecha_str)
                
                # ASUNTO - sobre la línea en blanco después de "ASUNTO:"
                asunto_x = page_width * 0.26
                asunto_y = page_height * 0.747
                can.drawString(asunto_x, asunto_y, asunto_str)
                
                # OBSERVACIONES - sobre las líneas en blanco
                obs_x = page_width * 0.26
                obs_y = page_height * 0.694
                
                if len(observaciones_str) > 70:
                    lineas = [observaciones_str[i:i+70] for i in range(0, len(observaciones_str), 70)]
                    y_pos = obs_y
                    for linea in lineas[:2]:
                        can.drawString(obs_x, y_pos, linea)
                        y_pos -= page_height * 0.04
                else:
                    can.drawString(obs_x, obs_y, observaciones_str)
                
                # SEGUNDA SECCIÓN (COPIA/TRABAJADOR) - misma página
                # Aplicar offset para la copia en la parte inferior (subir un poco)
                y_offset = page_height * 0.425
                
                # FOLIO - copia
                can.drawString(folio_x, folio_y - y_offset, str(pase.folio))
                
                # NOMBRE - copia
                can.drawString(nombre_x, nombre_y - y_offset, empleado_nombre)
                
                # HORA DE ENTRADA - copia
                can.drawString(hora_x, hora_y - y_offset, hora_str)
                
                # FECHA - copia
                can.drawString(fecha_x, fecha_y - y_offset, fecha_str)
                
                # ASUNTO - copia
                can.drawString(asunto_x, (asunto_y - y_offset) - page_height * 0.01, asunto_str)
                
                # OBSERVACIONES - copia
                obs_y_copy = (obs_y - y_offset) - page_height * 0.01
                if len(observaciones_str) > 70:
                    lineas = [observaciones_str[i:i+70] for i in range(0, len(observaciones_str), 70)]
                    y_pos = obs_y_copy
                    for linea in lineas[:2]:
                        can.drawString(obs_x, y_pos, linea)
                        y_pos -= page_height * 0.04
                else:
                    can.drawString(obs_x, obs_y_copy, observaciones_str)
            
            elif pase.tipo == 'salida':
                # PRIMERA SECCIÓN (ORIGINAL)
                # FOLIO - sobre la línea en blanco a la derecha
                folio_x = page_width * 0.78
                folio_y = page_height * 0.78
                can.drawString(folio_x, folio_y, str(pase.folio))
                
                # NOMBRE - sobre la línea en blanco
                nombre_x = page_width * 0.26
                nombre_y = page_height * 0.762
                can.drawString(nombre_x, nombre_y, empleado_nombre)
                
                # HORA DE SALIDA - sobre la línea en blanco
                hora_x = page_width * 0.26
                hora_y = page_height * 0.748
                can.drawString(hora_x, hora_y, hora_str)
                
                # HORA DE REINCORPORACIÓN (si aplica)
                if pase.hora_reincorporacion:
                    hora_reincorp = pase.hora_reincorporacion.strftime("%H:%M")
                    reincorp_x = page_width * 0.72
                    reincorp_y = page_height * 0.788
                    can.drawString(reincorp_x, reincorp_y, hora_reincorp)
                
                # FECHA - sobre la línea en blanco
                fecha_x = page_width * 0.26
                fecha_y = page_height * 0.65
                can.drawString(fecha_x, fecha_y, fecha_str)
                
                # ASUNTO - sobre la línea en blanco
                asunto_x = page_width * 0.26
                asunto_y = page_height * 0.70
                can.drawString(asunto_x, asunto_y, asunto_str)
                
                # OBSERVACIONES - sobre las líneas en blanco
                obs_x = page_width * 0.26
                obs_y = page_height * 0.67
                
                if len(observaciones_str) > 70:
                    lineas = [observaciones_str[i:i+70] for i in range(0, len(observaciones_str), 70)]
                    y_pos = obs_y
                    for linea in lineas[:2]:
                        can.drawString(obs_x, y_pos, linea)
                        y_pos -= page_height * 0.04
                else:
                    can.drawString(obs_x, obs_y, observaciones_str)
                
                # SEGUNDA SECCIÓN (COPIA/TRABAJADOR)
                if len(reader.pages) == 1:
                    # Si todo está en una página, usar offset vertical muy arriba
                    y_offset = page_height * 0.44
                    
                    # FOLIO - copia
                    can.drawString(folio_x, folio_y - y_offset, str(pase.folio))
                    
                    # NOMBRE - copia
                    can.drawString(nombre_x, nombre_y - y_offset, empleado_nombre)
                    
                    # HORA DE SALIDA - copia (subir 0.3 puntos)
                    can.drawString(hora_x, (hora_y - y_offset) - page_height * 0.006, hora_str)
                    
                    # HORA DE REINCORPORACIÓN - copia
                    if pase.hora_reincorporacion:
                        can.drawString(reincorp_x, reincorp_y - y_offset, hora_reincorp)
                    
                    # FECHA - copia
                    can.drawString(fecha_x, fecha_y - y_offset, fecha_str)
                    
                    # ASUNTO - copia (subir 2 puntos)
                    can.drawString(asunto_x, (asunto_y - y_offset) + page_height * 0.001 , asunto_str)
                    
                    # OBSERVACIONES - copia (subir 0.5 puntos)
                    obs_y_copy = (obs_y - y_offset) - page_height * 0.005
                    if len(observaciones_str) > 70:
                        lineas = [observaciones_str[i:i+70] for i in range(0, len(observaciones_str), 70)]
                        y_pos = obs_y_copy
                        for linea in lineas[:2]:
                            can.drawString(obs_x, y_pos, linea)
                            y_pos -= page_height * 0.04
                    else:
                        can.drawString(obs_x, obs_y_copy, observaciones_str)
            
            # Finalizar canvas
            can.save()
            packet.seek(0)
            
            # Leer el overlay
            overlay_reader = PdfReader(packet)
            overlay_page = overlay_reader.pages[0]
            
            # Combinar páginas
            page.merge_page(overlay_page)
            writer.add_page(page)
        
        # Generar PDF final
        output = BytesIO()
        writer.write(output)
        output.seek(0)
        
        return output


def obtener_templates_disponibles():
    """
    Retorna los templates disponibles en la carpeta pases_form
    """
    templates_path = os.path.join(settings.MEDIA_ROOT, 'pases_form')
    if os.path.exists(templates_path):
        return [f for f in os.listdir(templates_path) if f.endswith('.pdf')]
    return []


def generar_reporte_asistencias_pdf(asistencias_queryset, empleado_id, year, month):
    """Genera el PDF del reporte mensual de asistencias.

    Args:
        asistencias_queryset: QuerySet de Asistencia (filtrado por empleado y rango)
        empleado_id: id del empleado (usado para el filename y lookup)
        year: año (int)
        month: mes (int)

    Returns:
        (BytesIO, filename)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=18, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('ReportTitle', parent=styles['Title'], fontSize=12, leading=14, spaceAfter=6, alignment=1)
    elements = []

    empleado_obj = None
    try:
        empleado_obj = Empleado.objects.get(pk=empleado_id)
        title = f"Reporte mensual - {empleado_obj.nombre} {empleado_obj.apellido} - {year}-{str(month).zfill(2)}"
    except Empleado.DoesNotExist:
        title = f"Reporte mensual - Empleado {empleado_id} - {year}-{str(month).zfill(2)}"

    # Calcular primer y último día del mes para mostrarlos en el encabezado
    try:
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        period_text = f"Periodo: {first_day.strftime('%d/%m/%Y')} - {last_day.strftime('%d/%m/%Y')}"
    except Exception:
        period_text = ''

    period_style = ParagraphStyle('Period', parent=styles['Normal'], fontSize=9, leading=11, alignment=1, spaceAfter=2)
    if period_text:
        elements.append(Paragraph(period_text, period_style))
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 6))

    data = [["Fecha", "Entrada", "Salida", "Tiempo", "Tipo", "Diferencia(min)"]]

    def _format_time_12(t):
        if not t:
            return '-'
        if isinstance(t, _dt.time):
            return t.strftime('%I:%M %p')
        try:
            return timezone.localtime(t).strftime('%I:%M %p')
        except Exception:
            try:
                return str(t)
            except Exception:
                return '-'

    def _compute_entrada_salida_diff(entrada, salida, fecha_obj):
        if not entrada or not salida:
            return '-'
        try:
            if isinstance(entrada, _dt.time):
                dt_entrada = datetime.combine(fecha_obj, entrada)
            else:
                dt_entrada = timezone.localtime(entrada)

            if isinstance(salida, _dt.time):
                dt_salida = datetime.combine(fecha_obj, salida)
            else:
                dt_salida = timezone.localtime(salida)

            if dt_salida < dt_entrada:
                dt_salida = dt_salida + _dt.timedelta(days=1)

            diff = dt_salida - dt_entrada
            total_seconds = int(diff.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours:02d}:{minutes:02d}"
        except Exception:
            return '-'

    # Construir un mapeo fecha -> asistencia para acceder O(1) por día
    asistencias_list = list(asistencias_queryset)
    asist_map = {a.fecha: a for a in asistencias_list}

    # Iterar todos los días del mes y rellenar fila aunque no exista asistencia
    num_days = (last_day - first_day).days + 1
    for i in range(num_days):
        dia = first_day + _dt.timedelta(days=i)
        a = asist_map.get(dia)
        fecha_str = dia.strftime('%d/%m/%Y')

        if a:
            entrada = a.hora_entrada.strftime('%H:%M') if a.hora_entrada else '-'
            salida = _format_time_12(a.hora_salida)
            try:
                dif = a.compute_diferencia_minutes()
            except Exception:
                dif = None
            dif_str = str(dif) if dif is not None else '-'
            Tiempo = _compute_entrada_salida_diff(a.hora_entrada, a.hora_salida, a.fecha)
            tipo_str = a.tipo.title()
        else:
            entrada = '-'
            salida = '-'
            Tiempo = '-'
            dif_str = '-'
            tipo_str = '-'

        data.append([fecha_str, entrada, salida, Tiempo, tipo_str, dif_str])

    table = Table(data, colWidths=[64, 72, 90, 64, 64, 64])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    filename = f"reporte_asistencias_{empleado_id}_{year}_{str(month).zfill(2)}.pdf"
    return buffer, filename
