from datetime import date
import base64
import json
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.db.models import Count, Sum, Avg, Q
from django.contrib import messages
from django.db import IntegrityError
from django.urls import reverse
from urllib.parse import urlencode
from collections import Counter, defaultdict
from uuid import uuid4
from .models import (
    Administrador,
    Cliente,
    Disgusto,
    Foto,
    Gusto,
    Match,
    Mensaje,
    Notificacion,
    Usuario,
)


# =========================================================================
# 1. INICIO USUARIO: Sincronizado con los 5 Pilares del Radar de Afinidad
# =========================================================================
def inicioU(request):
    """USUARIO: Tarjetas de preferencia sincronizadas con los 5 pilares"""
    secciones = [
        {
            'id': 'valores',
            'titulo': 'Valores',
            'titulo_card': 'Conexión por Valores',
            'activo': True,
            'nombre': 'Elena',
            'edad': 26,
            'foto': 'usuario/img/elena.jpg',
            'items': ['Honestidad y transparencia', 'Empatía activa', 'Comunicación asertiva'],
            'bio': 'Busco a alguien con quien construir confianza real y conversar sin filtros.',
            'porcentaje': '95%',
            'metrica': 'Afinidad<br>en valores',
        },
        {
            'id': 'hobbies',
            'titulo': 'Hobbies',
            'titulo_card': 'Conexión por Hobbies',
            'activo': False,
            'nombre': 'Camila',
            'edad': 25,
            'foto': 'usuario/img/camila.jpg',
            'items': ['Escalar en boulder', 'Fotografía analógica', 'Dibujar e ilustrar'],
            'bio': 'Los fines de semana me encuentras en el muro o buscando rincones para sacar fotos.',
            'porcentaje': '88%',
            'metrica': 'Afinidad<br>en hobbies',
        },
        {
            'id': 'dinamica',
            'titulo': 'Dinámica Social',
            'titulo_card': 'Conexión por Dinámica Social',
            'activo': False,
            'nombre': 'Sofía',
            'edad': 24,
            'foto': 'usuario/img/elena.jpg',
            'items': ['Café de especialidad de sobremesa', 'Planes al aire libre', 'Juntadas íntimas en casa'],
            'bio': 'Prefiero una buena charla en una cafetería tranquila antes que el ruido de una disco.',
            'porcentaje': '82%',
            'metrica': 'Afinidad<br>social',
        },
        {
            'id': 'amor',
            'titulo': 'Lenguaje del Amor',
            'titulo_card': 'Conexión por Lenguaje del Amor',
            'activo': False,
            'nombre': 'Valentina',
            'edad': 23,
            'foto': 'usuario/img/camila.jpg',
            'items': ['Tiempo de calidad juntos', 'Palabras de afirmación', 'Detalles significativos'],
            'bio': 'Valoro muchísimo la presencia real, dejar el celular de lado y disfrutar el momento.',
            'porcentaje': '90%',
            'metrica': 'Afinidad<br>afectiva',
        },
        {
            'id': 'metas',
            'titulo': 'Metas & Futuro',
            'titulo_card': 'Conexión por Metas & Futuro',
            'activo': False,
            'nombre': 'Martina',
            'edad': 27,
            'foto': 'usuario/img/elena.jpg',
            'items': ['Crecimiento profesional constante', 'Relación estable', 'Viajar y conocer el mundo'],
            'bio': 'Enfocada en mis proyectos, pero con ganas de compartir el camino con alguien afín.',
            'porcentaje': '86%',
            'metrica': 'Afinidad<br>a futuro',
        },
    ]
    return render(request, 'usuario/inicioU.html', {'secciones': secciones})


# =========================================================================
# 2. BUSCADOR USUARIO: Filtrado en tiempo real desde AWS RDS
# =========================================================================
def buscadorU(request):
    query = request.GET.get('q', '').strip()
    categoria_filtro = request.GET.get('cat', '').strip()
    hoy = date.today()

    clientes_qs = Cliente.objects.select_related('usuario_rut').exclude(idcliente='CLI-001')

    if query:
        ruts_con_gusto = Gusto.objects.filter(
            Q(descripcion__icontains=query) | Q(categoria__icontains=query)
        ).values_list('rut', flat=True)

        clientes_qs = clientes_qs.filter(
            Q(usuario_rut__nombre__icontains=query) |
            Q(ocupacionlaboral__icontains=query) |
            Q(nacionalidad__icontains=query) |
            Q(biografia__icontains=query) |
            Q(usuario_rut__rut__in=ruts_con_gusto)
        )

    if categoria_filtro:
        ruts_cat = Gusto.objects.filter(categoria__icontains=categoria_filtro).values_list('rut', flat=True)
        clientes_qs = clientes_qs.filter(usuario_rut__rut__in=ruts_cat)

    resultados = []
    fotos_demo = ['usuario/img/camila.jpg', 'usuario/img/elena.jpg']

    for idx, cli in enumerate(clientes_qs[:15]):
        u = cli.usuario_rut
        edad = hoy.year - cli.fechanacimiento.year - ((hoy.month, hoy.day) < (cli.fechanacimiento.month, cli.fechanacimiento.day)) if cli.fechanacimiento else 24

        gustos_usr = Gusto.objects.filter(rut=u.rut)
        tags = list(gustos_usr.values_list('descripcion', flat=True)[:4])
        valores_num = [int(g.valor) for g in gustos_usr if str(g.valor).isdigit()]
        afinidad = round(sum(valores_num) / len(valores_num)) if valores_num else 88

        resultados.append({
            'rut': u.rut,
            'nombre': u.nombre,
            'apellido': u.apellidopaterno,
            'edad': edad,
            'profesion': cli.ocupacionlaboral or 'Profesional',
            'nacionalidad': cli.nacionalidad or 'Chilena',
            'biografia': cli.biografia,
            'afinidad': afinidad,
            'tags': tags if tags else ['Honestidad', 'Planes al aire libre', 'Viajes'],
            'foto': fotos_demo[idx % len(fotos_demo)],
        })

    resultados.sort(key=lambda x: x['afinidad'], reverse=True)

    context = {
        'resultados': resultados,
        'query': query,
        'categoria_filtro': categoria_filtro,
        'total_resultados': len(resultados),
    }
    return render(request, 'usuario/buscadorU.html', context)


# =========================================================================
# 3. MENSAJES USUARIO: Conversaciones y envío en vivo con AWS RDS
# =========================================================================
def mensajesU(request):
    hoy = date.today()
    usuario_principal = Usuario.objects.filter(nombre='Javier').first() or Usuario.objects.first()
    rut_actual = usuario_principal.rut if usuario_principal else ''

    if request.method == 'POST':
        receptor_rut = request.POST.get('receptor_rut', '').strip()
        texto_msg = request.POST.get('contenido', '').strip()
        if receptor_rut and texto_msg and rut_actual:
            nuevo_id = f"MSG-{Mensaje.objects.count() + 101:04d}"
            Mensaje.objects.create(
                idmensaje=nuevo_id,
                rut1=rut_actual,
                rut2=receptor_rut,
                contenido=texto_msg[:200],
                fechaenvio=hoy,
                leido=0
            )
            cache.delete(f'chat_historial_{rut_actual}_{receptor_rut}')
            cache.delete('graficosU_full_context_v5')
            return redirect(f"/usuario/mensajes/?chat={receptor_rut}")

    cache_key_contactos = f'contactos_usuario_{rut_actual}'
    contactos = cache.get(cache_key_contactos)

    if not contactos:
        msgs_involucrados = Mensaje.objects.filter(Q(rut1=rut_actual) | Q(rut2=rut_actual)).values_list('rut1', 'rut2')
        ruts_conversacion = []
        for r1, r2 in msgs_involucrados:
            otro = r2 if r1 == rut_actual else r1
            if otro and otro != rut_actual and otro not in ruts_conversacion:
                ruts_conversacion.append(otro)

        if not ruts_conversacion:
            matches_usr = Match.objects.filter(Q(cliente1rut=rut_actual) | Q(cliente2rut=rut_actual), estado=1)[:5]
            for mt in matches_usr:
                otro = mt.cliente2rut if mt.cliente1rut == rut_actual else mt.cliente1rut
                if otro and otro != rut_actual and otro not in ruts_conversacion:
                    ruts_conversacion.append(otro)

        fotos_demo = ['usuario/img/elena.jpg', 'usuario/img/camila.jpg']
        contactos = []
        for idx, r_otro in enumerate(ruts_conversacion[:6]):
            u_otro = Usuario.objects.filter(rut=r_otro).first()
            if not u_otro:
                continue
            cli_otro = Cliente.objects.filter(usuario_rut=u_otro).first()
            edad = hoy.year - cli_otro.fechanacimiento.year if (cli_otro and cli_otro.fechanacimiento) else 25

            contactos.append({
                'rut': r_otro,
                'nombre': u_otro.nombre,
                'edad': edad,
                'profesion': cli_otro.ocupacionlaboral if cli_otro else 'Profesional',
                'ultimo_mensaje': 'Conversación activa',
                'fecha': 'Hoy',
                'activo': False,
                'afinidad': 91,
                'foto': fotos_demo[idx % len(fotos_demo)],
            })
        cache.set(cache_key_contactos, contactos, 3600)

    chat_seleccionado_rut = request.GET.get('chat', contactos[0]['rut'] if contactos else '')

    contacto_activo = None
    for c in contactos:
        c['activo'] = (c['rut'] == chat_seleccionado_rut)
        if c['activo']:
            contacto_activo = c

    cache_key_historial = f'chat_historial_{rut_actual}_{chat_seleccionado_rut}'
    historial = cache.get(cache_key_historial)

    if not historial and chat_seleccionado_rut:
        mensajes_chat = Mensaje.objects.filter(
            Q(rut1=rut_actual, rut2=chat_seleccionado_rut) |
            Q(rut1=chat_seleccionado_rut, rut2=rut_actual)
        ).order_by('fechaenvio', 'idmensaje')[:30]

        historial = []
        for m in mensajes_chat:
            historial.append({
                'contenido': m.contenido,
                'fecha': m.fechaenvio.strftime('%d %b') if m.fechaenvio else 'Hoy',
                'es_mio': (m.rut1 == rut_actual),
            })
        cache.set(cache_key_historial, historial, 3600)

    context = {
        'contactos': contactos,
        'contacto_activo': contacto_activo,
        'historial': historial or [],
        'total_chats': len(contactos),
    }
    return render(request, 'usuario/mensajesU.html', context)


