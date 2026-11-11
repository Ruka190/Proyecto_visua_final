import os
import random
from datetime import date, timedelta
import django

# 1. Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BeyondDate.settings')
django.setup()

from dashboard.models import Usuario, Cliente, Gusto, Disgusto, Match, Mensaje, Notificacion

def poblar_base_datos():
    print("🚀 Conectando a AWS RDS (beyonddatedb) e iniciando carga masiva...")

    # Catálogos de datos realistas para los gráficos
    nombres_f = ['Sofía', 'Valentina', 'Camila', 'Elena', 'Martina', 'Daniela', 'Isidora', 'Florencia', 'Catalina', 'ignacia', 'Antonia', 'Fernanda', 'Javiera', 'Constanza', 'Francisca']
    nombres_m = ['Javier', 'Matías', 'Tomás', 'Nicolás', 'Sebastián', 'Diego', 'Lucas', 'Benjamín', 'Martín', 'Vicente', 'Joaquín', 'Maximiliano', 'Cristóbal', 'Agustín', 'Felipe']
    apellidos = ['Morales', 'González', 'Muñoz', 'Rojas', 'Díaz', 'Pérez', 'Soto', 'Contreras', 'Silva', 'Martínez', 'Sepúlveda', 'Fuentes', 'Torres', 'Araya', 'Valdivia']

    orientaciones = ['Heterosexual', 'Bisexual', 'Homosexual', 'Otro']
    pesos_orientacion = [0.55, 0.25, 0.15, 0.05]

    nacionalidades = ['Chilena', 'Venezolana', 'Colombiana', 'Argentina', 'Otras']
    pesos_nacionalidad = [0.65, 0.14, 0.09, 0.08, 0.04]

    profesiones = ['Ingeniería/Tech', 'Salud', 'Diseño/Artes', 'Educación', 'Otros']
    pesos_profesion = [0.35, 0.25, 0.20, 0.12, 0.08]

    # Los 5 Pilares del Pentágono del Radar de Afinidad
    catalogo_gustos = {
        'Valores': [
            'Honestidad y transparencia', 'Empatía activa', 'Comunicación asertiva',
            'Lealtad y compromiso', 'Responsabilidad afectiva'
        ],
        'Hobbies': [
            'Escalar en boulder', 'Dibujar e ilustrar', 'Fotografía analógica',
            'Tocar la guitarra', 'Leer ciencia ficción'
        ],
        'Dinámica Social': [
            'Juntadas íntimas en casa', 'Planes al aire libre', 'Café de especialidad de sobremesa',
            'Caminar y explorar la ciudad', 'Conversaciones profundas de madrugada'
        ],
        'Lenguaje del Amor': [
            'Tiempo de calidad juntos', 'Palabras de afirmación', 'Actos de servicio cotidianos',
            'Contacto físico afectuoso', 'Detalles significativos y sorpresas'
        ],
        'Metas & Futuro': [
            'Crecimiento profesional constante', 'Buscar una relación estable y a largo plazo',
            'Viajar y conocer el mundo', 'Aprender nuevos idiomas y habilidades',
            'Estabilidad e independencia financiera'
        ]
    }

    catalogo_disgustos = {
        'Valores': [
            'Falta de sinceridad', 'Desinterés afectivo', 'Egoísmo y soberbia',
            'Irresponsabilidad emocional', 'Falta de empatía con el entorno'
        ],
        'Hobbies': [
            'Sedentarismo extremo', 'Falta absoluta de curiosidad', 'Pasar todo el día en piloto automático',
            'Rechazo a aprender cosas nuevas', 'Cero conexión con el arte'
        ],
        'Dinámica Social': [
            'Bares repletos con ruido ensordecedor', 'Aglomeraciones agobiantes',
            'Conversaciones superficiales eternas', 'Gente impuntual sin aviso previo',
            'Ambientes cargados de drama innecesario'
        ],
        'Lenguaje del Amor': [
            'Falta de reciprocidad afectiva', 'Indiferencia ante los logros del otro',
            'Invalidar emociones o minimizarlas', 'Falta de contacto visual y presencia',
            'Frialdad en momentos importantes'
        ],
        'Metas & Futuro': [
            'Falta total de proyección o ambición', 'Estancamiento personal voluntario',
            'Miedo irracional al compromiso', 'Vivir sin propósito ni metas claras',
            'Conformismo excesivo'
        ]
    }

    ruts_creados = []
    hoy = date.today()

    # 1. Crear el usuario principal de prueba (Javier) + 39 perfiles adicionales (40 en total)
    print("👤 Creando 40 Usuarios y Clientes en AWS RDS...")
    for i in range(1, 41):
        rut_str = f"{18000000 + i * 12345}-{i % 9}"
        id_cli = f"CLI-{i:03d}"

        if i == 1:
            nombre = 'Javier'
            sexo = 'Masculino'
            edad_anios = 24
        else:
            es_mujer = (i % 2 == 0)
            nombre = random.choice(nombres_f if es_mujer else nombres_m)
            sexo = 'Femenino' if es_mujer else 'Masculino'
            # Distribución de edades para los rangos: 18-21, 22-25, 26-29, 30+
            edad_anios = random.choices([19, 20, 23, 24, 25, 27, 28, 31, 33], weights=[10, 10, 20, 20, 15, 10, 8, 4, 3])[0]

        ap_pat = random.choice(apellidos)
        ap_mat = random.choice(apellidos)
        fecha_nac = hoy - timedelta(days=edad_anios * 365 + random.randint(0, 300))
        fecha_ing = hoy - timedelta(days=random.randint(5, 180))

        orientacion = random.choices(orientaciones, weights=pesos_orientacion)[0]
        nacionalidad = random.choices(nacionalidades, weights=pesos_nacionalidad)[0]
        profesion = random.choices(profesiones, weights=pesos_profesion)[0]

        # Paso A: Insertar o actualizar Usuario sin cliente_idcliente aún
        usuario_obj, _ = Usuario.objects.update_or_create(
            rut=rut_str,
            defaults={
                'nombre': nombre,
                'apellidopaterno': ap_pat,
                'apellidomaterno': ap_mat,
                'correo': f"{nombre.lower()}.{ap_pat.lower()}{i}@beyonddate.cl",
                'telefono': 900000000 + i * 111,
                'fechaingreso': fecha_ing,
                'contrasena': 'hashed_password_123',
                'estado': 1,
                'cliente_idcliente': None
            }
        )

        # Paso B: Insertar o actualizar Cliente apuntando al Usuario
        cliente_obj, _ = Cliente.objects.update_or_create(
            idcliente=id_cli,
            defaults={
                'biografia': f"Hola, soy {nombre}. Busco conexiones auténticas y compartir buenos momentos.",
                'sexo': sexo,
                'orientacionsexual': orientacion,
                'nacionalidad': nacionalidad,
                'ocupacionlaboral': profesion,
                'fechanacimiento': fecha_nac,
                'usuario_rut': usuario_obj
            }
        )

        # Paso C: Enlazar cliente_idcliente en Usuario
        usuario_obj.cliente_idcliente = cliente_obj
        usuario_obj.save()
        ruts_creados.append(rut_str)

    # 2. Poblar GUSTO y DISGUSTO con los 5 pilares y puntajes numéricos en 'valor'
    print("✨ Insertando Gustos y Disgustos en los 5 Pilares...")
    contador_g = 1
    contador_d = 1

    for rut_u in ruts_creados[:20]:  # Asignamos gustos detallados a los primeros 20 usuarios
        for categoria, lista_items in catalogo_gustos.items():
            seleccionados = random.sample(lista_items, k=3)
            for item_desc in seleccionados:
                # Guardamos un puntaje de afinidad entre 75 y 98 en el campo 'valor'
                puntaje = str(random.randint(75, 98))
                Gusto.objects.update_or_create(
                    idgusto=f"GUS-{contador_g:04d}",
                    defaults={
                        'rut': rut_u,
                        'descripcion': item_desc,
                        'valor': puntaje,
                        'categoria': categoria
                    }
                )
                contador_g += 1

        for categoria, lista_items in catalogo_disgustos.items():
            seleccionados = random.sample(lista_items, k=2)
            for item_desc in seleccionados:
                puntaje_dis = str(random.randint(15, 45))
                Disgusto.objects.update_or_create(
                    idgusto=f"DIS-{contador_d:04d}",
                    defaults={
                        'rut': rut_u,
                        'descripcion': item_desc,
                        'valor': puntaje_dis,
                        'categoria': categoria
                    }
                )
                contador_d += 1

    # 3. Poblar tabla MATCH (120 registros entre exitosos estado=1 y rechazados estado=0)
    print("❤️ Creando 120 registros de Match...")
    rut_principal = ruts_creados[0]
    for m in range(1, 121):
        if m <= 35:
            # Matches del usuario principal con otros perfiles
            c1 = rut_principal
            c2 = ruts_creados[m]
        else:
            c1, c2 = random.sample(ruts_creados, 2)

        # 68% de probabilidad de Match exitoso (estado=1) para que el gráfico luzca atractivo
        estado_match = 1 if random.random() < 0.68 else 0
        fecha_m = hoy - timedelta(days=random.randint(0, 90))

        Match.objects.update_or_create(
            idmatch=f"MAT-{m:04d}",
            defaults={
                'cliente1rut': c1,
                'cliente2rut': c2,
                'fechamatch': fecha_m,
                'estado': estado_match
            }
        )

    # 4. Poblar MENSAJE y NOTIFICACION para dar actividad real temporal
    print("💬 Creando Mensajes y Notificaciones...")
    frases_chat = [
        "¡Hola! Vi que coincidimos en casi todos los valores.",
        "¡Qué buena! También me encanta escalar los fines de semana.",
        "¿Conoces algún buen café de especialidad por Providencia?",
        "Me pareció súper interesante tu perfil, ¿cómo va tu semana?",
        "¡Totalmente de acuerdo! La comunicación asertiva lo es todo."
    ]
    for msg_i in range(1, 81):
        emisor, receptor = random.sample(ruts_creados[:15], 2)
        fecha_env = hoy - timedelta(days=random.randint(0, 30))
        Mensaje.objects.update_or_create(
            idmensaje=f"MSG-{msg_i:04d}",
            defaults={
                'rut1': emisor,
                'rut2': receptor,
                'contenido': random.choice(frases_chat),
                'fechaenvio': fecha_env,
                'leido': random.choice([0, 1])
            }
        )

    for not_i in range(1, 41):
        Notificacion.objects.update_or_create(
            idnotificacion=f"NOT-{not_i:04d}",
            defaults={
                'rut': random.choice(ruts_creados[:10]),
                'informacion': "Tienes una nueva conexión con más de 85% de afinidad.",
                'fecha': hoy - timedelta(days=random.randint(0, 15)),
                'estado': random.choice([0, 1])
            }
        )

    print("✅ ¡Carga masiva completada con éxito en AWS RDS!")

if __name__ == '__main__':
    poblar_base_datos()