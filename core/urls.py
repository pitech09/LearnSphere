from django.urls import path

from .views import (
    home_view,
    post_add,
    edit_post,
    delete_post,
    session_list_view,
    session_add_view,
    session_update_view,
    session_delete_view,
    dashboard_view,
    class_list_view,
    class_add_view,
    class_update_view,
    class_delete_view,

)


urlpatterns = [
    # Accounts url
    path("", home_view, name="home"),
    path("add_item/", post_add, name="add_item"),
    path("item/<int:pk>/edit/", edit_post, name="edit_post"),
    path("item/<int:pk>/delete/", delete_post, name="delete_post"),
    path("session/", session_list_view, name="session_list"),
    path("session/add/", session_add_view, name="add_session"),
    path("session/<int:pk>/edit/", session_update_view, name="edit_session"),
    path("session/<int:pk>/delete/", session_delete_view, name="delete_session"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("class/", class_list_view, name="class_list"),
    path("class/add/", class_add_view, name="add_class"),
    path("class/<int:pk>/edit/", class_update_view, name="edit_class"),
    path("class/<int:pk>/delete/", class_delete_view, name="delete_class"),
]
