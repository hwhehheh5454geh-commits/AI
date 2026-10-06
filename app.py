
import os
import time
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    
    return webdriver.Chrome(service=service, options=chrome_options)

@app.route('/ask', methods=['POST'])
def handle_request():
    data = request.get_json() or {}
    prompt_input = data.get("url") or data.get("prompt") or data.get("text") or ""
    
    if not prompt_input:
        return jsonify({"status": "error", "message": "لم يتم إرسال أي نص."}), 400

    driver = None
    try:
        driver = get_driver()
        
        # 1. إذا كان المدخل رابط موقع مباشر -> افتحه واجلب عنوانه ونصه
        if prompt_input.startswith("http://") or prompt_input.startswith("https://"):
            driver.get(prompt_input)
            time.sleep(2)
            page_title = driver.title
            return jsonify({
                "status": "success",
                "title": page_title,
                "response": f"تم فتح الرابط بنجاح بواسطة المتصفح! عنوان الصفحة: {page_title}"
            })

        # 2. إذا كان سؤالاً نصياً -> افتح المتصفح على محرك الشات السحابي واطرح السؤال تلقائياً
        else:
            driver.get("https://duckduckgo.com/?q=DuckDuckGo+AI+Chat&ia=chat")
            
            # الانتظار والدخول للبحث التلقائي عبر المتصفح
            wait = WebDriverWait(driver, 15)
            search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
            search_box.clear()
            search_box.send_keys(prompt_input)
            search_box.send_keys(Keys.RETURN)
            
            time.sleep(4)
            
            page_title = driver.title
            body_text = driver.find_element(By.TAG_NAME, "body").text[:500]
            
            return jsonify({
                "status": "success",
                "title": page_title,
                "response": f"تم إجراء البحث التلقائي عبر المتصفح لـ: '{prompt_input}'.\n\nنتيجة المتصفح المباشرة:\n{body_text}"
            })

    except Exception as e:
        return jsonify({"status": "error", "message": f"خطأ أتمتة المتصفح: {str(e)}"}), 500
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
