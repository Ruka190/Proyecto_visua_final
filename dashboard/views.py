from django.shortcuts import render, redirect
import json
from .models import Match, Cliente, Gusto, Notificacion, Usuario, Administrador

def inicioU(request):
    """USUARIO tarjetas de preferencia con datos base"""
    secciones = [
        {
            'id': 'valores',
            'titulo': 'Valores',
            'titulo_card': 'Conexión por Valores',
            'activo': True,
            'nombre': 'Elena',
            'edad': 26,
            'foto': 'usuario/img/elena.jpg',
            'items': ['Honestidad', 'Pasión por el arte', 'Amor por la familia'],
            'bio': 'Busco a alguien con quien compartir.',
            'porcentaje': '100%',
            'metrica': 'Afinidad<br>en valores',
        },
        {
            'id': 'hobie',
            'titulo': 'Hobbies',
            'titulo_card': 'Conexión por Hobbies',
            'activo': False,
            'nombre': 'Martina',
            'edad': 27,
            'foto': 'usuario/img/martina.jpg',
            'items': ['Fotografía analógica', 'Escalada en boulder', 'Tocar la guitarra'],
            'bio': 'Alguien para salir a sacar fotos los domingos.',
            'porcentaje': '88%',
            'metrica': 'Afinidad<br>en hobbies',
        },
        {
            'id': 'gustos',
            'titulo': 'Gustos',
            'titulo_card': 'Conexión por Gustos',
            'activo': False,
            'nombre': 'Camila',
            'edad': 25,
            'foto': 'usuario/img/camila.jpg',
            'items': ['Café filtrado de especialidad', 'Cine independiente', 'Música synth-pop'],
            'bio': 'Fan del café y de compartir buenas charlas.',
            'porcentaje': '94%',
            'metrica': 'Afinidad<br>en gustos',
        },
        {
            'id': 'experiencias',
            'titulo': 'Experiencias',
            'titulo_card': 'Conexión por Experiencias',
            'activo': False,
            'nombre': 'Daniela',
            'edad': 29,
            'foto': 'usuario/img/daniela.jpg',
            'items': ['Acampar en la cordillera', 'Viajar solo como mochilero', 'Voluntariado ambiental'],
            'bio': 'Buscando compañeros de ruta y nuevas historias.',
            'porcentaje': '91%',
            'metrica': 'Afinidad<br>en experiencias',
        },
    ]

    return render(request, 'usuario/inicioU.html', {'secciones': secciones})



def perfilU(request):
    # Datos simulados (mock) para diseñar el frontend sin base de datos
    perfil = {
        'nombre': 'Javier',
        'edad': 21,
        'bio': 'Me considero un artista, chistoso, explorador y sobre todo abierto a nuevas experiencias...',
        'genero': 'Hombre',
        'ocupacion': 'Estudiante',
        'nacionalidad': 'Chile',
        'orientacion_sexual': 'Heterosexual',
        'religion': 'Agnóstico',
        'intereses': [
            {'nombre': 'Escalar'},
            {'nombre': 'Dibujar'},
            {'nombre': 'Explorar'},
            {'nombre': 'Dormir'},
        ],
        'fotos': ['usuario/img/javier2.jpg'],
    }

    total_fotos = len(perfil['fotos'])
    slots_disponibles = max(0, 6 - total_fotos)

    context = {
        'perfil': perfil,
        'slots_restantes': range(slots_disponibles),
    }
    return render(request, 'usuario/perfilU.html', context)

