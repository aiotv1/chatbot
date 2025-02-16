from flask import Flask, render_template, request, jsonify
import requests
import logging
import os

# تهيئة Flask
app = Flask(__name__)

# إعداد تسجيل الأخطاء (Logging)
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s')

# قائمة لتخزين الرسائل السابقة
conversation_history = []

# تخزين مؤقت (Caching) للأسئلة الشائعة
faq_cache = {
    "what is a pc": "A **PC** (Personal Computer) is a general-purpose computer designed for individual use. It typically includes a processor, memory, storage, and input/output devices like a keyboard and mouse.",
    "how are you": "I'm just a program, so I don't have feelings, but thanks for asking! How can I assist you today?",
    "hi": "Hello! How can I help you today?",
    "hello": "Hi there! How can I assist you?",
    "date": "To get the current date, you can ask 'What is the date today?' or 'Tell me the date.'",
}

def get_current_date_from_web():
    try:
        # تعطيل التحقق من SSL مؤقتًا (غير موصى به إلا في حالات الاختبار)
        response = requests.get("http://worldtimeapi.org/api/timezone/Etc/UTC", verify=False)
        if response.status_code == 200:
            data = response.json()
            date_time = data["datetime"][:10]  # استخراج التاريخ فقط (YYYY-MM-DD)
            return f"Today's date is: {date_time}"
        else:
            logging.error(f"Error fetching date from worldtimeapi.org: {response.status_code}")
            return "Sorry, I couldn't fetch the current date."
    except Exception as e:
        logging.error(f"Exception while fetching date: {e}")
        return "Sorry, an error occurred while fetching the date."

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/send_message", methods=["POST"])
def send_message():
    user_input = request.form["user_input"].strip().lower()
    bot_response = handle_user_input(user_input)
    return jsonify({"user_input": user_input, "bot_response": bot_response})

def handle_user_input(user_input):
    # التحقق من الأسئلة الشائعة (FAQ) أولاً
    if user_input in faq_cache:
        return faq_cache[user_input]

    # إذا كان السؤال يتعلق بالتاريخ
    if "date" in user_input or "what is the date" in user_input:
        return get_current_date_from_web()

    # إذا لم يكن هناك إجابة مسبقة، نرسل الطلب إلى Gemini API
    return send_message_to_gemini(user_input)

def send_message_to_gemini(message):
    conversation_history.append({"role": "user", "parts": [{"text": message}]})
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": conversation_history
    }
    params = {
        "key": "AIzaSyByJMeVo9xbPAp_n-Iy1c5I8IBpD-lSLV8"  # استبدل بمفتاح API الخاص بك
    }
    try:
        # تعطيل التحقق من SSL مؤقتًا (غير موصى به إلا في حالات الاختبار)
        response = requests.post(url, headers=headers, json=data, params=params, verify=False)
        if response.status_code == 200:
            try:
                # التحقق من بنية الاستجابة
                bot_response = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                conversation_history.append({"role": "model", "parts": [{"text": bot_response}]})
                return bot_response
            except KeyError as e:
                logging.error(f"KeyError in Gemini API response: {e}")
                logging.error(f"Full response: {response.json()}")
                return "Sorry, I encountered an issue while processing your request."
        else:
            logging.error(f"Gemini API request failed: {response.status_code}, {response.text}")
            return "Sorry, an error occurred while processing your request."
    except Exception as e:
        logging.error(f"Exception while calling Gemini API: {e}")
        return "Sorry, an unexpected error occurred."

if __name__ == "__main__":
    app.run(debug=True)
