from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import cohere
import traceback
import re
import os
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
cohere_api_key = os.getenv("COHERE_API_KEY")

# ✅ View to render the chat interface page
def chat_page(request):
    return render(request, 'chat/chat.html')

# ✅ View to handle chatbot API response
@csrf_exempt
def chat_response(request):
    if request.method == 'POST':
        try:
            print("🔧 Starting chat_response")
            data = json.loads(request.body)
            user_message = data.get('message', '')
            print("📩 User message received:", user_message)

            # ✅ Initialize Cohere client
            client = cohere.Client(cohere_api_key)

            # ✅ Use trial-accessible model
            print("🧠 Sending message to Cohere Chat API")
            response = client.chat(
                model='command-nightly',
                message=user_message,
                temperature=0.7
            )

            # ✅ Format bot reply with HTML line breaks and markdown
            raw_reply = response.text.strip()
            formatted_reply = raw_reply.replace("\\n", "\n").replace("\n", "<br>")
            formatted_reply = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", formatted_reply)
            formatted_reply = re.sub(r"### (.*?)<br>", r"<h5>\1</h5>", formatted_reply)
            formatted_reply = re.sub(r"- (.*?)<br>", r"<li>\1</li>", formatted_reply)
            print("💬 Bot reply:", formatted_reply)
            return JsonResponse({'reply': formatted_reply})

        except Exception as e:
            print("⚠️ An error occurred:")
            traceback.print_exc()
            return JsonResponse({'reply': 'Sorry, something went wrong.'})

# ✅ View to handle file uploads and analysis
@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        try:
            uploaded_files = request.FILES.getlist('file')
            saved_files = []
            replies = []

            # ✅ Create uploads directory if it doesn't exist
            upload_dir = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(upload_dir, exist_ok=True)

            for f in uploaded_files:
                save_path = os.path.join(upload_dir, f.name)
                with open(save_path, 'wb+') as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)
                saved_files.append(f.name)

                # ✅ Analyze based on file type
                ext = os.path.splitext(f.name)[1].lower()
                content = ""

                if ext == '.txt':
                    with open(save_path, 'r', encoding='utf-8') as file:
                        content = file.read()

                elif ext == '.pdf':
                    import pdfplumber
                    with pdfplumber.open(save_path) as pdf:
                        content = "\n".join(page.extract_text() or "" for page in pdf.pages)

                elif ext == '.docx':
                    from docx import Document
                    doc = Document(save_path)
                    content = "\n".join([para.text for para in doc.paragraphs])

                elif ext in ['.py', '.js', '.html']:
                    with open(save_path, 'r', encoding='utf-8') as file:
                        content = file.read()

                elif ext in ['.jpg', '.jpeg', '.png']:
                    content = f"This is an image file named {f.name}. Please describe or analyze it."

                else:
                    content = f"Uploaded file '{f.name}' is not supported for analysis."

                # ✅ Send content to Cohere
                client = cohere.Client(cohere_api_key)
                response = client.chat(
                    model='command-nightly',
                    message=f"Analyze this file:\n{content[:3000]}",
                    temperature=0.7
                )

                # ✅ Format reply with markdown conversion
                raw_reply = response.text.strip()
                formatted_reply = raw_reply.replace("\\n", "\n").replace("\n", "<br>")
                formatted_reply = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", formatted_reply)
                formatted_reply = re.sub(r"### (.*?)<br>", r"<h5>\1</h5>", formatted_reply)
                formatted_reply = re.sub(r"- (.*?)<br>", r"<li>\1</li>", formatted_reply)
                replies.append(formatted_reply)

            print("📁 Files uploaded:", saved_files)
            return JsonResponse({'status': 'success', 'files': saved_files, 'replies': replies})

        except Exception as e:
            print("⚠️ Upload error:")
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': 'Upload failed.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)