# =========================================================================
# 4. NOTIFICACIONES USUARIO: Conectado a tabla NOTIFICACION en AWS RDS
# =========================================================================
def notificacionesU(request):
    notificaciones_db = Notificacion.objects.all().order_by('-fecha', '-idnotificacion')[:20]

    lista_notificaciones = []
    no_leidas = 0

    for n in notificaciones_db:
        es_no_leida = (n.estado == 0)
        if es_no_leida:
            no_leidas += 1

        info_lower = n.informacion.lower()
        if 'match' in info_lower or 'afinidad' in info_lower or 'conexión' in info_lower:
            tipo = 'match'
            icono = 'bi-heart-fill'
            titulo = '¡Nueva Sintonía Alcanzada!'
        elif 'mensaje' in info_lower or 'chat' in info_lower:
            tipo = 'chat'
            icono = 'bi-chat-quote-fill'
            titulo = 'Nuevo Mensaje Recibido'
        else:
            tipo = 'system'
            icono = 'bi-shield-check'
            titulo = 'Actualización de Beyond Date'

        lista_notificaciones.append({
            'id': n.idnotificacion,
            'titulo': titulo,
            'informacion': n.informacion,
            'fecha': n.fecha.strftime('%d/%m/%Y') if n.fecha else 'Reciente',
            'unread': es_no_leida,
            'tipo': tipo,
            'icono': icono,
        })

    context = {
        'notificaciones': lista_notificaciones,
        'total_notificaciones': len(lista_notificaciones),
        'no_leidas': no_leidas,
    }
    return render(request, 'usuario/notificacionesU.html', context)


# =========================================================================
# 5. EDITAR PERFIL Y PERFIL USUARIO
# =========================================================================
def editar_perfilU(request):
    hoy = date.today()
    cliente_principal = Cliente.objects.select_related('usuario_rut').filter(idcliente='CLI-001').first()
    if not cliente_principal:
        cliente_principal = Cliente.objects.select_related('usuario_rut').first()
    usuario_principal = cliente_principal.usuario_rut if cliente_principal else Usuario.objects.first()
    rut_actual = usuario_principal.rut if usuario_principal else ''

    edad_actual = 21
    if cliente_principal and cliente_principal.fechanacimiento:
        fn = cliente_principal.fechanacimiento
        edad_actual = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))

    fotos_guardadas = cache.get(f'fotos_galeria_{rut_actual}')
    if fotos_guardadas is None:
        fotos_guardadas = ['/static/usuario/img/javier.jpg']

    if request.method == 'POST':
        nuevo_nombre = request.POST.get('nombre', '').strip()
        nueva_edad = request.POST.get('edad', '').strip()
        nueva_bio = request.POST.get('biografia', '').strip()
        nueva_ocupacion = request.POST.get('ocupacionlaboral', '').strip()
        nueva_nacionalidad = request.POST.get('nacionalidad', '').strip()
        nueva_orientacion = request.POST.get('orientacionsexual', '').strip()

        if usuario_principal and nuevo_nombre:
            usuario_principal.nombre = nuevo_nombre
            usuario_principal.save()

        if cliente_principal:
            cliente_principal.biografia = nueva_bio[:200]
            cliente_principal.ocupacionlaboral = nueva_ocupacion
            cliente_principal.nacionalidad = nueva_nacionalidad
            cliente_principal.orientacionsexual = nueva_orientacion

            if nueva_edad.isdigit():
                edad_int = max(18, min(99, int(nueva_edad)))
                cliente_principal.fechanacimiento = date(hoy.year - edad_int, 1, 1)

            cliente_principal.save()

        intereses_finales = request.POST.getlist('intereses_lista')
        if rut_actual:
            Gusto.objects.filter(rut=rut_actual).exclude(descripcion__in=intereses_finales).delete()
            existentes = set(Gusto.objects.filter(rut=rut_actual).values_list('descripcion', flat=True))

            for idx, desc in enumerate(intereses_finales):
                desc_limpia = desc.strip()
                if desc_limpia and desc_limpia not in existentes:
                    nuevo_id = f"GUS-{rut_actual[:4]}-{Gusto.objects.count() + idx + 100}"[:20]
                    Gusto.objects.create(
                        pk=nuevo_id,
                        categoria='Hobbies',
                        valor='90',
                        descripcion=desc_limpia[:100],
                        rut=rut_actual
                    )

        fotos_conservadas = request.POST.getlist('fotos_actuales')
        archivos_nuevos = request.FILES.getlist('nuevas_fotos')

        for archivo in archivos_nuevos:
            if len(fotos_conservadas) < 6:
                encoded = base64.b64encode(archivo.read()).decode('utf-8')
                mime = archivo.content_type or 'image/jpeg'
                fotos_conservadas.append(f"data:{mime};base64,{encoded}")

        if not fotos_conservadas:
            fotos_conservadas = ['/static/usuario/img/javier.jpg']

        cache.set(f'fotos_galeria_{rut_actual}', fotos_conservadas[:6], 86400)
        cache.delete(f'contactos_usuario_{rut_actual}')
        cache.delete('graficosU_full_context_v5')
        return redirect('perfilU')

    gustos_usr = Gusto.objects.filter(rut=rut_actual) if rut_actual else []

    context = {
        'usuario': usuario_principal,
        'cliente': cliente_principal,
        'edad': edad_actual,
        'gustos': gustos_usr,
        'fotos': fotos_guardadas,
    }
    return render(request, 'usuario/editar_perfilU.html', context)


def perfilU(request):
    hoy = date.today()
    cliente_principal = Cliente.objects.select_related('usuario_rut').filter(idcliente='CLI-001').first()
    if not cliente_principal:
        cliente_principal = Cliente.objects.select_related('usuario_rut').first()

    usuario_principal = cliente_principal.usuario_rut if cliente_principal else Usuario.objects.first()
    rut_actual = usuario_principal.rut if usuario_principal else ''

    edad = 21
    if cliente_principal and cliente_principal.fechanacimiento:
        fn = cliente_principal.fechanacimiento
        edad = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))

    gustos_usr = Gusto.objects.filter(rut=rut_actual) if rut_actual else []

    fotos_guardadas = cache.get(f'fotos_galeria_{rut_actual}')
    if fotos_guardadas is None:
        fotos_guardadas = ['/static/usuario/img/javier.jpg']
        cache.set(f'fotos_galeria_{rut_actual}', fotos_guardadas, 86400)

    slots_vacios = range(max(0, 6 - len(fotos_guardadas)))

    context = {
        'usuario': usuario_principal,
        'cliente': cliente_principal,
        'edad': edad,
        'gustos': gustos_usr,
        'fotos': fotos_guardadas,
        'total_fotos': len(fotos_guardadas),
        'slots_vacios': slots_vacios,
    }
    return render(request, 'usuario/perfilU.html', context)


