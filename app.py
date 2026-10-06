
import os
import time
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import g4f

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
    prompt_input = data.get("url") or data.get("prompt") or data.get("text") or ""
    
    if not prompt_input:
        return jsonify({"status": "error", "message": "لم يتم إرسال أي نص."}), 200

    # 1. إذا كان المدخل رابط موقع -> افتحه عبر Selenium
    if prompt_input.startswith("http://") or prompt_input.startswith("https://"):
        driver = None
        try:
            driver = get_driver()
            driver.get(prompt_input)
            time.sleep(2)
            page_title = driver.title
            return jsonify({
                "status": "success",
                "title": page_title,
                "response": f"تم جلب الصفحة بنجاح عبر المتصفح السحابي! عنوان الصفحة: {page_title}"
            }), 200
        except Exception as e:
            return jsonify({"status": "error", "response": f"خطأ متصفح: {str(e)}"}), 200
        finally:
            if driver:
                driver.quit()

    # 2. إذا كان سؤالاً نصياً -> جلب الإجابة من Gemini مباشرة تلقائياً
    else:
        try:
            # جلب الاستجابة من مزود Gemini
            response = g4f.ChatCompletion.create(
                model=g4f.models.gemini,
                messages=[{"role": "user", "content": prompt_input}],
            )
            
            return jsonify({
                "status": "success",
                "title": "إجابة Google Gemini",
                "response": str(response)
            }), 200
            
        except Exception as e:
            # خيار احتياطي عند حدوث أي ضغط على خوادم Gemini
            try:
                response = g4f.ChatCompletion.create(
                    model=g4f.models.default,
                    messages=[{"role": "user", "content": prompt_input}],
                )
                return jsonify({
                    "status": "success",
                    "title": "إجابة المساعد الذكي",
                    "response": str(response)
                }), 200
            except Exception as backup_error:
                return jsonify({
                    "status": "error",
                    "response": f"عذراً، تعذر جلب الإجابة حالياً: {str(backup_error)}"
                }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
