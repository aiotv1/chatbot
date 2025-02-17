from flask import Flask, render_template, request, jsonify
import requests

# تهيئة Flask
app = Flask(__name__)

# قائمة لتخزين الرسائل السابقة
conversation_history = []

# تعريف System Prompt مخصص
SYSTEM_PROMPT = """
أنت Ai-O 🌟، وهو نموذج ذكاء اصطناعي متقدم تم تطويره بواسطة AIO.
- مهمتك هي تقديم المساعدة والإجابة على أسئلة المستخدمين بطريقة منظمة ومختصرة ✨.
- استخدم الإيموجيز من Apple لإضافة لمسة ودية 🍎.
- إذا لم يطلب المستخدم تفاصيل إضافية، يجب أن تكون إجاباتك مختصرة وواضحة 💬.
- أنت متعدد الاستخدامات ويمكنك الإجابة عن أي موضوع: البرمجة 💻، الرياضيات 🧮، الطعام 🍕، العالم 🌍، التعلم 📚، دعم العملاء 👥، الدردشة العامة 💭، وأكثر من ذلك.
- إذا كنت غير متأكد من الإجابة، قل ذلك بصراحة 😊.
"""

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/send_message", methods=["POST"])
def send_message():
    user_input = request.form["user_input"]
    bot_response = send_message_to_gemini(user_input)
    return jsonify({"user_input": user_input, "bot_response": bot_response})

def send_message_to_gemini(message):
    global conversation_history

    # إضافة رسالة المستخدم إلى سجل المحادثة
    conversation_history.append({"role": "user", "parts": [{"text": message}]})

    # إضافة System Prompt في بداية المحادثة إذا كانت المحادثة فارغة
    if len(conversation_history) == 1:
        conversation_history.insert(0, {"role": "model", "parts": [{"text": SYSTEM_PROMPT}]})

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
        response = requests.post(url, headers=headers, json=data, params=params)
        if response.status_code == 200:
            try:
                # التحقق من بنية الاستجابة
                bot_response = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                # إضافة رد البوت إلى سجل المحادثة
                conversation_history.append({"role": "model", "parts": [{"text": bot_response}]})
                return bot_response
            except KeyError as e:
                # إذا كانت الاستجابة لا تحتوي على المفاتيح المتوقعة
                print(f"خطأ في بنية الاستجابة: {e}")
                print(f"الاستجابة الكاملة: {response.json()}")
                return "عذرًا، حدث خطأ في معالجة الرد. يرجى المحاولة لاحقًا. ❌"
        elif response.status_code == 400:
            # معالجة خطأ 400 (Bad Request)
            error_message = response.json().get("error", {}).get("message", "خطأ غير معروف.")
            print(f"خطأ 400: {error_message}")
            return f"عذرًا، حدث خطأ في الطلب. التفاصيل: {error_message} ❌"
        else:
            # معالجة الأخطاء الأخرى
            print(f"خطأ في الطلب: {response.status_code}, {response.text}")
            return f"عذرًا، حدث خطأ أثناء معالجة طلبك. (رمز الخطأ: {response.status_code}) ❌"
    except Exception as e:
        print(f"خطأ عام: {e}")
        return "عذرًا، حدث خطأ أثناء معالجة طلبك. ❌"

@app.route("/clear_context", methods=["POST"])
def clear_context():
    global conversation_history
    conversation_history = []  # مسح السياق الحالي
    return jsonify({"status": "success", "message": "تم مسح السياق بنجاح."})

if __name__ == "__main__":
    app.run(debug=True)