# =========================================================================
# 6. ESTADÍSTICAS Y GRÁFICOS USUARIO (DRILL-DOWN EN DONA, RADAR Y TIEMPO)
# =========================================================================
def graficosU(request):
    hoy = date.today()
    perfil_mock = {
        'nombre': 'Javier',
        'edad': 21,
    }

    cached_context = cache.get('graficosU_full_context_v5')
    if cached_context:
        return render(request, 'usuario/graficosU.html', cached_context)

    # 1. BALANCE DE MATCHES + DRILL-DOWN DE INTERACCIÓN
    total_matches = Match.objects.count()
    matches_reales = Match.objects.filter(estado=1).count()
    no_matches_reales = Match.objects.filter(estado=0).count()
    porcentaje_matches = round((matches_reales / total_matches) * 100, 1) if total_matches > 0 else 0.0

    chart_payload = {
        'labels': ['Match', 'No Match'],
        'data': [matches_reales, no_matches_reales],
        'porcentaje': porcentaje_matches,
    }

    usuarios_dict = {u.rut: u for u in Usuario.objects.all()}
    clientes_dict = {c.usuario_rut.rut: c for c in Cliente.objects.select_related('usuario_rut').all()}

    gustos_all = list(Gusto.objects.all())
    disgustos_all = list(Disgusto.objects.all())
    mensajes_all = list(Mensaje.objects.all().order_by('-fechaenvio', '-idmensaje')[:120])
    notificaciones_all = list(Notificacion.objects.all().order_by('-fecha', '-idnotificacion')[:30])

    gustos_por_rut = {}
    for g in gustos_all:
        gustos_por_rut.setdefault(g.rut, []).append({
            'pk': str(g.pk),
            'categoria': g.categoria or 'Hobbies',
            'valor': int(g.valor) if str(g.valor).isdigit() else 85,
            'descripcion': g.descripcion,
        })

    disgustos_por_rut = {}
    for d in disgustos_all:
        disgustos_por_rut.setdefault(d.rut, []).append({
            'pk': str(d.pk),
            'categoria': d.categoria or 'Valores',
            'valor': int(d.valor) if str(d.valor).isdigit() else 40,
            'descripcion': d.descripcion,
        })

    def construir_lista_drilldown(estado_filtro):
        qs = Match.objects.filter(estado=estado_filtro).order_by('-fechamatch', '-idmatch')[:12]
        lista = []
        ruts_vistos = set()

        for m in qs:
            rut_persona = m.cliente2rut if m.cliente2rut != '18012345-1' else m.cliente1rut
            if not rut_persona or rut_persona in ruts_vistos:
                continue
            ruts_vistos.add(rut_persona)

            u_obj = usuarios_dict.get(rut_persona)
            c_obj = clientes_dict.get(rut_persona)
            if not u_obj:
                continue

            edad_p = 23
            if c_obj and c_obj.fechanacimiento:
                fn = c_obj.fechanacimiento
                edad_p = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))

            gustos_p = gustos_por_rut.get(rut_persona, [])
            disgustos_p = disgustos_por_rut.get(rut_persona, [])

            msgs_persona = [
                {
                    'idmensaje': msg.idmensaje,
                    'fecha': msg.fechaenvio.strftime('%d/%m/%Y') if msg.fechaenvio else 'Reciente',
                    'contenido': msg.contenido,
                    'direccion': 'Enviado' if msg.rut1 == '18012345-1' else 'Recibido',
                }
                for msg in mensajes_all
                if msg.rut1 == rut_persona or msg.rut2 == rut_persona
            ][:8]

            enviados_count = sum(1 for m_it in msgs_persona if m_it['direccion'] == 'Enviado')
            recibidos_count = sum(1 for m_it in msgs_persona if m_it['direccion'] == 'Recibido')

            interaccion_labels = [
                'Gustos que comparten',
                'Límites que coinciden',
                'Mensajes enviados',
                'Mensajes recibidos'
            ]
            interaccion_data = [
                len(gustos_p) if gustos_p else 3,
                len(disgustos_p) if disgustos_p else 2,
                enviados_count if enviados_count else 2,
                recibidos_count if recibidos_count else 3,
            ]

            vals_totales = [item['valor'] for item in gustos_p]
            afinidad_gral = round(sum(vals_totales) / len(vals_totales)) if vals_totales else 88

            lista.append({
                'idmatch': m.idmatch,
                'fechamatch': m.fechamatch.strftime('%d/%m/%Y') if m.fechamatch else 'Última semana',
                'rut': rut_persona,
                'idcliente': c_obj.idcliente if c_obj else 'CLI-N/A',
                'nombre': f"{u_obj.nombre} {u_obj.apellidopaterno or ''}".strip(),
                'edad': edad_p,
                'ocupacion': c_obj.ocupacionlaboral if (c_obj and c_obj.ocupacionlaboral) else 'Profesional',
                'nacionalidad': c_obj.nacionalidad if (c_obj and c_obj.nacionalidad) else 'Chilena',
                'orientacion': c_obj.orientacionsexual if (c_obj and c_obj.orientacionsexual) else 'Heterosexual',
                'biografia': c_obj.biografia if (c_obj and c_obj.biografia) else 'Sin biografía registrada.',
                'afinidad_general': afinidad_gral,
                'interaccion_labels': interaccion_labels,
                'interaccion_data': interaccion_data,
                'gustos': gustos_p[:8],
                'disgustos': disgustos_p[:6],
                'mensajes': msgs_persona,
            })
        return lista

    drilldown_payload = {
        'match': construir_lista_drilldown(1),
        'no_match': construir_lista_drilldown(0),
    }

    # 2. CARACTERÍSTICAS DE MATCHES
    matches_exitosos = Match.objects.filter(estado=1)
    ruts_con_match = set(matches_exitosos.values_list('cliente2rut', flat=True)) | set(matches_exitosos.values_list('cliente1rut', flat=True))

    clientes_match_qs = Cliente.objects.filter(usuario_rut__rut__in=ruts_con_match)
    if not clientes_match_qs.exists():
        clientes_match_qs = Cliente.objects.all()

    orientacion_qs = clientes_match_qs.values('orientacionsexual').annotate(total=Count('idcliente')).order_by('-total')
    orientacion_labels = [item['orientacionsexual'] for item in orientacion_qs if item['orientacionsexual']]
    orientacion_data = [item['total'] for item in orientacion_qs if item['orientacionsexual']]

    rangos_edad = {'18-21 años': 0, '22-25 años': 0, '26-29 años': 0, '30+ años': 0}
    for cli in clientes_match_qs:
        if cli.fechanacimiento:
            edad = hoy.year - cli.fechanacimiento.year - ((hoy.month, hoy.day) < (cli.fechanacimiento.month, cli.fechanacimiento.day))
            if edad <= 21:
                rangos_edad['18-21 años'] += 1
            elif edad <= 25:
                rangos_edad['22-25 años'] += 1
            elif edad <= 29:
                rangos_edad['26-29 años'] += 1
            else:
                rangos_edad['30+ años'] += 1

    profesion_qs = clientes_match_qs.values('ocupacionlaboral').annotate(total=Count('idcliente')).order_by('-total')
    profesion_labels = [item['ocupacionlaboral'] for item in profesion_qs if item['ocupacionlaboral']]
    profesion_data = [item['total'] for item in profesion_qs if item['ocupacionlaboral']]

    nacionalidad_qs = clientes_match_qs.values('nacionalidad').annotate(total=Count('idcliente')).order_by('-total')
    nacionalidad_labels = [item['nacionalidad'] for item in nacionalidad_qs if item['nacionalidad']]
    nacionalidad_data = [item['total'] for item in nacionalidad_qs if item['nacionalidad']]

    arquetipo_payload = {
        'orientacion': {
            'labels': orientacion_labels or ['Sin datos'],
            'data': orientacion_data or [0],
            'label': 'Matches por orientación'
        },
        'edad': {
            'labels': list(rangos_edad.keys()),
            'data': list(rangos_edad.values()),
            'label': 'Matches por rango de edad'
        },
        'profesion': {
            'labels': profesion_labels or ['Sin datos'],
            'data': profesion_data or [0],
            'label': 'Matches por área profesional'
        },
        'nacionalidad': {
            'labels': nacionalidad_labels or ['Sin datos'],
            'data': nacionalidad_data or [0],
            'label': 'Matches por nacionalidad'
        },
        'religion': {
            'labels': ['Agnóstico/Ateo', 'Católico', 'Cristiano', 'Espiritual', 'Otro'],
            'data': [12, 8, 4, 3, 2],
            'label': 'Matches por creencias'
        }
    }

    # 3. RADAR DE AFINIDAD + DRILL-DOWN POR SUBCATEGORÍAS
    categorias_radar = [
        'Valores',
        'Hobbies',
        'Dinámica Social',
        'Lenguaje del Amor',
        'Metas & Futuro'
    ]

    mapa_subcategorias = {
        'Valores': [
            ('Ética y Confianza', ['honestidad', 'transparencia', 'lealtad', 'compromiso', 'sinceridad', 'verdad']),
            ('Vínculo Emocional', ['empatía', 'empatia', 'comunicación', 'comunicacion', 'asertiva', 'escucha', 'apoyo']),
            ('Respeto y Libertad', ['respeto', 'tolerancia', 'autonomía', 'igualdad', 'humildad', 'justicia']),
        ],
        'Hobbies': [
            ('Arte y Creatividad', ['fotografía', 'fotografia', 'dibujar', 'ilustrar', 'pintar', 'arte', 'música', 'musica', 'diseño']),
            ('Deporte y Aventura', ['escalar', 'boulder', 'deporte', 'correr', 'trekking', 'patinar', 'skate', 'naturaleza', 'bici']),
            ('Cultura y Entretenimiento', ['leer', 'ciencia ficción', 'cine', 'series', 'videojuegos', 'cocinar', 'libros']),
        ],
        'Dinámica Social': [
            ('Planes Tranquilos', ['café', 'cafe', 'sobremesa', 'casa', 'íntimas', 'intimas', 'tranquila', 'conversar']),
            ('Vida al Aire Libre', ['aire libre', 'parque', 'paseo', 'escapada', 'playa', 'montaña', 'picnic']),
            ('Eventos y Vida Social', ['conciertos', 'eventos', 'amigos', 'fiesta', 'bares', 'reuniones', 'salir']),
        ],
        'Lenguaje del Amor': [
            ('Presencia y Atención', ['tiempo de calidad', 'presencia', 'juntos', 'atención', 'momento', 'escuchar']),
            ('Expresión y Afecto', ['palabras', 'afirmación', 'contacto', 'físico', 'abrazos', 'cariño', 'afecto']),
            ('Detalles y Gestos', ['detalles', 'significativos', 'actos', 'servicio', 'regalos', 'sorpresas', 'cuidar']),
        ],
        'Metas & Futuro': [
            ('Desarrollo y Estabilidad', ['profesional', 'crecimiento', 'financiera', 'estabilidad', 'independencia', 'carrera', 'estudio']),
            ('Proyecto de Pareja', ['relación', 'estable', 'pareja', 'familia', 'hogar', 'futuro', 'compartir']),
            ('Estilo de Vida y Viajes', ['viajar', 'mundo', 'conocer', 'aventuras', 'mudarse', 'experiencias', 'mascotas']),
        ],
    }

    def clasificar_en_subcategoria(pilar, descripcion_texto):
        reglas = mapa_subcategorias.get(pilar, [])
        desc_low = (descripcion_texto or '').lower()
        for nombre_sub, keywords in reglas:
            if any(k in desc_low for k in keywords):
                return nombre_sub
        if reglas:
            idx = sum(ord(c) for c in desc_low) % len(reglas)
            return reglas[idx][0]
        return 'General'

    def construir_ficha_persona_radar(rut_p, pilar_actual, desc_coincidente):
        u_obj = usuarios_dict.get(rut_p)
        c_obj = clientes_dict.get(rut_p)
        if not u_obj:
            return None
        edad_p = 24
        if c_obj and c_obj.fechanacimiento:
            fn = c_obj.fechanacimiento
            edad_p = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))

        tiene_match = rut_p in ruts_con_match
        gustos_p = gustos_por_rut.get(rut_p, [])
        disgustos_p = disgustos_por_rut.get(rut_p, [])
        msgs_p = [
            {
                'fecha': msg.fechaenvio.strftime('%d/%m/%Y') if msg.fechaenvio else 'Reciente',
                'contenido': msg.contenido,
                'direccion': 'Enviado' if msg.rut1 == '18012345-1' else 'Recibido',
            }
            for msg in mensajes_all
            if msg.rut1 == rut_p or msg.rut2 == rut_p
        ][:4]

        vals_p = [g['valor'] for g in gustos_p if g['categoria'] == pilar_actual]
        afinidad_pilar = round(sum(vals_p) / len(vals_p)) if vals_p else 88

        return {
            'rut': rut_p,
            'nombre': f"{u_obj.nombre} {u_obj.apellidopaterno or ''}".strip(),
            'edad': edad_p,
            'ocupacion': c_obj.ocupacionlaboral if (c_obj and c_obj.ocupacionlaboral) else 'Profesional',
            'nacionalidad': c_obj.nacionalidad if (c_obj and c_obj.nacionalidad) else 'Chilena',
            'biografia': c_obj.biografia if (c_obj and c_obj.biografia) else 'Le encanta conectar a través de intereses reales.',
            'estado_match': 'Match Activo' if tiene_match else 'Por Conectar',
            'afinidad': afinidad_pilar,
            'interes_destacado': desc_coincidente,
            'gustos': gustos_p[:6],
            'disgustos': disgustos_p[:4],
            'mensajes': msgs_p,
        }

    gustos_data_db = []
    disgustos_data_db = []
    detalles_gustos_db = {}
    detalles_disgustos_db = {}
    radar_drilldown = {'gustos': {}, 'disgustos': {}}

    for cat in categorias_radar:
        # GUSTOS
        gustos_cat = [g for g in gustos_all if g.categoria == cat]
        valores_num_g = [int(g.valor) for g in gustos_cat if str(g.valor).isdigit()]
        promedio_g = round(sum(valores_num_g) / len(valores_num_g)) if valores_num_g else 85
        gustos_data_db.append(promedio_g)

        desc_g = list({g.descripcion for g in gustos_cat if g.descripcion})[:5]
        detalles_gustos_db[cat] = desc_g if desc_g else ['Sin registros']

        subcats_g = {nombre_sub: {'vals': [], 'temas': set(), 'personas': {}} for nombre_sub, _ in mapa_subcategorias.get(cat, [])}
        for g in gustos_cat:
            sub_name = clasificar_en_subcategoria(cat, g.descripcion)
            if sub_name not in subcats_g:
                subcats_g[sub_name] = {'vals': [], 'temas': set(), 'personas': {}}
            val_int = int(g.valor) if str(g.valor).isdigit() else 85
            subcats_g[sub_name]['vals'].append(val_int)
            if g.descripcion:
                subcats_g[sub_name]['temas'].add(g.descripcion)
            if g.rut and g.rut != '18012345-1' and g.rut not in subcats_g[sub_name]['personas']:
                ficha = construir_ficha_persona_radar(g.rut, cat, g.descripcion)
                if ficha:
                    subcats_g[sub_name]['personas'][g.rut] = ficha

        lista_sub_g = []
        for idx_s, (nombre_sub, info_s) in enumerate(subcats_g.items()):
            prom_sub = round(sum(info_s['vals']) / len(info_s['vals'])) if info_s['vals'] else (88 - idx_s * 5)
            temas_lista = list(info_s['temas'])[:6] or [f"Afinidad en {nombre_sub}"]
            personas_lista = list(info_s['personas'].values())[:8]
            if not personas_lista:
                for g_aux in gustos_cat[:4]:
                    if g_aux.rut and g_aux.rut != '18012345-1':
                        f_aux = construir_ficha_persona_radar(g_aux.rut, cat, temas_lista[0])
                        if f_aux and f_aux not in personas_lista:
                            personas_lista.append(f_aux)
            lista_sub_g.append({
                'nombre': nombre_sub,
                'porcentaje': prom_sub,
                'temas': temas_lista,
                'personas': personas_lista,
            })
        radar_drilldown['gustos'][cat] = lista_sub_g

        # DISGUSTOS
        disgustos_cat = [d for d in disgustos_all if d.categoria == cat]
        valores_num_d = [int(d.valor) for d in disgustos_cat if str(d.valor).isdigit()]
        promedio_d = round(sum(valores_num_d) / len(valores_num_d)) if valores_num_d else 35
        disgustos_data_db.append(promedio_d)

        desc_d = list({d.descripcion for d in disgustos_cat if d.descripcion})[:5]
        detalles_disgustos_db[cat] = desc_d if desc_d else ['Sin registros']

        subcats_d = {nombre_sub: {'vals': [], 'temas': set(), 'personas': {}} for nombre_sub, _ in mapa_subcategorias.get(cat, [])}
        for d in disgustos_cat:
            sub_name = clasificar_en_subcategoria(cat, d.descripcion)
            if sub_name not in subcats_d:
                subcats_d[sub_name] = {'vals': [], 'temas': set(), 'personas': {}}
            val_int = int(d.valor) if str(d.valor).isdigit() else 45
            subcats_d[sub_name]['vals'].append(val_int)
            if d.descripcion:
                subcats_d[sub_name]['temas'].add(d.descripcion)
            if d.rut and d.rut != '18012345-1' and d.rut not in subcats_d[sub_name]['personas']:
                ficha = construir_ficha_persona_radar(d.rut, cat, d.descripcion)
                if ficha:
                    subcats_d[sub_name]['personas'][d.rut] = ficha

        lista_sub_d = []
        for idx_s, (nombre_sub, info_s) in enumerate(subcats_d.items()):
            prom_sub = round(sum(info_s['vals']) / len(info_s['vals'])) if info_s['vals'] else (42 - idx_s * 4)
            temas_lista = list(info_s['temas'])[:6] or [f"Límites en {nombre_sub}"]
            personas_lista = list(info_s['personas'].values())[:8]
            if not personas_lista:
                for d_aux in disgustos_cat[:4]:
                    if d_aux.rut and d_aux.rut != '18012345-1':
                        f_aux = construir_ficha_persona_radar(d_aux.rut, cat, temas_lista[0])
                        if f_aux and f_aux not in personas_lista:
                            personas_lista.append(f_aux)
            lista_sub_d.append({
                'nombre': nombre_sub,
                'porcentaje': prom_sub,
                'temas': temas_lista,
                'personas': personas_lista,
            })
        radar_drilldown['disgustos'][cat] = lista_sub_d

    radar_afinidad_payload = {
        'categorias': categorias_radar,
        'gustos_data': gustos_data_db,
        'disgustos_data': disgustos_data_db,
        'detalles_gustos': detalles_gustos_db,
        'detalles_disgustos': detalles_disgustos_db,
        'drilldown': radar_drilldown,
    }

    # 4. TIEMPO EN LA APP CON JERARQUÍA DE 4 NIVELES (Mes -> Semana -> Día -> Actividad BD)
    meses_config = [
        ('Mayo', 'May', 24, [5.5, 6.2, 5.8, 6.5]),
        ('Junio', 'Jun', 30, [7.0, 7.8, 7.2, 8.0]),
        ('Julio', 'Jul', 18, [4.2, 4.8, 4.5, 4.5]),
        ('Agosto', 'Ago', 35, [8.5, 9.0, 8.2, 9.3]),
        ('Septiembre', 'Sep', 28, [6.8, 7.2, 6.5, 7.5]),
        ('Octubre', 'Oct', 32, [6.5, 8.0, 7.5, 10.0]),
    ]
    dias_nombres = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    base_minutos_dia = [45, 60, 30, 85, 50, 110, 95]

    # Preparamos eventos reales desde las tablas MATCH, MENSAJE y NOTIFICACION para el Nivel 3
    eventos_reales = []
    for m_ev in drilldown_payload['match'][:6]:
        eventos_reales.append({
            'tipo': 'Match',
            'icono': 'bi-heart-fill text-danger',
            'persona': m_ev['nombre'],
            'detalle': f"Conexión exitosa con {m_ev['afinidad_general']}% de sintonía ({m_ev['ocupacion']})",
            'duracion': '18 min',
        })
    for msg_ev in mensajes_all[:12]:
        otro_rut = msg_ev.rut2 if msg_ev.rut1 == '18012345-1' else msg_ev.rut1
        u_otro = usuarios_dict.get(otro_rut)
        nombre_otro = u_otro.nombre if u_otro else 'Contacto'
        eventos_reales.append({
            'tipo': 'Chat',
            'icono': 'bi-chat-dots-fill text-primary',
            'persona': nombre_otro,
            'detalle': f'Mensaje: "{msg_ev.contenido[:55]}"',
            'duracion': '15 min',
        })
    for not_ev in notificaciones_all[:6]:
        eventos_reales.append({
            'tipo': 'Actividad',
            'icono': 'bi-bell-fill text-warning',
            'persona': 'Beyond Date',
            'detalle': not_ev.informacion[:65],
            'duracion': '10 min',
        })

    if not eventos_reales:
        eventos_reales = [{
            'tipo': 'Exploración',
            'icono': 'bi-compass-fill text-danger',
            'persona': 'Descubrimiento',
            'detalle': 'Revisión de perfiles compatibles por pilares',
            'duracion': '25 min',
        }]

    jerarquia_tiempo = []
    for idx_m, (nombre_mes, corto_mes, hrs_mes, semanas_hrs) in enumerate(meses_config):
        semanas_list = []
        for idx_s, hrs_sem in enumerate(semanas_hrs):
            factor = round(hrs_sem / 7.9, 2)
            dias_mins = [max(15, round(m_base * factor)) for m_base in base_minutos_dia]
            actividades_por_dia = {}
            for idx_d, d_label in enumerate(dias_nombres):
                desplazamiento = (idx_m + idx_s + idx_d) % len(eventos_reales)
                seleccion = [
                    eventos_reales[(desplazamiento + k) % len(eventos_reales)]
                    for k in range(min(4, len(eventos_reales)))
                ]
                actividades_por_dia[d_label] = seleccion

            semanas_list.append({
                'nombre': f'Semana {idx_s + 1}',
                'horas': hrs_sem,
                'dias_labels': dias_nombres,
                'dias_data': dias_mins,
                'actividades': actividades_por_dia,
            })

        jerarquia_tiempo.append({
            'mes_corto': corto_mes,
            'mes_largo': nombre_mes,
            'horas': hrs_mes,
            'semanas': semanas_list,
        })

    tiempo_payload = {
        'diario': {
            'labels': dias_nombres,
            'data': base_minutos_dia,
            'unit': 'min',
            'label': 'Minutos por día'
        },
        'semanal': {
            'labels': ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
            'data': [6.5, 8.0, 5.2, 9.4],
            'unit': 'hrs',
            'label': 'Horas por semana'
        },
        'mensual': {
            'labels': [m[1] for m in meses_config],
            'data': [m[2] for m in meses_config],
            'unit': 'hrs',
            'label': 'Horas por mes'
        },
        'jerarquia': jerarquia_tiempo,
    }

    context = {
        'perfil': perfil_mock,
        'chart_payload': chart_payload,
        'drilldown_payload': drilldown_payload,
        'tiempo_payload': tiempo_payload,
        'arquetipo_payload': arquetipo_payload,
        'radar_afinidad_payload': radar_afinidad_payload,
    }

    cache.set('graficosU_full_context_v5', context, 3600)
    return render(request, 'usuario/graficosU.html', context)


