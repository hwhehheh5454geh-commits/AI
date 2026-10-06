
import os
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

app = Flask(__name__)

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    
    return webdriver.Chrome(service=service, options=chrome_options)

@app.route('/ask', methods=['POST'])
def handle_request():
    data = request.get_json() or {}
    
    # استلام النص سواء أرسله Lovable كـ url أو prompt أو text
    prompt_input = data.get("url") or data.get("prompt") or data.get("text") or ""
    
    if not prompt_input:
        return jsonify({"status": "error", "message": "لم يتم إرسال أي نص أو رابط."}), 400

    # الحالة الأولى: إذا كان المدخل رابط موقع، افتحه بواسطة Selenium
    if prompt_input.startswith("http://") or prompt_input.startswith("https://"):
        driver = None
        try:
            driver = get_driver()
            driver.get(prompt_input)
            page_title = driver.title
            return jsonify({
                "status": "success",
                "title": page_title,
                "response": f"تم جلب الصفحة بنجاح. عنوان الصفحة هو: {page_title}"
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
        finally:
            if driver:
                driver.quit()

    # الحالة الثانية: إذا كان المدخل سؤالاً أو دردشة نصية عادية
    else:
        # استجابة نموذجية للتأكد من نجاح الطلب
        reply = f"مرحباً! تلقيت طلبك: '{prompt_input}'. الخادم يعمل بنجاح وجاهز لتنفيذ الأوامر."
        return jsonify({
            "status": "success",
            "response": reply,
            "title": "إجابة المساعد"
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
