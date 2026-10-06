
import os
import gc
import time
import subprocess
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

app = Flask(__name__)

def kill_chromium_processes():
    """إنهاء أي عمليات معلقة لـ Chromium لتفريغ الذاكرة تماماً"""
    try:
        subprocess.run(["pkill", "-f", "chromium"], check=False)
        subprocess.run(["pkill", "-f", "chromedriver"], check=False)
    except Exception:
        pass

def get_driver():
    # تنظيف الذاكرة قبل فتح متصفح جديد
    kill_chromium_processes()
    gc.collect()

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # إيقاف الصور لتسريع المتصفح
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
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

    driver = None
    try:
        driver = get_driver()

        # الحالة الأولى: إذا كان المدخل رابط موقع مباشر
        if prompt_input.startswith("http://") or prompt_input.startswith("https://"):
            driver.get(prompt_input)
            time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            for script in soup(["script", "style", "nav", "footer"]):
                script.extract()
            
            page_title = driver.title or "صفحة ويب"
            clean_text = soup.get_text(separator=' ', strip=True)[:1000]
            
            return jsonify({
                "status": "success",
                "title": page_title,
                "response": f"🌐 **تم فتح الرابط بواسطة المتصفح:** {page_title}\n\n**محتوى الصفحة:**\n{clean_text}..."
            }), 200

        # الحالة الثانية: إذا كان سؤالاً نصياً -> أتمتة البحث والجلب من المتصفح مباشرة
        else:
            encoded_query = prompt_input.replace(" ", "+")
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            driver.get(search_url)
            time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            snippets = soup.find_all('a', class_='result__snippet')
            
            extracted_results = [s.get_text(strip=True) for s in snippets[:4] if s.get_text(strip=True)]
            
            if extracted_results:
                formatted_response = "\n\n• ".join(extracted_results)
                reply = f"🤖 **نتائج أتمتة المتصفح المباشرة لـ ({prompt_input}):**\n\n• {formatted_response}"
            else:
                reply = f"تم تنفيذ الأتمتة والبحث عبر المتصفح عن '{prompt_input}'، ولكن لم يتم إرجاع نصوص مباشرة."

            return jsonify({
                "status": "success",
                "title": "أتمتة المتصفح",
                "response": reply
            }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "response": f"تنبيه الأتمتة: {str(e)}"
        }), 200

    finally:
        # إغلاق المتصفح وإجبار السيرفر على تفريغ الذاكرة
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        kill_chromium_processes()
        gc.collect()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
