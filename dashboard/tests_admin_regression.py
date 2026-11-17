from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from django.test import RequestFactory, SimpleTestCase

from . import views


class AdminAfterPullTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_demo_login_opens_admin_session(self):
        request = self.factory.post(
            "/login/", {"rut": "admin", "password": "admin123"}
        )
        request.session = {}

        response = views.login_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/administrador/inicio/")
        self.assertTrue(request.session.get("es_admin"))

    def test_database_admin_login_opens_admin_session(self):
        request = self.factory.post(
            "/login/", {"rut": "12-3", "password": "clave"}
        )
        request.session = {}
        with patch("dashboard.views.Usuario") as user_model, patch(
            "dashboard.views.Administrador"
        ) as admin_model:
            user_model.objects.get.return_value = SimpleNamespace(rut="12-3")
            admin_model.objects.filter.return_value.exists.return_value = True

            response = views.login_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/administrador/inicio/")
        self.assertTrue(request.session.get("es_admin"))
        self.assertEqual(request.session.get("admin_rut"), "12-3")

    def test_admin_users_come_from_database(self):
        request = self.factory.get("/administrador/usuarios/")
        row = {
            "rut": "12-3", "nombre": "Ana", "apellidopaterno": "Soto",
            "apellidomaterno": "Pérez", "correo": "ana@example.com",
            "telefono": 123456789, "estado": 1,
        }
        with patch("dashboard.views.Usuario") as user_model, patch(
            "dashboard.views.render"
        ) as render:
            user_model.objects.values.return_value.order_by.return_value = [row]

            views.admin_usuarios(request)

        users = render.call_args.args[2]["users"]
        self.assertEqual(users[0]["rut"], "12-3")
        self.assertEqual(users[0]["telefono"], 123456789)

    def test_admin_messages_require_admin_session(self):
        request = self.factory.get("/administrador/mensajes/")
        request.session = {}
        with patch("dashboard.views.Mensaje"), patch("dashboard.views.render"):
            response = views.admin_mensajes(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/")

    def test_demo_admin_can_send_message(self):
        request = self.factory.post(
            "/administrador/mensajes/",
            {"receptor_rut": "12-3", "contenido": "Te ayudo"},
        )
        request.session = {"es_admin": True}
        with patch("dashboard.views.Usuario") as user_model, patch(
            "dashboard.views.Mensaje"
        ) as message_model, patch("dashboard.views.messages"), patch(
            "dashboard.views.cache"
        ):
            user_model.objects.filter.return_value.exists.return_value = True
            response = views.admin_mensajes(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn("chat=12-3", response.url)
        self.assertEqual(message_model.objects.create.call_args.kwargs["rut1"], "admin-demo")
        self.assertEqual(message_model.objects.create.call_args.kwargs["rut2"], "12-3")

    def test_admin_can_edit_database_user(self):
        request = self.factory.post(
            "/administrador/usuarios/",
            {
                "accion": "editar", "rut": "12-3", "nombre": "Ana",
                "apellidopaterno": "Soto", "apellidomaterno": "Pérez",
                "correo": "ana@example.com", "telefono": "123456789",
                "estado": "Suspendido",
            },
        )
        user = MagicMock()
        with patch("dashboard.views.Usuario") as user_model, patch(
            "dashboard.views.messages"
        ):
            user_model.objects.filter.return_value.first.return_value = user
            response = views.admin_usuarios(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(user.estado, 0)
        user.save.assert_called_once()

    def test_admin_can_create_demo_notification(self):
        request = self.factory.post(
            "/administrador/notificaciones/",
            {"accion": "crear", "tipo": "Reporte", "mensaje": "Revisar caso"},
        )
        request.session = {"es_admin": True}
        with patch("dashboard.views.Notificacion") as notification_model, patch(
            "dashboard.views.messages", create=True
        ), patch("dashboard.views.render"):
            response = views.admin_notificaciones(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/administrador/notificaciones/")
        self.assertEqual(
            notification_model.objects.create.call_args.kwargs["rut"],
            "admin-demo",
        )
