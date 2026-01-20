import os
import time
import random
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def load_config():
    """Load configuration from environment variables"""
    load_dotenv()
    return {
        "username": os.getenv("STOCKBIT_USERNAME", ""),
        "password": os.getenv("STOCKBIT_PASSWORD", ""),
        "headless": os.getenv("HEADLESS_MODE", "false").lower() == "true",
    }


def setup_browser(playwright, config, manual_login=False):
    """Initialize and configure browser with persistent context"""
    user_data_dir = Path.home() / ".stockbit_browser_profile"
    user_data_dir.mkdir(exist_ok=True)
    
    headless_mode = config["headless"] and not manual_login
    
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(user_data_dir),
        headless=headless_mode,
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-infobars",
            "--disable-save-password-bubble",
            "--disable-single-click-autofill",
            "--disable-translate",
            "--disable-component-extensions-with-background-pages",
            "--disable-default-apps",
            "--disable-extensions-file-access-check",
            "--disable-extensions-http-throttling",
            "--disable-ipc-flooding-protection",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-pings",
            "--password-store=basic",
            "--use-mock-keychain",
            "--enable-automation=false",
            "--exclude-switches=enable-automation",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=TranslateUI",
            "--disable-features=BlinkGenPropertyTrees",
        ],
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
    )
    
    context.set_default_timeout(60000)
    context.set_default_navigation_timeout(60000)
    
    page = context.pages[0] if context.pages else context.new_page()
    
    # Enhanced stealth scripts for reCAPTCHA v3 bypass
    page.add_init_script("""
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Override plugins with realistic data
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: ""},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    },
                    {
                        0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                        1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                        description: "",
                        filename: "internal-nacl-plugin",
                        length: 2,
                        name: "Native Client"
                    }
                ];
                plugins.item = function(index) { return this[index]; };
                plugins.namedItem = function(name) {
                    for (let i = 0; i < this.length; i++) {
                        if (this[i].name === name) return this[i];
                    }
                    return null;
                };
                return plugins;
            }
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Enhanced chrome object
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Override WebGL vendor/renderer
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.call(this, parameter);
        };
        
        // Override WebGL2
        const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter2.call(this, parameter);
        };
        
        // Canvas fingerprint randomization
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            const context = this.getContext('2d');
            if (context) {
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] = imageData.data[i] ^ 1;
                }
                context.putImageData(imageData, 0, 0);
            }
            return originalToDataURL.apply(this, arguments);
        };
        
        // AudioContext fingerprint spoofing
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
            const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
            AudioContext.prototype.createAnalyser = function() {
                const analyser = originalCreateAnalyser.apply(this, arguments);
                const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                analyser.getFloatFrequencyData = function(array) {
                    originalGetFloatFrequencyData.apply(this, arguments);
                    for (let i = 0; i < array.length; i++) {
                        array[i] += Math.random() * 0.0001 - 0.00005;
                    }
                };
                return analyser;
            };
        }
        
        // Override toString methods to hide automation
        const originalToString = Function.prototype.toString;
        Function.prototype.toString = function() {
            if (this === navigator.webdriver || this === window.chrome || this === window.navigator.plugins) {
                return 'function () { [native code] }';
            }
            return originalToString.apply(this, arguments);
        };
        
        // Hide automation indicators
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });
        
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });
        
        // Override getBattery if it exists
        if (navigator.getBattery) {
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1
            });
        }
        
        // Override connection property
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 50,
                downlink: 10,
                saveData: false
            })
        });
        
        // Override platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'MacIntel'
        });
        
        // Override vendor
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Google Inc.'
        });
        
        // Hide iframe detection
        Object.defineProperty(window, 'outerHeight', {
            get: () => window.innerHeight
        });
        
        Object.defineProperty(window, 'outerWidth', {
            get: () => window.innerWidth
        });
        
        // Override Notification permission
        const originalNotification = window.Notification;
        window.Notification = function(title, options) {
            return new originalNotification(title, options);
        };
        Object.defineProperty(Notification, 'permission', {
            get: () => 'default'
        });
        
        // Override MediaDevices
        if (navigator.mediaDevices) {
            Object.defineProperty(navigator.mediaDevices, 'enumerateDevices', {
                value: () => Promise.resolve([])
            });
        }
        
        // Prevent detection via iframe
        Object.defineProperty(window, 'frameElement', {
            get: () => null
        });
        
        // Override document properties
        Object.defineProperty(document, 'hidden', {
            get: () => false
        });
        
        Object.defineProperty(document, 'visibilityState', {
            get: () => 'visible'
        });
        
        // Add realistic timing
        const originalNow = Date.now;
        let timeOffset = 0;
        Date.now = function() {
            return originalNow() + timeOffset;
        };
        
        // Override performance timing
        if (window.performance && window.performance.timing) {
            const timing = window.performance.timing;
            Object.defineProperty(timing, 'navigationStart', {
                get: () => Date.now() - Math.random() * 1000
            });
        }
    """)
    
    return context, page


