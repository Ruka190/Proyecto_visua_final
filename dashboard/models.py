# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Administrador(models.Model):
    idadministrador = models.CharField(db_column='idAdministrador', primary_key=True, max_length=100)  # Field name made lowercase.
    nivelacceso = models.IntegerField(db_column='nivelAcceso')  # Field name made lowercase.
    fechaasignacion = models.DateField(db_column='fechaAsignacion', blank=True, null=True)  # Field name made lowercase.
    dineroacumulado = models.FloatField(db_column='dineroAcumulado')  # Field name made lowercase.
    usuario_rut = models.OneToOneField('Usuario', models.DO_NOTHING, db_column='USUARIO_rut')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ADMINISTRADOR'


class Cliente(models.Model):
    idcliente = models.CharField(db_column='idCliente', primary_key=True, max_length=100)  # Field name made lowercase.
    biografia = models.CharField(max_length=200)
    sexo = models.CharField(max_length=50)
    orientacionsexual = models.CharField(db_column='orientacionSexual', max_length=100)  # Field name made lowercase.
    nacionalidad = models.CharField(max_length=100, blank=True, null=True)
    ocupacionlaboral = models.CharField(db_column='ocupacionLaboral', max_length=100, blank=True, null=True)  # Field name made lowercase.
    fechanacimiento = models.DateField(db_column='fechaNacimiento')  # Field name made lowercase.
    usuario_rut = models.OneToOneField('Usuario', models.DO_NOTHING, db_column='USUARIO_rut')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CLIENTE'


class Disgusto(models.Model):
    idgusto = models.CharField(db_column='idGusto', primary_key=True, max_length=100)  # Field name made lowercase.
    rut = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200)
    valor = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'DISGUSTO'


class Foto(models.Model):
    idfoto = models.CharField(db_column='idFoto', primary_key=True, max_length=100)  # Field name made lowercase.
    rut = models.CharField(max_length=100)
    urlimagen = models.CharField(db_column='urlImagen', max_length=100)  # Field name made lowercase.
    esprincipal = models.IntegerField(db_column='esPrincipal')  # Field name made lowercase.
    cliente_idcliente = models.ForeignKey(Cliente, models.DO_NOTHING, db_column='CLIENTE_idCliente')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'FOTO'


class Gusto(models.Model):
    idgusto = models.CharField(db_column='idGusto', primary_key=True, max_length=100)  # Field name made lowercase.
    rut = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200)
    valor = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'GUSTO'


class Match(models.Model):
    idmatch = models.CharField(db_column='idMatch', primary_key=True, max_length=100)  # Field name made lowercase.
    cliente1rut = models.CharField(db_column='cliente1Rut', max_length=100)  # Field name made lowercase.
    cliente2rut = models.CharField(db_column='cliente2Rut', max_length=100)  # Field name made lowercase.
    fechamatch = models.DateField(db_column='fechaMatch')  # Field name made lowercase.
    estado = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'MATCH'


class Mensaje(models.Model):
    idmensaje = models.CharField(db_column='idMensaje', primary_key=True, max_length=100)  # Field name made lowercase.
    rut1 = models.CharField(max_length=100)
    rut2 = models.CharField(max_length=100)
    contenido = models.CharField(max_length=200)
    fechaenvio = models.DateField(db_column='fechaEnvio')  # Field name made lowercase.
    leido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'MENSAJE'


class Notificacion(models.Model):
    idnotificacion = models.CharField(db_column='idNotificacion', primary_key=True, max_length=100)  # Field name made lowercase.
    rut = models.CharField(max_length=100)
    informacion = models.CharField(max_length=200)
    fecha = models.DateField()
    estado = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'NOTIFICACION'



class Usuario(models.Model):
    rut = models.CharField(primary_key=True, max_length=100)
    nombre = models.CharField(max_length=100)
    apellidopaterno = models.CharField(db_column='apellidoPaterno', max_length=100)  # Field name made lowercase.
    apellidomaterno = models.CharField(db_column='apellidoMaterno', max_length=100)  # Field name made lowercase.
    correo = models.CharField(max_length=300)
    telefono = models.IntegerField()
    fechaingreso = models.DateField(db_column='fechaIngreso')  # Field name made lowercase.
    contrasena = models.CharField(max_length=100)
    estado = models.IntegerField()
    administrador_idadministrador = models.OneToOneField(Administrador, models.DO_NOTHING, db_column='ADMINISTRADOR_idAdministrador', blank=True, null=True)  # Field name made lowercase.
    mensaje_idmensaje = models.ForeignKey(Mensaje, models.DO_NOTHING, db_column='MENSAJE_idMensaje', blank=True, null=True)  # Field name made lowercase.
    notificacion_idnotificacion = models.ForeignKey(Notificacion, models.DO_NOTHING, db_column='NOTIFICACION_idNotificacion', blank=True, null=True)  # Field name made lowercase.
    cliente_idcliente = models.OneToOneField(Cliente, models.DO_NOTHING, db_column='CLIENTE_idCliente', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'USUARIO'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class InicioPerfil(models.Model):
    id = models.BigAutoField(primary_key=True)
    display_name = models.CharField(max_length=80)
    ciudad = models.CharField(max_length=80)
    edad = models.PositiveIntegerField(blank=True, null=True)
    biografia = models.TextField()
    valores = models.CharField(max_length=255)
    hobbies = models.CharField(max_length=255)
    gustos = models.CharField(max_length=255)
    user = models.OneToOneField(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'inicio_perfil'


class InicioPreferencia(models.Model):
    id = models.BigAutoField(primary_key=True)
    edad_min = models.PositiveIntegerField()
    edad_max = models.PositiveIntegerField()
    distancia_km = models.PositiveIntegerField()
    intereses = models.CharField(max_length=255)
    busco = models.CharField(max_length=255)
    perfil = models.OneToOneField(InicioPerfil, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'inicio_preferencia'
