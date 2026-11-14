from datetime import date
import base64
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.db.models import Count, Sum, Avg, Q
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

    # Traemos los clientes desde AWS RDS (excluyendo al usuario principal CLI-001)
    clientes_qs = Cliente.objects.select_related('usuario_rut').exclude(idcliente='CLI-001')

    if query:
        # Buscamos coincidencias en nombre, profesión, nacionalidad, biografía o en la tabla GUSTO
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

        # Obtenemos los gustos reales de este usuario en AWS RDS
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

    # Ordenamos de mayor a menor afinidad
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
            # Limpiamos la caché de este chat al enviar uno nuevo para que se actualice al instante
            cache.delete(f'chat_historial_{rut_actual}_{receptor_rut}')
            return redirect(f"/usuario/mensajes/?chat={receptor_rut}")

    # Intentamos leer la lista de contactos desde la caché RAM (durará 1 hora guardada)
    cache_key_contactos = f'contactos_usuario_{rut_actual}'
    contactos = cache.get(cache_key_contactos)

    if not contactos:
        # Si no está en caché, lo consultamos a AWS RDS una sola vez
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
        # Guardamos en la caché por 3600 segundos (1 hora)
        cache.set(cache_key_contactos, contactos, 3600)

    chat_seleccionado_rut = request.GET.get('chat', contactos[0]['rut'] if contactos else '')

    # Marcamos cuál está activo sin alterar la caché global
    contacto_activo = None
    for c in contactos:
        c['activo'] = (c['rut'] == chat_seleccionado_rut)
        if c['activo']:
            contacto_activo = c

    # Historial de mensajes optimizado con caché por chat
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
# 5. EDITAR PERFIL USUARIO: Actualización en AWS RDS (Tablas USUARIO y CLIENTE)
# =========================================================================

def editar_perfilU(request):
    hoy = date.today()
    cliente_principal = Cliente.objects.select_related('usuario_rut').filter(idcliente='CLI-001').first()
    if not cliente_principal:
        cliente_principal = Cliente.objects.select_related('usuario_rut').first()
    usuario_principal = cliente_principal.usuario_rut if cliente_principal else Usuario.objects.first()
    rut_actual = usuario_principal.rut if usuario_principal else ''

    # Calculamos la edad actual para mostrarla en el input
    edad_actual = 21
    if cliente_principal and cliente_principal.fechanacimiento:
        fn = cliente_principal.fechanacimiento
        edad_actual = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))

    fotos_guardadas = cache.get(f'fotos_galeria_{rut_actual}')
    if fotos_guardadas is None:
        fotos_guardadas = ['/static/usuario/img/javier.jpg']

    if request.method == 'POST':
        # 1. Actualizar datos básicos en USUARIO y CLIENTE (AWS RDS)
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

            # Si ingresó una edad válida, actualizamos fechanacimiento en AWS RDS
            if nueva_edad.isdigit():
                edad_int = max(18, min(99, int(nueva_edad)))
                cliente_principal.fechanacimiento = date(hoy.year - edad_int, 1, 1)

            cliente_principal.save()

        # 2. Actualizar Intereses y Pasiones en tabla GUSTO (AWS RDS)
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

        # 3. Actualizar Galería de Fotos
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

    # Traemos todos los intereses reales del usuario desde la tabla GUSTO en AWS RDS
    gustos_usr = Gusto.objects.filter(rut=rut_actual) if rut_actual else []

    # Obtenemos la galería de fotos (hasta 6) guardada para este usuario
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