# =========================================================================
# 7. VISTAS ADMINISTRADOR E INICIO PÚBLICO
# =========================================================================
def administrador(request):
    return render(request, 'admin/administrador.html')


def admin_inicio(request):
    # 1. Datos de Conexiones recientes
    labels = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]
    datasets = [{
            "data": [120, 180, 90, 220, 150],
            "borderColor": "#B94448",
            "backgroundColor": "#B944482E",
            "tension": 0.2,
            "fill": True,
        }]
    matches_totales = 20012

    # 2. Datos del Histórico de Matches (Conexión a BD AWS)
    matches_exitosos = Match.objects.filter(estado=1, fechamatch__isnull=False)

    conteo_dias = {"Lun": 0, "Mar": 0, "Mié": 0, "Jue": 0, "Vie": 0, "Sáb": 0, "Dom": 0}
    dias_map = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
    conteo_meses = {"Ene": 0, "Feb": 0, "Mar": 0, "Abr": 0, "May": 0, "Jun": 0, "Jul": 0, "Ago": 0, "Sep": 0, "Oct": 0, "Nov": 0, "Dic": 0}
    meses_map = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

    for m in matches_exitosos:
        if m.fechamatch:
            dia_str = dias_map.get(m.fechamatch.weekday())
            if dia_str:
                conteo_dias[dia_str] += 1
            mes_str = meses_map.get(m.fechamatch.month)
            if mes_str:
                conteo_meses[mes_str] += 1

    periodos_matchs = {
        "semana": {
            "labels": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
            "data": [conteo_dias[d] for d in ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]],
            "detalle": "Matches por día de la semana",
            "eje_x": "Día",
        },
        "mes": {
            "labels": ["Sem 1", "Sem 2", "Sem 3", "Sem 4"],
            "data": [
                matches_exitosos.filter(fechamatch__day__lte=7).count(),
                matches_exitosos.filter(fechamatch__day__gt=7, fechamatch__day__lte=14).count(),
                matches_exitosos.filter(fechamatch__day__gt=14, fechamatch__day__lte=21).count(),
                matches_exitosos.filter(fechamatch__day__gt=21).count(),
            ],
            "detalle": "Matches por semana del mes",
            "eje_x": "Semana",
        },
        "anio": {
            "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
            "data": [conteo_meses[mes] for mes in ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]],
            "detalle": "Matches por mes del año",
            "eje_x": "Mes",
        },
    }

    # 3. Distribución de edades y Gustos
    edades_labels = ["18-19", "20-29", "30-39", "40-49", "50-59", "60+"]
    conteos = {
        grupo: {rango: 0 for rango in edades_labels}
        for grupo in ("Hombres", "Mujeres", "Otros")
    }
    hoy = date.today()

    for nacimiento, sexo in Cliente.objects.values_list(
        "fechanacimiento", "sexo"
    ).iterator():
        if not nacimiento:
            continue

        edad = hoy.year - nacimiento.year - (
            (hoy.month, hoy.day) < (nacimiento.month, nacimiento.day)
        )
        if edad < 18:
            continue

        if edad < 20:
            rango = "18-19"
        elif edad < 30:
            rango = "20-29"
        elif edad < 40:
            rango = "30-39"
        elif edad < 50:
            rango = "40-49"
        elif edad < 60:
            rango = "50-59"
        else:
            rango = "60+"

        sexo = (sexo or "").strip().casefold()
        if sexo in ("masculino", "hombre", "m"):
            grupo = "Hombres"
        elif sexo in ("femenino", "mujer", "f"):
            grupo = "Mujeres"
        else:
            grupo = "Otros"
        conteos[grupo][rango] += 1

    datasets2 = [
        {
            "label": "Hombres",
            "data": [-conteos["Hombres"][r] for r in edades_labels],
            "backgroundColor": "#652E38",
        },
        {
            "label": "Mujeres",
            "data": [conteos["Mujeres"][r] for r in edades_labels],
            "backgroundColor": "#E86E67",
        },
        {
            "label": "Otros",
            "data": [conteos["Otros"][r] for r in edades_labels],
            "backgroundColor": "#C7B6BC",
        },
    ]

    gustos_labels = ["Música", "Viajes", "Cine", "Deporte", "Libros"]
    gustos_valores = [60, 55, 49, 32, 2]

    conexiones_resientes = {
        "labels": ["Lun", "Mar", "Mié"],
        "usuarios": {"hombres": [3, 4, 2], "mujeres": [5, 2, 4]},
        "administradores": {"hombres": [1, 0, 1], "mujeres": [0, 1, 0]}
        }

    matches_diarios = [
        {
            "fecha": fila["fechamatch"].isoformat(),
            "total": fila["total"],
        }
        for fila in (
            matches_exitosos.order_by()
            .values("fechamatch")
            .annotate(total=Count("idmatch"))
            .order_by("fechamatch")
        )
    ]

    context = {
        "clientes_registrados": 20,
        "matches_totales": f"{matches_totales:,}".replace(",", "."),
        "reportes_usuarios": 33,
        "notificacion_pendiente": 67,
        "labels_json": json.dumps(labels, ensure_ascii=False),
        "datasets_json": json.dumps(datasets, ensure_ascii=False),
        "periodos_matchs_json": json.dumps(periodos_matchs, ensure_ascii=False),
        "edades_labels_json": json.dumps(edades_labels, ensure_ascii=False),
        "datasets2_json": json.dumps(datasets2, ensure_ascii=False),
        "gustos_labels_json": json.dumps(gustos_labels, ensure_ascii=False),
        "gustos_valores_json": json.dumps(gustos_valores),
        "kpi_matchs": 60.3,
        "kpi_estancados": 3.25,
        "conexiones_recientes_json": json.dumps(conexiones_resientes),
        "matches_diarios_json": json.dumps(matches_diarios, ensure_ascii=False),
        "edades_desde_bd": True,
    }
    ######## Bloque para probar el sankey
    parejas = {}
    registros = (
        Match.objects.filter(estado__in=[0, 1])
        .order_by("-fechamatch", "-idmatch")
        .values_list("cliente1rut", "cliente2rut", "estado")
    )
    for rut1, rut2, estado in registros:
        if rut1 and rut2 and rut1 != rut2:
            parejas.setdefault(tuple(sorted((rut1, rut2))), (rut1, rut2, estado))

    ruts = {rut for pareja in parejas for rut in pareja}

    def preferencias_por_usuario(modelo):
        datos = defaultdict(lambda: defaultdict(set))
        filas = modelo.objects.filter(rut__in=ruts).values_list(
            "rut", "categoria", "descripcion"
        )
        for rut, categoria, descripcion in filas:
            if categoria and descripcion:
                datos[rut][categoria].add(descripcion.strip().casefold())
        return datos

    gustos = preferencias_por_usuario(Gusto)
    disgustos = preferencias_por_usuario(Disgusto)

    def categoria_compartida(datos, rut1, rut2, alternativa):
        coincidencias = []
        for categoria in datos[rut1].keys() & datos[rut2].keys():
            cantidad = len(datos[rut1][categoria] & datos[rut2][categoria])
            if cantidad:
                coincidencias.append((cantidad, categoria))
        return sorted(coincidencias, key=lambda item: (-item[0], item[1]))[0][1] if coincidencias else alternativa

    conteo = Counter()
    for rut1, rut2, estado in parejas.values():
        gusto = categoria_compartida(gustos, rut1, rut2, "Sin gusto común")
        disgusto = categoria_compartida(disgustos, rut1, rut2, "Sin disgusto común")
        resultado = "Match" if estado == 1 else "No match"
        conteo[(gusto, disgusto, resultado)] += 1

    context["sankey_admin_json"] = json.dumps({
        "sintetico": False,
        "paths": [
            {"gusto": gusto, "disgusto": disgusto,
            "resultado": resultado, "total": total}
            for (gusto, disgusto, resultado), total in conteo.items()
        ],
    }, ensure_ascii=False)
    ########

    ####### Radar
    pilares = [
        "Valores", "Hobbies", "Dinámica Social",
        "Lenguaje del Amor", "Metas & Futuro",
    ]

    def datos_radar(modelo):
        por_persona = defaultdict(list)
        por_descripcion = defaultdict(list)

        for rut, categoria, descripcion, valor in modelo.objects.values_list(
            "rut", "categoria", "descripcion", "valor"
        ):
            categoria = (categoria or "").strip()
            if categoria not in pilares or not rut:
                continue
            try:
                puntuacion = float(str(valor).replace(",", "."))
            except (TypeError, ValueError):
                continue
            if not 0 <= puntuacion <= 100:
                continue

            por_persona[(categoria, rut)].append(puntuacion)
            if descripcion:
                por_descripcion[(categoria, descripcion.strip())].append(puntuacion)

        promedios = []
        detalle = {}
        for categoria in pilares:
            valores = [
                sum(puntos) / len(puntos)
                for (cat, _rut), puntos in por_persona.items()
                if cat == categoria
            ]
            promedios.append(round(sum(valores) / len(valores), 1) if valores else None)

            items = [
                (nombre, puntos)
                for (cat, nombre), puntos in por_descripcion.items()
                if cat == categoria
            ]
            items.sort(key=lambda item: (-len(item[1]), item[0]))
            detalle[categoria] = [
                {"nombre": nombre, "porcentaje": round(sum(puntos) / len(puntos), 1)}
                for nombre, puntos in items[:5]
            ]

        return promedios, detalle

    gustos_data, gustos_detalle = datos_radar(Gusto)
    disgustos_data, disgustos_detalle = datos_radar(Disgusto)

    sexo_por_rut = dict(
        Cliente.objects.values_list("usuario_rut_id", "sexo")
    )

    def agregar_genero(detalle, modelo):
        usuarios_por_preferencia = defaultdict(set)

        for rut, categoria, descripcion, valor in modelo.objects.values_list(
            "rut", "categoria", "descripcion", "valor"
        ):
            if not rut or not categoria or not descripcion:
                continue
            try:
                puntuacion = float(str(valor).replace(",", "."))
            except (TypeError, ValueError):
                continue
            if not 0 <= puntuacion <= 100:
                continue

            clave = (categoria.strip(), descripcion.strip())
            usuarios_por_preferencia[clave].add(rut)

        for categoria, items in detalle.items():
            for item in items:
                conteo = {"hombres": 0, "mujeres": 0, "otros": 0}
                for rut in usuarios_por_preferencia[(categoria, item["nombre"])]:
                    sexo = (sexo_por_rut.get(rut) or "").strip().casefold()
                    if sexo in ("masculino", "hombre"):
                        conteo["hombres"] += 1
                    elif sexo in ("femenino", "mujer"):
                        conteo["mujeres"] += 1
                    else:
                        conteo["otros"] += 1
                item["genero"] = conteo

    agregar_genero(gustos_detalle, Gusto)
    agregar_genero(disgustos_detalle, Disgusto)


    context["radar_admin_json"] = json.dumps({
        "categorias": pilares,
        "gustos_data": gustos_data,
        "disgustos_data": disgustos_data,
        "drilldown": {
            "gustos": gustos_detalle,
            "disgustos": disgustos_detalle,
        },
    }, ensure_ascii=False)

    clientes = {
        rut: (orientacion, nacimiento)
        for rut, orientacion, nacimiento in Cliente.objects.values_list(
            "usuario_rut_id", "orientacionsexual", "fechanacimiento"
        )
    }

    por_orientacion = defaultdict(Counter)
    por_brecha = defaultdict(Counter)

    for rut1, rut2, estado in parejas.values():
        persona1 = clientes.get(rut1)
        persona2 = clientes.get(rut2)
        if not persona1 or not persona2:
            continue

        clave_resultado = "match" if estado == 1 else "no_match"
        orientacion1, nacimiento1 = persona1
        orientacion2, nacimiento2 = persona2

        if orientacion1 and orientacion2:
            grupo = " + ".join(sorted(
                [orientacion1.strip(), orientacion2.strip()],
                key=str.casefold
            ))
            por_orientacion[grupo][clave_resultado] += 1

        if nacimiento1 and nacimiento2:
            diferencia = abs((nacimiento1 - nacimiento2).days) / 365.2425
            if diferencia < 3:
                grupo = "0–2 años"
            elif diferencia < 6:
                grupo = "3–5 años"
            elif diferencia < 10:
                grupo = "6–9 años"
            else:
                grupo = "10 años o más"
            por_brecha[grupo][clave_resultado] += 1

    def filas_factor(conteos, orden=None):
        nombres = orden or sorted(
            conteos,
            key=lambda nombre: -sum(conteos[nombre].values())
        )
        return [
            {
                "label": nombre,
                "match": conteos[nombre]["match"],
                "no_match": conteos[nombre]["no_match"],
            }
            for nombre in nombres
            if nombre in conteos
        ]

    context["match_factores_json"] = json.dumps({
        "sintetico": False,
        "orientacion": filas_factor(por_orientacion),
        "brecha_edad": filas_factor(
            por_brecha,
            ["0–2 años", "3–5 años", "6–9 años", "10 años o más"]
        ),
    }, ensure_ascii=False)
        #######
    ####kpis
    resultados_diarios = (
        Match.objects
        .filter(fechamatch__isnull=False, estado__in=[0, 1])
        .values("fechamatch")
        .annotate(
            match=Count("idmatch", filter=Q(estado=1)),
            no_match=Count("idmatch", filter=Q(estado=0)),
        )
        .order_by("fechamatch")
    )

    context["kpi_diarios_json"] = json.dumps([
        {
            "fecha": fila["fechamatch"].isoformat(),
            "match": fila["match"],
            "no_match": fila["no_match"],
        }
        for fila in resultados_diarios
    ], ensure_ascii=False)

        #####

    return render(request, "admin/inicio.html", context)


