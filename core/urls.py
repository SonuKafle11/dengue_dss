from django.urls import path
from . import views

urlpatterns = [

    # Root
    path('', views.index, name='index'),

    # Auth
    path('register/', views.register,    name='register'),
    path('login/',    views.login_view,  name='login'),
    path('logout/',   views.logout_view, name='logout'),

    # Admin auth
    path('admin-login/',  views.admin_login,  name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),

    # Patient
    path('patient/',
         views.patient_dashboard,
         name='patient_dashboard'),

    path('patient/form/',
         views.patient_form,
         name='patient_form'),

    path('patient/result/<uuid:record_id>/',
         views.patient_result,
         name='patient_result'),

    # Doctor
    path('doctor/',
         views.doctor_dashboard,
         name='doctor_dashboard'),

    path('doctor/patient/<uuid:record_id>/',
         views.doctor_patient_detail,
         name='doctor_patient_detail'),

    path('doctor/result/<uuid:record_id>/',
         views.doctor_prediction_result,
         name='doctor_prediction_result'),

    # Admin
    path('admin-panel/',
         views.admin_dashboard,
         name='admin_dashboard'),

    path('admin-panel/delete-user/<str:user_id>/',
         views.admin_delete_user,
         name='admin_delete_user'),

    path('admin-panel/delete-record/<uuid:record_id>/',
         views.admin_delete_record,
         name='admin_delete_record'),

    path('admin-panel/dataset-json/',
         views.admin_dataset_json,
         name='admin_dataset_json'),

]