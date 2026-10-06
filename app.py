
import os
import gc
import time
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import g4f

app = Flask(__name__)

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--single-process")
    chrome_options.binary_location = "/usr/bin/chromium"
    
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(15)
    return driver

@app.route('/ask', methods=['POST'])
def handle_request():
    data = request.get_json() or {}
    prompt_input = data.get("url") or data.get("prompt") or data.get("text") or ""
    
    if not prompt_input:
        return jsonify({"status": "error", "message": "لم يتم إرسال أي نص."}), 200

    # 1. إذا كان المدخل رابط موقع -> استخدام Selenium لفتحه
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
                "response": f"تم جلب الصفحة بنجاح! عنوان الصفحة: {page_title}"
            }), 200
        except Exception as e:
            return jsonify({"status": "error", "response": f"خطأ متصفح: {str(e)}"}), 200
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            gc.collect()  # تنظيف الذاكرة فوراً

    # 2. إذا كان سؤالاً نصياً -> استخدام مكتبة g4f للإجابة المباشرة (بدون فتح Selenium لتوفير الذاكرة)
    else:
        try:
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
            try:
                # خيار احتياطي في حال ضغط السيرفرات
                response = g4f.ChatCompletion.create(
                    model=g4f.models.default,
                    messages=[{"role": "user", "content": prompt_input}],
                )
                return jsonify({
                    "status": "success",
                    "title": "إجابة المساعد الذكي",
                    "response": str(response)
                }), 200
            except Exception as backup_err:
                return jsonify({
                    "status": "error",
                    "response": f"حدث خطأ أثناء معالجة الطلب: {str(backup_err)}"
                }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