def admin_estadisticas(request):
    """
    [CONEXIÓN A BASE DE DATOS - AWS RDS]
    Función que consulta la tabla 'Match' en la base de datos de AWS para
    generar dinámicamente el histórico de matches según la fecha real (fechamatch)
    agrupada por días de la semana y periodos.
    """
    # Consulta a la BD filtrando los matches exitosos (estado=1)
    matches_exitosos = Match.objects.filter(estado=1, fechamatch__isnull=False)

    conteo_dias = {"Lun": 0, "Mar": 0, "Mié": 0, "Jue": 0, "Vie": 0, "Sáb": 0, "Dom": 0}
    dias_map = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}

    conteo_meses = {"Ene": 0, "Feb": 0, "Mar": 0, "Abr": 0, "May": 0, "Jun": 0, "Jul": 0, "Ago": 0, "Sep": 0, "Oct": 0, "Nov": 0, "Dic": 0}
    meses_map = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

    for m in matches_exitosos:
        if m.fechamatch:
            dia_str = dias_map.get(m.fechamatch.weekday())
            if dia_str:
                conteo_dias[dia_str] += 1
            mes_str = meses_map.get(m.fechamatch.month)
            if mes_str:
                conteo_meses[mes_str] += 1

    periodos_matchs = {
        "semana": {
            "labels": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
            "data": [conteo_dias[d] for d in ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]],
            "detalle": "Matches por día de la semana",
            "eje_x": "Día",
        },
        "mes": {
            "labels": ["Semana 1", "Semana 2", "Semana 3", "Semana 4"],
            "data": [
                matches_exitosos.filter(fechamatch__day__lte=7).count(),
                matches_exitosos.filter(fechamatch__day__gt=7, fechamatch__day__lte=14).count(),
                matches_exitosos.filter(fechamatch__day__gt=14, fechamatch__day__lte=21).count(),
                matches_exitosos.filter(fechamatch__day__gt=21).count(),
            ],
            "detalle": "Matches por semana del mes",
            "eje_x": "Semana",
        },
        "anio": {
            "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
            "data": [conteo_meses[mes] for mes in ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]],
            "detalle": "Matches por mes del año",
            "eje_x": "Mes",
        },
    }

    # 2. Distribución de edades (Datos simulados para lucir bien el panel)
    edades_labels = ["18-19", "20-29", "30-39", "40-49", "50-59", "60+"]
    hombres_por_edad = {"18-19": 38, "20-29": 55, "30-39": 64, "40-49": 52, "60+": 22}
    mujeres_por_edad = {"18-19": 42, "20-29": 61, "30-39": 70, "40-49": 58, "60+": 35}
    datasets2 = [
        {
            "label": "Hombres",
            "data": [-hombres_por_edad.get(rango, 0) for rango in edades_labels],
            "backgroundColor": "#652E38",
        },
        {
            "label": "Mujeres",
            "data": [mujeres_por_edad.get(rango, 0) for rango in edades_labels],
            "backgroundColor": "#E86E67",
        },
    ]

    # 3. Top gustos (Datos simulados)
    gustos_labels = ["Música", "Viajes", "Cine", "Deporte", "Libros"]
    gustos_valores = [60, 55, 49, 32, 2]

    context = {
        "periodos_matchs_json": json.dumps(periodos_matchs, ensure_ascii=False),
        "edades_labels_json": json.dumps(edades_labels, ensure_ascii=False),
        "datasets2_json": json.dumps(datasets2, ensure_ascii=False),
        "gustos_labels_json": json.dumps(gustos_labels, ensure_ascii=False),
        "gustos_valores_json": json.dumps(gustos_valores),
        "kpi_matchs": 60.3,
        "kpi_estancados": 3.25,
    }

    return render(request, "admin/estadisticas.html", context)


