
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
    
    # تحديد مسار المتصفح والمشغل المثبتين بالنظام
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    
    return webdriver.Chrome(service=service, options=chrome_options)

@app.route('/ask', methods=['POST'])
def run_browser_task():
    data = request.get_json() or {}
    target_url = data.get("url", "https://example.com")
    
    driver = None
    try:
        driver = get_driver()
        driver.get(target_url)
        page_title = driver.title
        
        return jsonify({
            "status": "success",
            "title": page_title
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
