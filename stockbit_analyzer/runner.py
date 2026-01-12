import os
import time
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def load_config():
    """Load configuration from environment variables"""
    load_dotenv()
    return {
        "username": os.getenv("STOCKBIT_USERNAME", ""),
        "password": os.getenv("STOCKBIT_PASSWORD", ""),
        "headless": os.getenv("HEADLESS_MODE", "false").lower() == "true",
    }


def setup_driver(config):
    """Initialize and configure Chrome WebDriver with persistent profile"""
    chrome_options = Options()
    
    user_data_dir = Path.home() / ".stockbit_browser_profile"
    user_data_dir.mkdir(exist_ok=True)
    
    chrome_options.add_argument(f"--user-data-dir={str(user_data_dir)}")
    
    if not config["headless"]:
        chrome_options.add_argument("--start-maximized")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)
    
    return driver


def navigate_with_retry(driver, url, max_retries=3):
    """Navigate to URL with retry logic to handle renderer timeouts"""
    for attempt in range(max_retries):
        try:
            print(f"Attempting to navigate to {url} (attempt {attempt + 1}/{max_retries})...")
            driver.get(url)
            time.sleep(2)
            current_url = driver.current_url
            if url.split('?')[0] in current_url or current_url.startswith(url.split('?')[0]):
                print(f"Successfully navigated to: {current_url}")
                return True
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "renderer" in error_msg.lower():
                print(f"Renderer timeout on attempt {attempt + 1}, trying workaround...")
                try:
                    driver.execute_script(f"window.location.href = '{url}';")
                    time.sleep(3)
                    current_url = driver.current_url
                    if url.split('?')[0] in current_url or current_url.startswith(url.split('?')[0]):
                        print(f"JavaScript navigation succeeded: {current_url}")
                        return True
                except Exception as js_error:
                    print(f"JavaScript navigation also failed: {js_error}")
                    if attempt < max_retries - 1:
                        print("Retrying...")
                        time.sleep(2)
                        continue
            else:
                raise
    
    print("All navigation attempts failed")
    return False


def login_to_stockbit(driver, config, manual_login=False):
    """Handle Stockbit login - either manual or automated"""
    print("Navigating to Stockbit login page...")
    if not navigate_with_retry(driver, "https://stockbit.com/login"):
        raise Exception("Failed to navigate to login page after multiple attempts")
    
    if manual_login:
        print("\n" + "="*70)
        print("MANUAL LOGIN MODE")
        print("="*70)
        print("Please log in manually in the browser window.")
        print("The script will wait for you to complete the login process.")
        print("="*70 + "\n")
        
        initial_url = driver.current_url
        wait = WebDriverWait(driver, 600)
        
        try:
            wait.until(lambda d: d.current_url != initial_url and "login" not in d.current_url.lower())
            current_url = driver.current_url
            print(f"\nLogin successful! Current URL: {current_url}")
            
            if "new-device" in current_url.lower():
                print("\nNew device verification required. Please complete verification...")
                verification_wait = WebDriverWait(driver, 300)
                verification_wait.until(lambda d: "new-device" not in d.current_url.lower())
                print("Verification completed!")
            
        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False
    else:
        wait = WebDriverWait(driver, 10)
        redirect_wait = WebDriverWait(driver, 30)
        
        try:
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
            login_button = wait.until(EC.element_to_be_clickable((By.ID, "email-login-button")))
            
            print("Filling in credentials...")
            username_field.send_keys(config["username"])
            password_field.send_keys(config["password"])
            
            print("Clicking login button...")
            login_button.click()
            
            time.sleep(2)
            redirect_wait.until(lambda d: "login" not in d.current_url.lower())
            current_url = driver.current_url
            print(f"Login successful! Current URL: {current_url}")
            if "new-device" in current_url.lower():
                print("NEW DEVICE VERIFICATION REQUIRED")
                print("="*70)
                print("A verification code has been sent to your email.")
                print("Please enter the code in the browser window.")
                print("Waiting for you to complete verification...")
                print("="*70 + "\n")
                
                verification_wait = WebDriverWait(driver, 300)
                try:
                    verification_wait.until(lambda d: "new-device" not in d.current_url.lower())
                    final_url = driver.current_url
                    print(f"\nVerification completed! Redirected to: {final_url}")
                except Exception as e:
                    error_msg = str(e) if str(e) else type(e).__name__
                    print(f"\nTimeout waiting for verification. Current URL: {driver.current_url}")
                    print(f"Error details: {error_msg}")
                    raise Exception(f"Verification timeout - please complete verification manually and try again. Error: {error_msg}")
            
            return True
        except Exception as e:
            error_msg = str(e) if str(e) else f"{type(e).__name__} (no message)"
            print(f"Login failed: {error_msg}")
            print(f"Current URL: {driver.current_url}")
            return False


def main(manual_login=False):
    """Main entry point"""
    config = load_config()
    driver = setup_driver(config)
    
    try:
        success = login_to_stockbit(driver, config, manual_login=manual_login)
        if success:
            print("\nLogin completed successfully!")
            print("Browser will stay open for 10 seconds...")
            time.sleep(10)
        else:
            print("\nLogin failed. Browser will stay open for 20 seconds...")
            time.sleep(20)
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Browser will stay open for 20 seconds for debugging...")
        time.sleep(20)
    finally:
        driver.quit()



if __name__ == "__main__":
    main()