RUT_ADMIN_DEMO = "admin-demo"

def admin_notificaciones(request):
    if not request.session.get("es_admin"):
        return redirect("login_view")

    es_demo = not request.session.get("admin_rut")
    if request.method == "POST" and request.POST.get("accion") in ("editar", "eliminar"):
        accion = request.POST["accion"]
        aviso_id = request.POST.get("idnotificacion", "").strip()

        if es_demo:
            permitidos = Notificacion.objects.filter(rut=RUT_ADMIN_DEMO)
        else:
            ruts_admin = Administrador.objects.values_list(
                "usuario_rut_id", flat=True
            )
            permitidos = Notificacion.objects.filter(rut__in=ruts_admin)

        aviso = permitidos.filter(idnotificacion=aviso_id).first()

        if aviso is None:
            messages.error(request, "No se encontró la notificación.")
        elif accion == "editar":
            tipo = request.POST.get("tipo", "")
            mensaje = request.POST.get("mensaje", "").strip()

            if tipo not in ("Reporte", "Mensaje", "Sistema"):
                messages.error(request, "Tipo de aviso no válido.")
            elif not mensaje or len(mensaje) > 180:
                messages.error(request, "Escribe un mensaje de hasta 180 caracteres.")
            else:
                aviso.informacion = f"{tipo}: {mensaje}"
                try:
                    aviso.save(update_fields=["informacion"])
                    messages.success(request, "Notificación actualizada.")
                except IntegrityError:
                    messages.error(request, "La base de datos rechazó el cambio.")
        else:
            try:
                aviso.delete()
                messages.success(request, "Notificación eliminada.")
            except IntegrityError:
                messages.error(request, "No se pudo eliminar la notificación.")

        return redirect("admin_notificaciones")
    if request.method == "POST" and request.POST.get("accion") == "crear":
        rut = (
            RUT_ADMIN_DEMO if es_demo
            else request.POST.get("rut", "").strip()
        )
        tipo = request.POST.get("tipo", "")
        mensaje = request.POST.get("mensaje", "").strip()

        if tipo not in ("Reporte", "Mensaje", "Sistema"):
            messages.error(request, "Selecciona un tipo válido.")
        elif not mensaje or len(mensaje) > 180:
            messages.error(request, "Escribe un mensaje de hasta 180 caracteres.")
        elif not es_demo and not Administrador.objects.filter(
            usuario_rut_id=rut
        ).exists():
            messages.error(request, "Selecciona un administrador válido.")
        else:
            Notificacion.objects.create(
                idnotificacion=f"ADM-{uuid4().hex}",
                rut=rut,
                informacion=f"{tipo}: {mensaje}",
                fecha=date.today(),
                estado=0,
            )
            messages.success(request, "Notificación creada.")

        return redirect("admin_notificaciones")

    if es_demo:
        registros = Notificacion.objects.filter(rut=RUT_ADMIN_DEMO)
    else:
        ruts_admin = Administrador.objects.values_list(
            "usuario_rut_id", flat=True
        )
        registros = Notificacion.objects.filter(rut__in=ruts_admin)

    registros = registros.order_by("-fecha", "-idnotificacion")[:50]

    notificaciones_reales = []
    for n in registros:
        texto = (n.informacion or "").casefold()
        if any(palabra in texto for palabra in ("reporte", "denuncia", "moderaci")):
            tipo, titulo = "reportes", "Revisar reporte"
        elif any(palabra in texto for palabra in ("mensaje", "correo", "comunicaci")):
            tipo, titulo = "mensajes", "Revisar comunicación"
        else:
            tipo, titulo = "sistema", "Aviso del sistema"

        notificaciones_reales.append({
            "id": n.idnotificacion,
            "tipo": tipo,
            "titulo": titulo,
            "informacion": n.informacion,
            "fecha": n.fecha,
            "no_leida": n.estado == 0,
        })


    administradores_destino = [
        {
            "rut": admin.usuario_rut.rut,
            "nombre": f"{admin.usuario_rut.nombre} {admin.usuario_rut.apellidopaterno}",
        }
        for admin in Administrador.objects.select_related("usuario_rut")
    ]

    return render(
        request,
        "admin/notificacion.html",
        {
        "notificaciones_reales": notificaciones_reales,
        "administradores_destino": administradores_destino,
        "notificaciones_demo_bd": True,
        "acciones_notificaciones_habilitadas": True,
    },
    )


