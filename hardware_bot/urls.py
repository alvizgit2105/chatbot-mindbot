from django.contrib import admin
from django.urls import path
from chat.views import chat_response, chat_page, upload_file  # ✅ Include upload view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chat/', chat_response),     # ✅ Handles chatbot API requests
    path('upload/', upload_file),     # ✅ Handles file/image uploads
    path('', chat_page),              # ✅ Loads the chat interface at http://localhost:8000/
]