from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
urlpatterns=[
    path('',views.home,name='home'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('investment/',views.investment,name='investment'),
    path('learning/',views.learning,name='learning'),
    path('loginuser/',views.loginuser,name='loginuser'),
    path('signup/',views.signup,name='signup'),
    path('logoutuser/',views.logoutuser,name='logoutuser'),
    path('delete_transaction/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('ai-chat/', views.ai_chat, name='ai-chat'),
    path("clear-chat/", views.clear_chat, name="clear_chat"),  # New route for clearing chat
     # Password reset views
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("password-reset-confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("password-reset-complete/", auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),
    path('export/pdf/', views.export_transactions_pdf, name='export_transactions_pdf'),

]