def admin_usuarios(request):
    if request.method == "POST":
        accion = request.POST.get("accion", "")
        rut = request.POST.get("rut", "").strip()
        usuario = Usuario.objects.filter(rut=rut).first()

        if usuario is None:
            messages.error(request, "No se encontró el usuario.")
            return redirect("admin_usuarios")

        if accion == "editar":
            nombre = request.POST.get("nombre", "").strip()
            paterno = request.POST.get("apellidopaterno", "").strip()
            materno = request.POST.get("apellidomaterno", "").strip()
            correo = request.POST.get("correo", "").strip()
            telefono = request.POST.get("telefono", "").strip()
            estado = request.POST.get("estado", "")

            if not all((nombre, paterno, materno, correo, telefono)):
                messages.error(request, "Completa todos los campos.")
            elif not telefono.isdecimal() or int(telefono) > 2147483647:
                messages.error(request, "El teléfono debe ser un número válido.")
            elif estado not in ("Activo", "Suspendido"):
                messages.error(request, "Estado no válido.")
            else:
                usuario.nombre = nombre
                usuario.apellidopaterno = paterno
                usuario.apellidomaterno = materno
                usuario.correo = correo
                usuario.telefono = int(telefono)
                usuario.estado = 1 if estado == "Activo" else 0

                try:
                    usuario.save(update_fields=[
                        "nombre", "apellidopaterno", "apellidomaterno",
                        "correo", "telefono", "estado",
                    ])
                    messages.success(request, "Usuario actualizado.")
                except IntegrityError:
                    messages.error(request, "La base de datos rechazó el cambio.")

        elif accion == "eliminar":
            try:
                usuario.delete()
                messages.success(request, "Usuario eliminado.")
            except IntegrityError:
                messages.error(
                    request,
                    "No se pudo eliminar: existen registros relacionados.",
                )
        else:
            messages.error(request, "Acción no reconocida.")

        return redirect("admin_usuarios")



    registros = Usuario.objects.values(
        "rut", "nombre", "apellidopaterno",
        "apellidomaterno", "correo", "estado", "telefono"
    ).order_by("nombre", "apellidopaterno")

    users = [
        {
            "rut": u["rut"],
            "nombre": u["nombre"],
            "apellidoPaterno": u["apellidopaterno"],
            "apellidoMaterno": u["apellidomaterno"],
            "correo": u["correo"],
            "estado": "Activo" if u["estado"] == 1 else "Suspendido",
            "telefono": u["telefono"],
            "editar_url": request.path,
            "eliminar_url": request.path,
        }
        for u in registros
    ]

    return render(request, "admin/usuarios.html", {"users": users})


def admin_mensajes(request):
    if not request.session.get("es_admin"):
        return redirect("login_view")

    rut_admin = request.session.get("admin_rut") or RUT_ADMIN_DEMO

    if request.method == "POST":
        receptor_rut = request.POST.get("receptor_rut", "").strip()
        contenido = request.POST.get("contenido", "").strip()

        if not Usuario.objects.filter(rut=receptor_rut).exists():
            messages.error(request, "No se encontró al usuario destinatario.")
        elif not contenido or len(contenido) > 200:
            messages.error(request, "Escribe un mensaje de hasta 200 caracteres.")
        else:
            Mensaje.objects.create(
                idmensaje=f"MSG-ADM-{uuid4().hex[:20]}",
                rut1=rut_admin,
                rut2=receptor_rut,
                contenido=contenido,
                fechaenvio=date.today(),
                leido=0,
            )
            cache.delete(f"chat_historial_{receptor_rut}_{rut_admin}")
            cache.delete(f"contactos_usuario_{receptor_rut}")
            messages.success(request, "Respuesta enviada.")

        url = reverse("admin_mensajes")
        return redirect(f"{url}?{urlencode({'chat': receptor_rut})}")

    registros = list(
        Mensaje.objects.filter(
            Q(rut1=rut_admin) | Q(rut2=rut_admin)
        ).order_by("-fechaenvio", "-idmensaje")
    )

    ruts = {
        m.rut2 if m.rut1 == rut_admin else m.rut1
        for m in registros
    }
    usuarios = {
        u.rut: u
        for u in Usuario.objects.filter(rut__in=ruts)
    }

    conversaciones = {}
    for m in registros:
        otro_rut = m.rut2 if m.rut1 == rut_admin else m.rut1
        usuario = usuarios.get(otro_rut)
        if usuario is None:
            continue

        if otro_rut not in conversaciones:
            conversaciones[otro_rut] = {
                "rut": otro_rut,
                "nombre": f"{usuario.nombre} {usuario.apellidopaterno}".strip(),
                "fecha": m.fechaenvio.strftime("%d/%m/%Y"),
                "ultimo_mensaje": m.contenido,
                "no_leidos": 0,
                "activo": False,
            }

        if m.rut2 == rut_admin and m.leido == 0:
            conversaciones[otro_rut]["no_leidos"] += 1

    rut_activo = request.GET.get("chat", "").strip()
    if rut_activo not in conversaciones:
        rut_activo = next(iter(conversaciones), "")

    historial_admin = []
    conversacion_activa = None

    if rut_activo:
        Mensaje.objects.filter(
            rut1=rut_activo,
            rut2=rut_admin,
            leido=0,
        ).update(leido=1)

        conversaciones[rut_activo]["no_leidos"] = 0
        conversaciones[rut_activo]["activo"] = True
        conversacion_activa = conversaciones[rut_activo]

        historial = Mensaje.objects.filter(
            Q(rut1=rut_admin, rut2=rut_activo) |
            Q(rut1=rut_activo, rut2=rut_admin)
        ).order_by("-fechaenvio", "-idmensaje")[:50]

        historial_admin = [
            {
                "contenido": m.contenido,
                "fecha": m.fechaenvio.strftime("%d/%m/%Y"),
                "es_admin": m.rut1 == rut_admin,
            }
            for m in reversed(list(historial))
        ]

    return render(request, "admin/mensajes.html", {
        "conversaciones_admin": list(conversaciones.values()),
        "conversacion_activa": conversacion_activa,
        "historial_admin": historial_admin,
        "total_pendientes": sum(
            c["no_leidos"] for c in conversaciones.values()
        ),
        "mensajeria_admin_habilitada": True,
    })
    
    
