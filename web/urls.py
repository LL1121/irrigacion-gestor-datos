from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("cargar/", views.cargar_medicion, name="cargar"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("api/weekly-route/", views.get_weekly_route_data, name="weekly_route_data"),
    path("mapa/", views.weekly_route, name="weekly_route"),
    path("api/docs/", views.api_docs, name="api_docs"),
    path("exportar/", views.exportar_csv, name="exportar_csv"),
    
    # Admin Panel (Custom UI)
    path("gestion/usuarios/", views.admin_usuarios_view, name="admin_usuarios"),
    path("gestion/usuarios/crear/", views.admin_crear_usuario_view, name="admin_crear_usuario"),
    path("gestion/usuarios/<int:user_id>/editar/", views.admin_editar_usuario_view, name="admin_editar_usuario"),
    path("gestion/usuarios/<int:user_id>/eliminar/", views.admin_eliminar_usuario_view, name="admin_eliminar_usuario"),
    path("gestion/empresas/", views.admin_empresas_view, name="admin_empresas"),
    path("gestion/empresas/<int:user_id>/legajo/", views.admin_empresa_legajo_view, name="admin_empresa_legajo"),
    path("gestion/empresas/<int:user_id>/editar-perfil/", views.admin_editar_perfil_empresa_view, name="admin_editar_perfil_empresa"),
    path("gestion/empresas/<int:user_id>/mediciones/", views.admin_mediciones_empresa_view, name="admin_mediciones_empresa"),
    path("gestion/mediciones/<int:medicion_id>/validar/", views.admin_validar_medicion_view, name="admin_validar_medicion"),
    path("gestion/mediciones/<int:medicion_id>/eliminar/", views.admin_eliminar_medicion_view, name="admin_eliminar_medicion"),
]