def simulate_human_behavior(page):
    """Simulate human-like mouse movements and scrolling to improve reCAPTCHA v3 score"""
    try:
        viewport = page.viewport_size
        if not viewport:
            return
        
        width = viewport['width']
        height = viewport['height']
        
        for _ in range(random.randint(2, 4)):
            x = random.randint(100, width - 100)
            y = random.randint(100, height - 100)
            page.mouse.move(x, y, steps=random.randint(5, 15))
            time.sleep(random.uniform(0.1, 0.3))
        
        page.mouse.move(width // 2, height // 2, steps=10)
        time.sleep(random.uniform(0.2, 0.5))
        
        page.evaluate("""
            window.scrollTo({
                top: Math.random() * 200,
                left: 0,
                behavior: 'smooth'
            });
        """)
        time.sleep(random.uniform(0.5, 1.0))
        
    except Exception as e:
        print(f"Note: Could not simulate human behavior: {e}")


def navigate_with_retry(page, url, max_retries=3):
    """Navigate to URL with retry logic"""
    for attempt in range(max_retries):
        try:
            print(f"Attempting to navigate to {url} (attempt {attempt + 1}/{max_retries})...")
            page.goto(url, wait_until="networkidle", timeout=60000)
            current_url = page.url
            if url.split('?')[0] in current_url or current_url.startswith(url.split('?')[0]):
                print(f"Successfully navigated to: {current_url}")
                return True
        except PlaywrightTimeoutError as e:
            print(f"Navigation timeout on attempt {attempt + 1}, retrying...")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                raise
        except Exception as e:
            print(f"Navigation error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                raise
    
    print("All navigation attempts failed")
    return False


def login_to_stockbit(page, config, manual_login=False):
    """Handle Stockbit login - either manual or automated"""
    print("Navigating to Stockbit login page...")
    if not navigate_with_retry(page, "https://stockbit.com/login"):
        raise Exception("Failed to navigate to login page after multiple attempts")
    
    print("Waiting for page to fully load and reCAPTCHA to initialize...")
    time.sleep(3)
    
    if manual_login:
        print("\n" + "="*70)
        print("MANUAL LOGIN MODE")
        print("="*70)
        print("Please log in manually in the browser window.")
        print("The script will wait for you to complete the login process.")
        print("\nTips for better reCAPTCHA v3 score:")
        print("- Wait a few seconds after the page loads before typing")
        print("- Type naturally with some pauses")
        print("- Move your mouse around the page a bit")
        print("- Don't rush - take your time")
        print("="*70 + "\n")
        
        time.sleep(2)
        simulate_human_behavior(page)
        time.sleep(1)
        
        initial_url = page.url
        max_wait_time = 600
        check_interval = 2
        elapsed_time = 0
        
        try:
            while elapsed_time < max_wait_time:
                try:
                    if page.is_closed():
                        print("\n⚠️  Browser page was closed. Please check the browser window.")
                        return False
                    
                    current_url = page.url
                    
                    if current_url != initial_url and "login" not in current_url.lower():
                        print(f"\n✅ Login successful! Current URL: {current_url}")
                        
                        if "new-device" in current_url.lower():
                            print("\nNew device verification required. Please complete verification...")
                            verification_elapsed = 0
                            verification_max = 300
                            
                            while verification_elapsed < verification_max:
                                try:
                                    if page.is_closed():
                                        print("\n⚠️  Browser page was closed during verification.")
                                        return False
                                    
                                    current_url = page.url
                                    if "new-device" not in current_url.lower():
                                        print(f"✅ Verification completed! Redirected to: {current_url}")
                                        return True
                                    
                                    time.sleep(check_interval)
                                    verification_elapsed += check_interval
                                    
                                    if verification_elapsed % 30 == 0:
                                        print(f"Still waiting for verification... ({verification_elapsed}s/{verification_max}s)")
                                        
                                except Exception as e:
                                    print(f"Error checking verification status: {e}")
                                    time.sleep(check_interval)
                                    verification_elapsed += check_interval
                            
                            print(f"\n⚠️  Verification timeout after {verification_max} seconds.")
                            print(f"Current URL: {page.url}")
                            return False
                        
                        return True
                    
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    
                    if elapsed_time % 30 == 0:
                        print(f"Waiting for login... ({elapsed_time}s/{max_wait_time}s)")
                        print(f"Current URL: {current_url}")
                        
                except Exception as e:
                    error_msg = str(e)
                    if "Target page, context or browser has been closed" in error_msg:
                        print("\n⚠️  Browser was closed. Please check the browser window.")
                        return False
                    print(f"Error checking login status: {error_msg}")
                    time.sleep(check_interval)
                    elapsed_time += check_interval
            
            print(f"\n⚠️  Login timeout after {max_wait_time} seconds.")
            print(f"Final URL: {page.url}")
            return False
            
        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False
    else:
        try:
            # Wait a bit for page to fully load
            time.sleep(2)
            
            username_field = page.wait_for_selector("#username", timeout=10000)
            password_field = page.wait_for_selector("#password", timeout=10000)
            login_button = page.wait_for_selector("#email-login-button", timeout=10000, state="visible")
            
            print("Filling in credentials...")
            # Type with human-like delays
            username_field.click()
            time.sleep(0.5)
            username_field.fill(config["username"])
            time.sleep(0.3)
            
            password_field.click()
            time.sleep(0.5)
            password_field.fill(config["password"])
            time.sleep(1)
            
            print("Clicking login button...")
            login_button.click()
            time.sleep(2)
            
            # Check if we're still on login page (might be captcha)
            current_url = page.url
            if "login" in current_url.lower():
                # Wait a bit to see if captcha appears or redirect happens
                time.sleep(30)
                current_url = page.url
                if "login" in current_url.lower():
                    print("\n⚠️  reCAPTCHA detected or login failed!")
                    print("Current URL:", current_url)
                    print("\nConsider using --manual-login flag to bypass reCAPTCHA manually.")
                    return False
            
            page.wait_for_function(
                '!window.location.href.toLowerCase().includes("login")',
                timeout=30000
            )
            current_url = page.url
            print(f"Login successful! Current URL: {current_url}")
            
            if "new-device" in current_url.lower():
                print("NEW DEVICE VERIFICATION REQUIRED")
                print("="*70)
                print("A verification code has been sent to your email.")
                print("Please enter the code in the browser window.")
                print("Waiting for you to complete verification...")
                print("="*70 + "\n")
                
                try:
                    page.wait_for_function(
                        '!window.location.href.toLowerCase().includes("new-device")',
                        timeout=300000
                    )
                    final_url = page.url
                    print(f"\nVerification completed! Redirected to: {final_url}")
                except PlaywrightTimeoutError as e:
                    error_msg = str(e) if str(e) else type(e).__name__
                    print(f"\nTimeout waiting for verification. Current URL: {page.url}")
                    print(f"Error details: {error_msg}")
                    raise Exception(f"Verification timeout - please complete verification manually and try again. Error: {error_msg}")
            
            return True
        except Exception as e:
            error_msg = str(e) if str(e) else f"{type(e).__name__} (no message)"
            print(f"Login failed: {error_msg}")
            print(f"Current URL: {page.url}")
            return False


def main(manual_login=False):
    """Main entry point"""
    config = load_config()
    
    if manual_login:
        print("\n" + "="*70)
        print("MANUAL LOGIN MODE ENABLED")
        print("="*70)
        print("The browser will open in visible mode (non-headless).")
        print("You can manually log in and solve the reCAPTCHA.")
        print("The script will automatically detect when login is complete.")
        print("="*70 + "\n")
    
    with sync_playwright() as playwright:
        context, page = setup_browser(playwright, config, manual_login=manual_login)
        
        try:
            success = login_to_stockbit(page, config, manual_login=manual_login)
            if success:
                print("\n✅ Login completed successfully!")
                if manual_login:
                    print("Browser will stay open for 30 seconds for you to verify...")
                    time.sleep(30)
                else:
                    print("Browser will stay open for 10 seconds...")
                    time.sleep(10)
            else:
                print("\n❌ Login failed.")
                if manual_login:
                    print("Browser will stay open for 60 seconds for debugging...")
                    time.sleep(60)
                else:
                    print("Browser will stay open for 20 seconds...")
                    time.sleep(20)
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Browser will stay open for 20 seconds for debugging...")
            time.sleep(20)
        finally:
            context.close()



if __name__ == "__main__":
    main()