def graficosU(request):
    perfil_mock = {
        'nombre': 'Javier',
        'edad': 24,
    }

    # 1. Matches (Dona) -> REAL DESDE AWS
    matches_reales = Match.objects.filter(estado=1).count()
    no_matches_reales = Match.objects.filter(estado=0).count()
    
    chart_payload = {
        'labels': ['Match', 'No Match'],
        'data': [matches_reales, no_matches_reales]
    }

    # 2. Tiempo en la app (Falso / Mock)
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

    # 3. Arquetipo de matches (Falso / Mock)
    arquetipo_payload = {
        'orientacion': {
            'labels': ['Heterosexual', 'Bisexual', 'Homosexual', 'Otro'],
            'data': [11, 6, 3, 2],
            'label': 'Matches por orientación'
        },
        'edad': {
            'labels': ['18-21 años', '22-25 años', '26-29 años', '30+ años'],
            'data': [4, 12, 5, 1],
            'label': 'Matches por rango de edad'
        },
        'profesion': {
            'labels': ['Ingeniería/Tech', 'Salud', 'Diseño/Artes', 'Educación', 'Otros'],
            'data': [9, 5, 4, 3, 1],
            'label': 'Matches por área profesional'
        },
        'nacionalidad': {
            'labels': ['Chilena', 'Venezolana', 'Colombiana', 'Argentina', 'Otras'],
            'data': [14, 4, 2, 1, 1],
            'label': 'Matches por nacionalidad'
        },
        'religion': {
            'labels': ['Agnóstico/Ateo', 'Católico', 'Cristiano', 'Espiritual', 'Otro'],
            'data': [10, 6, 3, 2, 1],
            'label': 'Matches por creencias'
        }
    }

    # 4. Radar de Afinidad (Falso / Mock)
    radar_afinidad_payload = {
        'categorias': [
            'Vida en Casa',
            'Vida Social',
            'Cultura & Ocio',
            'Entorno & Movilidad',
            'Metas & Estilo de Vida'
        ],
        'gustos_data': [85, 65, 90, 45, 75],
        'disgustos_data': [30, 70, 20, 60, 40],
        'detalles_gustos': {
            'Vida en Casa': ['Series & Películas', 'Videojuegos', 'Cocinar juntos'],
            'Vida Social': ['Juntadas tranquilas', 'Ir por café', 'Paseos urbanos'],
            'Cultura & Ocio': ['Música en vivo', 'Cine', 'Tecnología'],
            'Entorno & Movilidad': ['Parques al aire libre', 'Caminar por la ciudad'],
            'Metas & Estilo de Vida': ['Desarrollo profesional', 'Vivir sin prisa']
        },
        'detalles_disgustos': {
            'Vida en Casa': ['Desorden extremo', 'Ruido excesivo al descansar'],
            'Vida Social': ['Bares repletos / aglomeraciones', 'Llegar tarde'],
            'Cultura & Ocio': ['Conversaciones superficiales', 'Spoilers de series'],
            'Entorno & Movilidad': ['Tacos / Tráfico vehicular', 'Calor extremo'],
            'Metas & Estilo de Vida': ['Falta de ambición', 'Presión social']
        }
    }

    # Unificamos todo en un solo diccionario context
    context = {
        'perfil': perfil_mock,
        'chart_payload': chart_payload,
        'tiempo_payload': tiempo_payload,
        'arquetipo_payload': arquetipo_payload,
        'radar_afinidad_payload': radar_afinidad_payload,
    }
    
    return render(request, 'usuario/graficosU.html', context)





def administrador(request):
    return render(request, 'admin/administrador.html')

def admin_inicio(request):
    labels = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]
    datasets = [{
            "data": [120, 180, 90, 220, 150],
            "borderColor": "#B94448",
            "backgroundColor": "#B944482E",
            "tension": 0.2,
            "fill": True,
        }]

    matches_totales = 20012
    return render(request, "admin/inicio.html", {
        "clientes_registrados": 20, ##
        "matches_totales": f"{matches_totales:,}".replace(",", "."), ##
        "reportes_usuarios": 33, ##s
        "notificacion_pendiente": 67, ##
        "labels_json": json.dumps(labels, ensure_ascii=False),
        "datasets_json": json.dumps(datasets, ensure_ascii=False),
    })

from datetime import date
import json

def admin_estadisticas(request):
    # 1. Histórico de Matches: ¡Este SÍ es real porque la tabla MATCH está llena!
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