def graficosU(request):
    """
    [CONEXIÓN A BASE DE DATOS - AWS RDS + DRILL-DOWN EN DONA Y RADAR]
    Consulta las tablas MATCH, USUARIO, CLIENTE, GUSTO, DISGUSTO y MENSAJE
    para alimentar los gráficos y la navegación multinivel amigable.
    """
    hoy = date.today()
    perfil_mock = {
        'nombre': 'Javier',
        'edad': 21,
    }

    cached_context = cache.get('graficosU_full_context_v2')
    if cached_context:
        return render(request, 'usuario/graficosU.html', cached_context)

    # =========================================================================
    # 1. BALANCE DE MATCHES + ÁRBOL DRILL-DOWN DE DONA
    # =========================================================================
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

            pilares = ['Valores', 'Hobbies', 'Dinámica Social', 'Lenguaje del Amor', 'Metas & Futuro']
            promedios_pilares = []
            for p_nombre in pilares:
                vals_p = [item['valor'] for item in gustos_p if item['categoria'] == p_nombre]
                promedios_pilares.append(round(sum(vals_p) / len(vals_p)) if vals_p else 82)

            msgs_persona = [
                {
                    'idmensaje': msg.idmensaje,
                    'fecha': msg.fechaenvio.strftime('%d/%m/%Y') if msg.fechaenvio else 'Reciente',
                    'contenido': msg.contenido,
                    'direccion': 'Enviado' if msg.rut1 == '18012345-1' else 'Recibido',
                }
                for msg in mensajes_all
                if msg.rut1 == rut_persona or msg.rut2 == rut_persona
            ][:6]

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
                'pilares_labels': pilares,
                'pilares_data': promedios_pilares,
                'gustos': gustos_p[:8],
                'disgustos': disgustos_p[:6],
                'mensajes': msgs_persona,
            })
        return lista

    drilldown_payload = {
        'match': construir_lista_drilldown(1),
        'no_match': construir_lista_drilldown(0),
    }

    # =========================================================================
    # 2. CARACTERÍSTICAS DE MATCHES
    # =========================================================================
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

    # =========================================================================
    # 3. RADAR DE AFINIDAD + DRILL-DOWN POR SUBCATEGORÍAS
    # =========================================================================
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
        # Si no coincide con una palabra clave específica, se asigna de forma balanceada a una subcategoría del pilar
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
        # --- GUSTOS ---
        gustos_cat = [g for g in gustos_all if g.categoria == cat]
        valores_num_g = [int(g.valor) for g in gustos_cat if str(g.valor).isdigit()]
        promedio_g = round(sum(valores_num_g) / len(valores_num_g)) if valores_num_g else 85
        gustos_data_db.append(promedio_g)

        desc_g = list({g.descripcion for g in gustos_cat if g.descripcion})[:5]
        detalles_gustos_db[cat] = desc_g if desc_g else ['Sin registros']

        # Agrupar por subcategoría para Gustos
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
            # Si una subcategoría tiene pocas personas directas, completamos con perfiles afines del pilar
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

        # --- DISGUSTOS ---
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

    # =========================================================================
    # 4. TIEMPO EN LA APP
    # =========================================================================
    tiempo_payload = {
        'diario': {
            'labels': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
            'data': [45, 60, 30, 85, 50, 110, 95],
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
            'labels': ['May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct'],
            'data': [24, 30, 18, 35, 28, 32],
            'unit': 'hrs',
            'label': 'Horas por mes'
        }
    }

    context = {
        'perfil': perfil_mock,
        'chart_payload': chart_payload,
        'drilldown_payload': drilldown_payload,
        'tiempo_payload': tiempo_payload,
        'arquetipo_payload': arquetipo_payload,
        'radar_afinidad_payload': radar_afinidad_payload,
    }

    cache.set('graficosU_full_context_v2', context, 3600)
    return render(request, 'usuario/graficosU.html', context)





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
    hombres_por_edad = {"18-19": 38, "20-29": 55, "30-39": 64, "40-49": 52, "60+": 22}
    mujeres_por_edad = {"18-19": 42, "20-29": 61, "30-39": 70, "40-49": 58, "60+": 35}
    datasets2 = [
        { "label": "Hombres", "data": [-hombres_por_edad.get(rango, 0) for rango in edades_labels], "backgroundColor": "#652E38" },
        { "label": "Mujeres", "data": [mujeres_por_edad.get(rango, 0) for rango in edades_labels], "backgroundColor": "#E86E67" },
    ]

    gustos_labels = ["Música", "Viajes", "Cine", "Deporte", "Libros"]
    gustos_valores = [60, 55, 49, 32, 2]

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
    }

    return render(request, "admin/inicio.html", context)

from datetime import date
import json



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

def admin_notificaciones(request):
    notificaciones = [
        {
            "id_notificacion": 1,
            "tema": "Reporte",
            "fecha": "Enero",
            "id_usuario": 2,
            "mensaje": "Usuario reportado por feo",
            "estado": 1
        },
        {
            "id_notificacion": 2,
            "tema": "Mensaje",
            "fecha": "Febrero",
            "id_usuario": 3,
            "mensaje": "Nuevo correo en bandeja",
            "estado": 1
        },
        {
            "id_notificacion": 3,
            "tema": "Reporte",
            "fecha": "Marzo",
            "id_usuario": 1,
            "mensaje": "Usuario menor de edad",
            "estado": 2
        }
    ]

    return render(
        request,
        "admin/notificacion.html",
        {"notificaciones": notificaciones}
    )


def admin_usuarios(request):

    users = [
        {
            "rut": "12.345.678-9",
            "nombre": "María",
            "apellidoPaterno": "González",
            "apellidoMaterno": "Pérez",
            "correo": "maria@ejemplo.cl",
            "estado": "Activo",
        },
        {
            "rut": "18.765.432-1",
            "nombre": "Juan",
            "apellidoPaterno": "Soto",
            "apellidoMaterno": "Rojas",
            "correo": "juan@ejemplo.cl",
            "estado": "Suspendido",
        },
    ]

    #users = Users.objects.all()
    return render(
            request,
            "admin/usuarios.html",
            {"users": users}
            )
    

    
    


def index(request):###
    return render(request, 'inicio/index.html')

def contacto(request):###
    return render(request, 'inicio/contacto.html')

def faq(request):###
    return render(request, 'inicio/faq.html')

def mision(request):##
    return render(request, 'inicio/mision.html')

def login_view(request):
    error_msg = None
    if request.method == 'POST':
        rut_input = request.POST.get('rut', '').strip()
        pass_input = request.POST.get('password', '').strip()

        # Atajos rápidos para desarrollo
        if rut_input == 'admin' and pass_input == 'admin123':
            return redirect('admin_inicio')
        if rut_input == 'user' and pass_input == 'user123':
            return redirect('inicioU')

        # Lógica real validando en AWS
        try:
            # Nota: Asegúrate de que el campo en tu modelo se llame 'contrasena' o 'contraseña' según el inspectdb
            usuario = Usuario.objects.get(rut=rut_input, contrasena=pass_input)
            es_admin = Administrador.objects.filter(usuario_rut=usuario).exists()
            if es_admin:
                return redirect('admin_inicio')
            else:
                return redirect('inicioU')
        except Usuario.DoesNotExist:
            error_msg = "RUT o contraseña incorrectos."

    return render(request, 'login.html', {'error': error_msg})