# =========================================================================
# MANTENEDOR 2 (CRUD COMPLETO): LÍMITES Y DISGUSTOS (Tabla DISGUSTO en AWS RDS)
# =========================================================================
def mantenedor_disgustosU(request):
    cliente_principal = Cliente.objects.select_related('usuario_rut').filter(idcliente='CLI-001').first()
    if not cliente_principal:
        cliente_principal = Cliente.objects.select_related('usuario_rut').first()
    usuario_principal = cliente_principal.usuario_rut if cliente_principal else Usuario.objects.first()
    rut_actual = usuario_principal.rut if usuario_principal else ''

    pilares = ['Valores', 'Hobbies', 'Dinámica Social', 'Lenguaje del Amor', 'Metas & Futuro']

    if request.method == 'POST' and rut_actual:
        accion = request.POST.get('accion', '')

        # CREATE: Crear nuevo registro en tabla DISGUSTO
        if accion == 'crear':
            categoria = request.POST.get('categoria', 'Valores').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            valor = request.POST.get('valor', '80').strip()
            if descripcion:
                nuevo_id = f"DIS-{rut_actual[:4]}-{Disgusto.objects.count() + 101}"[:20]
                Disgusto.objects.create(
                    pk=nuevo_id,
                    categoria=categoria[:45],
                    valor=valor if valor.isdigit() else '80',
                    descripcion=descripcion[:100],
                    rut=rut_actual
                )

        # UPDATE: Actualizar registro existente por su PK
        elif accion == 'editar':
            pk_id = request.POST.get('pk_id', '').strip()
            categoria = request.POST.get('categoria', 'Valores').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            valor = request.POST.get('valor', '80').strip()
            item = Disgusto.objects.filter(pk=pk_id, rut=rut_actual).first()
            if item and descripcion:
                item.categoria = categoria[:45]
                item.descripcion = descripcion[:100]
                item.valor = valor if valor.isdigit() else '80'
                item.save()

        # DELETE: Eliminar registro por su PK
        elif accion == 'eliminar':
            pk_id = request.POST.get('pk_id', '').strip()
            Disgusto.objects.filter(pk=pk_id, rut=rut_actual).delete()

        # Limpiamos caché de gráficos para que el Radar refleje los cambios al instante
        cache.delete('graficosU_full_context_v5')
        return redirect('mantenedor_disgustosU')

    disgustos_usr = Disgusto.objects.filter(rut=rut_actual) if rut_actual else []

    context = {
        'usuario': usuario_principal,
        'disgustos': disgustos_usr,
        'pilares': pilares,
        'total_registros': len(disgustos_usr),
    }
    return render(request, 'usuario/mantenedor_disgustosU.html', context)


# =========================================================================
# MANTENEDOR 3 (CRUD COMPLETO): CONEXIONES Y MENSAJES (Tablas MATCH y MENSAJE)
# =========================================================================
def mantenedor_matchesU(request):
    hoy = date.today()
    cliente_principal = Cliente.objects.select_related('usuario_rut').filter(idcliente='CLI-001').first()
    if not cliente_principal:
        cliente_principal = Cliente.objects.select_related('usuario_rut').first()
    usuario_principal = cliente_principal.usuario_rut if cliente_principal else Usuario.objects.first()
    rut_actual = usuario_principal.rut if usuario_principal else ''

    if request.method == 'POST' and rut_actual:
        accion = request.POST.get('accion', '')

        # CREATE MATCH: Crear una nueva conexión en tabla MATCH
        if accion == 'crear_match':
            rut_destino = request.POST.get('rut_destino', '').strip()
            estado_inicial = int(request.POST.get('estado', '1'))
            if rut_destino and rut_destino != rut_actual:
                nuevo_id = f"MTC-{Match.objects.count() + 201:04d}"
                Match.objects.create(
                    idmatch=nuevo_id,
                    fechamatch=hoy,
                    estado=estado_inicial,
                    cliente1rut=rut_actual,
                    cliente2rut=rut_destino
                )

        # UPDATE MATCH: Cambiar estado (Match Activo <-> En Pausa / No Match) o fecha
        elif accion == 'editar_match':
            idmatch = request.POST.get('idmatch', '').strip()
            nuevo_estado = int(request.POST.get('estado', '1'))
            m_obj = Match.objects.filter(idmatch=idmatch).first()
            if m_obj:
                m_obj.estado = nuevo_estado
                m_obj.save()

        # DELETE MATCH: Eliminar conexión de la tabla MATCH
        elif accion == 'eliminar_match':
            idmatch = request.POST.get('idmatch', '').strip()
            Match.objects.filter(idmatch=idmatch).delete()

        # UPDATE MENSAJE: Editar el texto de un mensaje enviado en tabla MENSAJE
        elif accion == 'editar_mensaje':
            idmensaje = request.POST.get('idmensaje', '').strip()
            nuevo_contenido = request.POST.get('contenido', '').strip()
            msg_obj = Mensaje.objects.filter(idmensaje=idmensaje, rut1=rut_actual).first()
            if msg_obj and nuevo_contenido:
                msg_obj.contenido = nuevo_contenido[:200]
                msg_obj.save()
                cache.delete(f'chat_historial_{rut_actual}_{msg_obj.rut2}')

        # DELETE MENSAJE: Borrar un mensaje enviado de la tabla MENSAJE
        elif accion == 'eliminar_mensaje':
            idmensaje = request.POST.get('idmensaje', '').strip()
            msg_obj = Mensaje.objects.filter(idmensaje=idmensaje, rut1=rut_actual).first()
            if msg_obj:
                cache.delete(f'chat_historial_{rut_actual}_{msg_obj.rut2}')
                msg_obj.delete()

        cache.delete(f'contactos_usuario_{rut_actual}')
        cache.delete('graficosU_full_context_v5')
        return redirect('mantenedor_matchesU')

    # Lectura (READ) de Matches y Mensajes del usuario
    usuarios_dict = {u.rut: u for u in Usuario.objects.all()}
    clientes_dict = {c.usuario_rut.rut: c for c in Cliente.objects.select_related('usuario_rut').all()}

    matches_qs = Match.objects.filter(Q(cliente1rut=rut_actual) | Q(cliente2rut=rut_actual)).order_by('-fechamatch', '-idmatch')[:20]
    lista_matches = []
    ruts_conectados = set()

    for m in matches_qs:
        otro_rut = m.cliente2rut if m.cliente1rut == rut_actual else m.cliente1rut
        ruts_conectados.add(otro_rut)
        u_otro = usuarios_dict.get(otro_rut)
        c_otro = clientes_dict.get(otro_rut)
        if not u_otro:
            continue
        lista_matches.append({
            'idmatch': m.idmatch,
            'rut_persona': otro_rut,
            'nombre': f"{u_otro.nombre} {u_otro.apellidopaterno or ''}".strip(),
            'ocupacion': c_otro.ocupacionlaboral if (c_otro and c_otro.ocupacionlaboral) else 'Profesional',
            'nacionalidad': c_otro.nacionalidad if (c_otro and c_otro.nacionalidad) else 'Chilena',
            'fechamatch': m.fechamatch.strftime('%d/%m/%Y') if m.fechamatch else 'Reciente',
            'estado': m.estado,
        })

    # Perfiles disponibles para crear un nuevo Match
    perfiles_disponibles = []
    for r_key, u_val in usuarios_dict.items():
        if r_key != rut_actual and r_key not in ruts_conectados:
            c_val = clientes_dict.get(r_key)
            perfiles_disponibles.append({
                'rut': r_key,
                'nombre': f"{u_val.nombre} {u_val.apellidopaterno or ''}".strip(),
                'ocupacion': c_val.ocupacionlaboral if (c_val and c_val.ocupacionlaboral) else 'Estudiante',
            })

    # Mensajes enviados por el usuario (para poder editarlos o eliminarlos)
    mensajes_enviados_qs = Mensaje.objects.filter(rut1=rut_actual).order_by('-fechaenvio', '-idmensaje')[:15]
    lista_mensajes = []
    for msg in mensajes_enviados_qs:
        u_dest = usuarios_dict.get(msg.rut2)
        lista_mensajes.append({
            'idmensaje': msg.idmensaje,
            'receptor_nombre': u_dest.nombre if u_dest else msg.rut2,
            'receptor_rut': msg.rut2,
            'contenido': msg.contenido,
            'fecha': msg.fechaenvio.strftime('%d/%m/%Y') if msg.fechaenvio else 'Hoy',
        })

    context = {
        'matches': lista_matches,
        'perfiles_disponibles': perfiles_disponibles[:15],
        'mensajes_enviados': lista_mensajes,
    }
    return render(request, 'usuario/mantenedor_matchesU.html', context)


def index(request):
    return render(request, 'inicio/index.html')


def contacto(request):
    return render(request, 'inicio/contacto.html')


def faq(request):
    return render(request, 'inicio/faq.html')


def mision(request):
    return render(request, 'inicio/mision.html')


def login_view(request):
    error_msg = None
    if request.method == 'POST':
        rut_input = request.POST.get('rut', '').strip()
        pass_input = request.POST.get('password', '').strip()

        # Atajos rápidos para desarrollo
        if rut_input == 'admin' and pass_input == 'admin123':
            request.session["es_admin"] = True
            request.session.pop("admin_rut", None)
            return redirect('admin_inicio')
        if rut_input == 'user' and pass_input == 'user123':
            return redirect('inicioU')

        # Lógica real validando en AWS
        try:
            # Nota: Asegúrate de que el campo en tu modelo se llame 'contrasena' o 'contraseña' según el inspectdb
            usuario = Usuario.objects.get(rut=rut_input, contrasena=pass_input)
            es_admin = Administrador.objects.filter(usuario_rut=usuario).exists()
            if es_admin:
                request.session["es_admin"] = True
                request.session["admin_rut"] = usuario.rut
                return redirect('admin_inicio')
            else:
                return redirect('inicioU')
        except Usuario.DoesNotExist:
            error_msg = "RUT o contraseña incorrectos."

    return render(request, 'login.html', {'error': error_msg})
