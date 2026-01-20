import os
import time
import random
from datetime import datetime, timedelta
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
    
    # Try to launch persistent context, with retry logic for locked profiles
    max_retries = 3
    for attempt in range(max_retries):
        try:
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
            break
        except Exception as e:
            if attempt < max_retries - 1:
                error_msg = str(e)
                if "Target page, context or browser has been closed" in error_msg or "already in use" in error_msg.lower():
                    print(f"Browser profile is locked (attempt {attempt + 1}/{max_retries}). Waiting 2 seconds...")
                    time.sleep(2)
                    # Try to kill any existing browser processes using this profile
                    import subprocess
                    try:
                        subprocess.run(["pkill", "-f", "stockbit_browser_profile"], check=False)
                        time.sleep(1)
                    except:
                        pass
                    continue
                else:
                    raise
            else:
                raise
    
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
            
            # Check if navigation succeeded (either exact match or redirected)
            url_base = url.split('?')[0].split('#')[0].rstrip('/')
            current_base = current_url.split('?')[0].split('#')[0].rstrip('/')
            
            # Success if we reached the target URL or were redirected (which is OK for login page)
            if url_base in current_url or current_url.startswith(url_base) or current_url.startswith(url.split('?')[0]):
                print(f"Successfully navigated to: {current_url}")
                return True
            
            # If trying to go to login page but redirected away, that's also OK (already authenticated)
            if "login" in url.lower() and "login" not in current_url.lower():
                print(f"Redirected away from login page (likely already authenticated): {current_url}")
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
    
    # Check if already authenticated (redirected away from login page)
    current_url = page.url
    is_login_page = "login" in current_url.lower() or current_url.endswith("/login")
    
    if not is_login_page:
        print(f"\n✅ Already authenticated! Current URL: {current_url}")
        print("Skipping login process...")
        return True
    
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
        
        # Get initial URL using JavaScript to ensure we have the actual current URL
        initial_url = page.evaluate("() => window.location.href") or page.url
        max_wait_time = 600
        check_interval = 2
        elapsed_time = 0
        
        try:
            while elapsed_time < max_wait_time:
                try:
                    if page.is_closed():
                        print("\n⚠️  Browser page was closed. Please check the browser window.")
                        return False
                    
                    try:
                        # Force evaluation of current URL using JavaScript to get real-time URL
                        current_url = page.evaluate("() => window.location.href") or page.url
                    except Exception as e:
                        print(f"Error getting URL: {e}")
                        time.sleep(check_interval)
                        elapsed_time += check_interval
                        continue
                    
                    # Check if we've left the login page (more robust check)
                    initial_url_clean = initial_url.split('?')[0].split('#')[0].rstrip('/')
                    current_url_clean = current_url.split('?')[0].split('#')[0].rstrip('/')
                    
                    is_login_page = "login" in current_url.lower() or current_url_clean.endswith("/login")
                    url_changed = current_url_clean != initial_url_clean
                    
                    # Debug output every 30 seconds
                    if elapsed_time % 30 == 0:
                        print(f"Waiting for login... ({elapsed_time}s/{max_wait_time}s)")
                        print(f"Current URL: {current_url}")
                        print(f"Initial URL: {initial_url}")
                        print(f"URL changed: {url_changed}, Is login page: {is_login_page}")
                    
                    # Also check if we're on stream page or any non-login page
                    if url_changed and not is_login_page:
                        print(f"\n✅ Login detected! URL changed from login page.")
                        print(f"Current URL: {current_url}")
                        print(f"Proceeding with login completion...")
                        
                        if "new-device" in current_url.lower():
                            print("\nNew device verification required. Please complete verification...")
                            verification_elapsed = 0
                            verification_max = 300
                            
                            while verification_elapsed < verification_max:
                                try:
                                    if page.is_closed():
                                        print("\n⚠️  Browser page was closed during verification.")
                                        return False
                                    
                                    current_url = page.evaluate("() => window.location.href") or page.url
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
                        
                        print("Login completed successfully, returning True...")
                        return True
                    
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                        
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


def set_date_range(page, days):
    """Set the date range picker to last X days by clicking calendar dates"""
    try:
        # Calculate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days - 1)  # days-1 because today is included
        
        # Format dates for display (e.g., "Jan 20, 2026")
        start_date_str = start_date.strftime("%b %d, %Y")
        end_date_str = end_date.strftime("%b %d, %Y")
        
        print(f"Setting date range: {start_date_str} to {end_date_str}")
        
        # Find date picker inputs within broker summary
        broker_summary_locator = page.locator('div.sc-f10b1c12-0.jQepBs').first
        
        # Wait for date pickers to be visible
        time.sleep(2)
        
        # Get date picker containers first, then get inputs from each
        date_pickers = broker_summary_locator.locator('div.ant-picker').all()
        
        if len(date_pickers) < 2:
            print(f"⚠️  Warning: Found {len(date_pickers)} date picker containers, trying alternative selector...")
            date_pickers = page.locator('div.sc-f10b1c12-0.jQepBs div.ant-picker').all()
        
        if len(date_pickers) < 2:
            print(f"⚠️  Warning: Could not find date pickers. Found {len(date_pickers)} containers")
            return
        
        # Get inputs from each picker container
        start_picker_container = date_pickers[0]
        end_picker_container = date_pickers[1]
        
        start_input = start_picker_container.locator('div.ant-picker-input > input').first
        end_input = end_picker_container.locator('div.ant-picker-input > input').first
        
        # Verify which input is which by checking their current values or positions
        try:
            start_value_before = start_input.input_value()
            end_value_before = end_input.input_value()
            print(f"Initial values - Start: {start_value_before}, End: {end_value_before}")
        except:
            pass
        
        # Set start date
        print(f"Clicking start date input (first input) to open calendar...")
        start_input.click()
        time.sleep(2)  # Wait for calendar to fully open
        
        # Wait for calendar to appear and click the start date
        start_day = start_date.day
        start_month = start_date.month
        start_year = start_date.year
        
        # Use JavaScript to find and click the date cell
        start_day = start_date.day
        start_month = start_date.month
        start_year = start_date.year
        
        result = page.evaluate(f"""
            () => {{
                const calendarBody = document.querySelector('div.ant-picker-body');
                if (!calendarBody) {{
                    return {{ error: 'Calendar body not found' }};
                }}
                
                // Find all date cells (td elements with class ant-picker-cell)
                const cells = calendarBody.querySelectorAll('td.ant-picker-cell');
                let targetCell = null;
                
                // Target date: day {start_day}
                for (const cell of cells) {{
                    const cellText = cell.textContent.trim();
                    const cellTitle = cell.getAttribute('title') || '';
                    
                    // Check if this cell matches our target day number
                    // Also check title attribute which often contains full date
                    if (cellText === '{start_day}' && 
                        (cellTitle.includes('{start_date_str}') || cellTitle.includes('{start_month}') || cellTitle.includes('{start_year}'))) {{
                        // Make sure it's not disabled and is in-range
                        if (!cell.classList.contains('ant-picker-cell-disabled') && 
                            !cell.classList.contains('ant-picker-cell-in-range')) {{
                            targetCell = cell;
                            break;
                        }}
                    }}
                }}
                
                // If not found by title, try just by day number (might be in current month view)
                if (!targetCell) {{
                    for (const cell of cells) {{
                        const cellText = cell.textContent.trim();
                        if (cellText === '{start_day}' && 
                            !cell.classList.contains('ant-picker-cell-disabled') &&
                            !cell.classList.contains('ant-picker-cell-in-range')) {{
                            targetCell = cell;
                            break;
                        }}
                    }}
                }}
                
                if (targetCell) {{
                    targetCell.click();
                    return {{ success: true, clicked: targetCell.textContent.trim(), title: targetCell.getAttribute('title') }};
                }} else {{
                    return {{ error: 'Date cell not found for day {start_day}', availableCells: cells.length }};
                }}
            }}
        """)
        
        if result.get('error'):
            print(f"⚠️  Warning: Could not click start date: {result.get('error')}")
        else:
            print(f"✅ Start date clicked: {result.get('clicked')}")
        
        # Wait for calendar to close and start date to be set
        time.sleep(2)
        
        # Verify start date was set correctly before proceeding
        try:
            start_date_value = start_input.input_value()
            print(f"Start date after selection: {start_date_value}")
            
            # If start date is wrong, something went wrong
            if start_date_str not in start_date_value and str(start_day) not in start_date_value:
                print(f"⚠️  Warning: Start date not set correctly. Expected {start_date_str}, got {start_date_value}")
        except:
            pass
        
        # Close any open calendar dropdowns before clicking end date
        page.keyboard.press('Escape')
        time.sleep(1)
        
        # Double-check that start date is still set correctly
        try:
            start_check = start_input.input_value()
            print(f"Start date before end date selection: {start_check}")
            if start_date_str not in start_check and str(start_day) not in start_check:
                print(f"⚠️  Start date was lost! Re-setting...")
                start_input.click()
                time.sleep(1.5)
                # Re-click start date
                page.evaluate(f"""
                    () => {{
                        const calendarBody = document.querySelector('div.ant-picker-body');
                        if (calendarBody) {{
                            const cells = calendarBody.querySelectorAll('td.ant-picker-cell');
                            for (const cell of cells) {{
                                if (cell.textContent.trim() === '{start_day}' && 
                                    !cell.classList.contains('ant-picker-cell-disabled')) {{
                                    cell.click();
                                    break;
                                }}
                            }}
                        }}
                    }}
                """)
                time.sleep(1)
                page.keyboard.press('Escape')
                time.sleep(0.5)
        except:
            pass
        
        # Set end date - click the END picker container's input
        print(f"Clicking end date input (second picker) to open calendar...")
        end_input.click()
        time.sleep(2)  # Wait for calendar to fully open
        
        # Verify we're clicking the end date input by checking which input is focused
        focused_input = page.evaluate("""
            () => {
                const active = document.activeElement;
                if (active && active.tagName === 'INPUT') {
                    return { isInput: true, value: active.value };
                }
                return { isInput: false };
            }
        """)
        print(f"Focused element after clicking end date: {focused_input}")
        
        # Click the end date in the calendar
        end_day = end_date.day
        end_month = end_date.month
        end_year = end_date.year
        
        result = page.evaluate(f"""
            () => {{
                // Find the calendar that's associated with the end date picker
                // Look for the calendar dropdown that's currently visible
                const calendarBody = document.querySelector('div.ant-picker-dropdown:not([style*="display: none"]) div.ant-picker-body') ||
                                     document.querySelector('div.ant-picker-body');
                if (!calendarBody) {{
                    return {{ error: 'Calendar body not found' }};
                }}
                
                // Find all date cells (td elements with class ant-picker-cell)
                const cells = calendarBody.querySelectorAll('td.ant-picker-cell');
                let targetCell = null;
                
                // Target date: day {end_day} - make sure we're selecting the END date
                // Prefer cells marked as "today" to ensure we're setting end date correctly
                for (const cell of cells) {{
                    const cellText = cell.textContent.trim();
                    const cellTitle = cell.getAttribute('title') || '';
                    
                    // Check if this cell matches our target day number
                    if (cellText === '{end_day}') {{
                        // Make sure it's not disabled
                        if (!cell.classList.contains('ant-picker-cell-disabled')) {{
                            // Strongly prefer today's cell (which should be day {end_day})
                            if (cell.classList.contains('ant-picker-cell-today')) {{
                                targetCell = cell;
                                break;
                            }}
                            // Also check title for exact match
                            if ((cellTitle.includes('{end_date_str}') || cellTitle.includes('{end_month}') || cellTitle.includes('{end_year}')) && !targetCell) {{
                                targetCell = cell;
                            }}
                        }}
                    }}
                }}
                
                // If not found by title, try just by day number - prefer today
                if (!targetCell) {{
                    for (const cell of cells) {{
                        const cellText = cell.textContent.trim();
                        if (cellText === '{end_day}' && 
                            !cell.classList.contains('ant-picker-cell-disabled')) {{
                            // Prefer today's cell
                            if (cell.classList.contains('ant-picker-cell-today')) {{
                                targetCell = cell;
                                break;
                            }}
                            if (!targetCell) {{
                                targetCell = cell;
                            }}
                        }}
                    }}
                }}
                
                if (targetCell) {{
                    // Double-click or ensure we're setting end date
                    targetCell.click();
                    return {{ success: true, clicked: targetCell.textContent.trim(), title: targetCell.getAttribute('title'), isToday: targetCell.classList.contains('ant-picker-cell-today') }};
                }} else {{
                    return {{ error: 'Date cell not found for day {end_day}', availableCells: cells.length }};
                }}
            }}
        """)
        
        if result.get('error'):
            print(f"⚠️  Warning: Could not click end date: {result.get('error')}")
        else:
            print(f"✅ End date clicked: {result.get('clicked')}")
        
        # Wait for calendar to close
        time.sleep(1)
        page.keyboard.press('Escape')  # Ensure calendar is closed
        time.sleep(1)
        
        # Verify both dates are set correctly
        try:
            final_start = start_input.input_value()
            final_end = end_input.input_value()
            print(f"Final date range - Start: {final_start}, End: {final_end}")
            
            # Check if start date was incorrectly changed
            if start_date_str not in final_start and str(start_day) not in final_start:
                print(f"❌ ERROR: Start date was changed incorrectly!")
                print(f"   Expected: {start_date_str} (day {start_day})")
                print(f"   Got: {final_start}")
                print(f"   Attempting to fix...")
                
                # Try to re-set the start date
                start_input.click()
                time.sleep(1.5)
                page.evaluate(f"""
                    () => {{
                        const calendarBody = document.querySelector('div.ant-picker-body');
                        if (calendarBody) {{
                            const cells = calendarBody.querySelectorAll('td.ant-picker-cell');
                            for (const cell of cells) {{
                                const cellText = cell.textContent.trim();
                                const cellTitle = cell.getAttribute('title') || '';
                                if (cellText === '{start_day}' && 
                                    !cell.classList.contains('ant-picker-cell-disabled') &&
                                    (cellTitle.includes('{start_date_str}') || cellTitle.includes('{start_month}'))) {{
                                    cell.click();
                                    break;
                                }}
                            }}
                        }}
                    }}
                """)
                time.sleep(1)
                page.keyboard.press('Escape')
                time.sleep(1)
                
                # Re-check
                final_start = start_input.input_value()
                print(f"After fix - Start: {final_start}, End: {final_end}")
            
            if start_date_str in final_start and end_date_str in final_end:
                print(f"✅ Date range set successfully")
            else:
                print(f"⚠️  Warning: Date range mismatch.")
                print(f"   Expected Start: {start_date_str}, Got: {final_start}")
                print(f"   Expected End: {end_date_str}, Got: {final_end}")
        except Exception as e:
            print(f"⚠️  Could not verify date range: {e}")
        
        time.sleep(2)  # Extra wait for table to update
        
    except Exception as e:
        print(f"⚠️  Warning: Error setting date range: {str(e)}")
        import traceback
        traceback.print_exc()
        print("Continuing with default date range...")


def format_broker_summary_table(rows, date_range=None):
    """Format broker summary rows into a nicely formatted table"""
    formatted_rows = []
    
    # Add date range header if available
    if date_range:
        start_date = date_range.get('start', 'N/A')
        end_date = date_range.get('end', 'N/A')
        formatted_rows.append(f"📅 Date Range: {start_date} to {end_date}")
        formatted_rows.append("")
    
    # Table header
    header = f"{'BY':<6} {'B.val':<12} {'B.lot':<10} {'B.avg':<8} | {'SL':<6} {'S.val':<12} {'S.lot':<10} {'S.avg':<8}"
    separator = "-" * 100
    
    formatted_rows.extend([header, separator])
    
    # Format each row
    for row in rows:
        formatted_row = (
            f"{row['buyBroker']:<6} "
            f"{row['buyValue']:<12} "
            f"{row['buyLot']:<10} "
            f"{row['buyAvg']:<8} | "
            f"{row['sellBroker']:<6} "
            f"{row['sellValue']:<12} "
            f"{row['sellLot']:<10} "
            f"{row['sellAvg']:<8}"
        )
        formatted_rows.append(formatted_row)
    
    return "\n".join(formatted_rows)


def extract_broker_summary(page, stock_symbol="BUMI", days=1):
    """Extract Broker Summary table data from Stockbit stock page"""
    print(f"\nNavigating to stock page for {stock_symbol}...")
    url = f"https://stockbit.com/symbol/{stock_symbol}"
    
    if not navigate_with_retry(page, url):
        raise Exception(f"Failed to navigate to {url}")
    
    print("Waiting for Broker Summary table to load...")
    time.sleep(3)
    
    # If days > 1, extract data for each individual day
    if days > 1:
        print(f"\nExtracting broker summary for each of the last {days} trading days (skipping weekends)...")
        all_results = []
        
        # Collect trading days (skip weekends: Saturday=5, Sunday=6)
        trading_dates = []
        current_date = datetime.now()
        day_offset = 0
        
        while len(trading_dates) < days:
            check_date = current_date - timedelta(days=day_offset)
            weekday = check_date.weekday()  # Monday=0, Sunday=6
            
            # Skip weekends (Saturday=5, Sunday=6)
            if weekday < 5:  # Monday through Friday
                trading_dates.append(check_date)
            
            day_offset += 1
            
            # Safety check to prevent infinite loop
            if day_offset > days * 2:
                print(f"⚠️  Warning: Could not find {days} trading days within {day_offset} calendar days")
                break
        
        # Sort dates from oldest to newest
        trading_dates.sort()
        
        # Extract data for each trading day
        for idx, target_date in enumerate(trading_dates, 1):
            day_number = idx
            day_name = target_date.strftime('%A')
            
            print(f"\n{'='*70}")
            print(f"Day {day_number}/{days} ({day_name}): {target_date.strftime('%b %d, %Y')}")
            print(f"{'='*70}")
            
            # Set date range to single day (start = end = target_date)
            set_single_date_range(page, target_date)
            print("Waiting for table to update...")
            time.sleep(3)
            
            # Extract data for this day
            day_data = extract_single_day_data(page, target_date)
            if day_data:
                day_data['day'] = day_number
                day_data['date'] = target_date.strftime('%b %d, %Y')
                all_results.append(day_data)
                print(f"✅ Extracted {len(day_data.get('rows', []))} rows for {target_date.strftime('%b %d, %Y')}")
            else:
                print(f"⚠️  No data found for {target_date.strftime('%b %d, %Y')}")
            
            time.sleep(1)  # Small delay between days
        
        return {
            'all_days': all_results,
            'total_days': len(all_results),
            'summary': f"Extracted data for {len(all_results)} trading days"
        }
    
    # Single day extraction (original behavior)
    # If today is a weekend, use the last trading day instead
    today = datetime.now()
    weekday = today.weekday()  # Monday=0, Sunday=6
    
    if weekday >= 5:  # Saturday or Sunday
        # Go back to find the last Friday
        days_back = weekday - 4  # Saturday: 1 day back, Sunday: 2 days back
        target_date = today - timedelta(days=days_back)
        print(f"⚠️  Today is {today.strftime('%A')}, using last trading day: {target_date.strftime('%b %d, %Y')}")
    else:
        target_date = today
    
    return extract_single_day_data(page, target_date)


def set_single_date_range(page, target_date):
    """Set the date range picker to a single specific date (start = end = target_date)"""
    try:
        date_str = target_date.strftime("%b %d, %Y")
        day = target_date.day
        target_month = target_date.month
        target_year = target_date.year
        target_month_name = target_date.strftime("%b")
        
        print(f"Setting date range to: {date_str} (single day)")
        
        # Find date picker inputs within broker summary
        broker_summary_locator = page.locator('div.sc-f10b1c12-0.jQepBs').first
        time.sleep(1)
        
        # Get date picker containers
        date_pickers = broker_summary_locator.locator('div.ant-picker').all()
        if len(date_pickers) < 2:
            date_pickers = page.locator('div.sc-f10b1c12-0.jQepBs div.ant-picker').all()
        
        if len(date_pickers) < 2:
            print(f"⚠️  Warning: Could not find date pickers")
            return
        
        start_picker_container = date_pickers[0]
        end_picker_container = date_pickers[1]
        
        start_input = start_picker_container.locator('div.ant-picker-input > input').first
        end_input = end_picker_container.locator('div.ant-picker-input > input').first
        
        # Set start date
        print(f"Setting start date to {date_str}...")
        start_input.click()
        time.sleep(2)
        
        result = page.evaluate(f"""
            () => {{
                // Find the currently visible calendar dropdown (for start date picker)
                const visibleDropdown = Array.from(document.querySelectorAll('div.ant-picker-dropdown')).find(
                    dropdown => {{
                        const style = window.getComputedStyle(dropdown);
                        return style.display !== 'none' && style.visibility !== 'hidden';
                    }}
                );
                
                const calendarBody = visibleDropdown 
                    ? visibleDropdown.querySelector('div.ant-picker-body')
                    : document.querySelector('div.ant-picker-body');
                    
                if (!calendarBody) {{
                    return {{ error: 'Calendar body not found' }};
                }}
                
                const cells = calendarBody.querySelectorAll('td.ant-picker-cell');
                let targetCell = null;
                let exactMatch = null;
                
                // First pass: Look for exact date match via title attribute
                for (const cell of cells) {{
                    const cellText = cell.textContent.trim();
                    const cellTitle = cell.getAttribute('title') || '';
                    
                    if (cellText === '{day}' && !cell.classList.contains('ant-picker-cell-disabled')) {{
                        // Prioritize exact date match in title
                        if (cellTitle.includes('{date_str}') || 
                            (cellTitle.includes('{target_month_name}') && cellTitle.includes('{target_year}'))) {{
                            exactMatch = cell;
                            break;
                        }}
                    }}
                }}
                
                // If exact match found, use it
                if (exactMatch) {{
                    targetCell = exactMatch;
                }} else {{
                    // Second pass: Find by day number, but avoid "today" if it's not our target date
                    for (const cell of cells) {{
                        const cellText = cell.textContent.trim();
                        const cellTitle = cell.getAttribute('title') || '';
                        
                        if (cellText === '{day}' && !cell.classList.contains('ant-picker-cell-disabled')) {{
                            // Only use "today" if the title matches our target date
                            if (cell.classList.contains('ant-picker-cell-today')) {{
                                if (cellTitle.includes('{date_str}') || 
                                    (cellTitle.includes('{target_month_name}') && cellTitle.includes('{target_year}'))) {{
                                    targetCell = cell;
                                    break;
                                }}
                                // Skip "today" if it doesn't match our target date
                                continue;
                            }}
                            
                            // Use first matching cell that's not today
                            if (!targetCell) {{
                                targetCell = cell;
                            }}
                        }}
                    }}
                }}
                
                if (targetCell) {{
                    targetCell.click();
                    return {{ 
                        success: true, 
                        clicked: targetCell.textContent.trim(),
                        title: targetCell.getAttribute('title'),
                        isToday: targetCell.classList.contains('ant-picker-cell-today')
                    }};
                }} else {{
                    return {{ error: 'Date cell not found for day {day}', availableCells: cells.length }};
                }}
            }}
        """)
        
        if result.get('error'):
            print(f"⚠️  Warning: Could not click start date: {result.get('error')}")
        else:
            clicked_day = result.get('clicked')
            clicked_title = result.get('title', '')
            print(f"✅ Start date clicked: {clicked_day} (title: {clicked_title})")
        
        time.sleep(2)
        page.keyboard.press('Escape')
        time.sleep(1)
        
        # Set end date to the same date
        print(f"Setting end date to {date_str}...")
        end_input.click()
        time.sleep(2)
        
        result = page.evaluate(f"""
            () => {{
                // Find the currently visible calendar dropdown (for end date picker)
                const visibleDropdown = Array.from(document.querySelectorAll('div.ant-picker-dropdown')).find(
                    dropdown => {{
                        const style = window.getComputedStyle(dropdown);
                        return style.display !== 'none' && style.visibility !== 'hidden';
                    }}
                );
                
                const calendarBody = visibleDropdown 
                    ? visibleDropdown.querySelector('div.ant-picker-body')
                    : document.querySelector('div.ant-picker-body');
                    
                if (!calendarBody) {{
                    return {{ error: 'Calendar body not found' }};
                }}
                
                const cells = calendarBody.querySelectorAll('td.ant-picker-cell');
                let targetCell = null;
                let exactMatch = null;
                
                // First pass: Look for exact date match via title attribute
                for (const cell of cells) {{
                    const cellText = cell.textContent.trim();
                    const cellTitle = cell.getAttribute('title') || '';
                    
                    if (cellText === '{day}' && !cell.classList.contains('ant-picker-cell-disabled')) {{
                        // Prioritize exact date match in title
                        if (cellTitle.includes('{date_str}') || 
                            (cellTitle.includes('{target_month_name}') && cellTitle.includes('{target_year}'))) {{
                            exactMatch = cell;
                            break;
                        }}
                    }}
                }}
                
                // If exact match found, use it
                if (exactMatch) {{
                    targetCell = exactMatch;
                }} else {{
                    // Second pass: Find by day number, but avoid "today" if it's not our target date
                    for (const cell of cells) {{
                        const cellText = cell.textContent.trim();
                        const cellTitle = cell.getAttribute('title') || '';
                        
                        if (cellText === '{day}' && !cell.classList.contains('ant-picker-cell-disabled')) {{
                            // Only use "today" if the title matches our target date
                            if (cell.classList.contains('ant-picker-cell-today')) {{
                                if (cellTitle.includes('{date_str}') || 
                                    (cellTitle.includes('{target_month_name}') && cellTitle.includes('{target_year}'))) {{
                                    targetCell = cell;
                                    break;
                                }}
                                // Skip "today" if it doesn't match our target date
                                continue;
                            }}
                            
                            // Use first matching cell that's not today
                            if (!targetCell) {{
                                targetCell = cell;
                            }}
                        }}
                    }}
                }}
                
                if (targetCell) {{
                    targetCell.click();
                    return {{ 
                        success: true, 
                        clicked: targetCell.textContent.trim(),
                        title: targetCell.getAttribute('title'),
                        isToday: targetCell.classList.contains('ant-picker-cell-today')
                    }};
                }} else {{
                    return {{ error: 'Date cell not found for day {day}', availableCells: cells.length }};
                }}
            }}
        """)
        
        if result.get('error'):
            print(f"⚠️  Warning: Could not click end date: {result.get('error')}")
        else:
            clicked_day = result.get('clicked')
            clicked_title = result.get('title', '')
            print(f"✅ End date clicked: {clicked_day} (title: {clicked_title})")
        
        time.sleep(2)  # Wait for date picker to update
        page.keyboard.press('Escape')
        time.sleep(1)
        
        # Verify dates are set correctly with retry logic
        max_retries = 3
        for retry in range(max_retries):
            try:
                final_start = start_input.input_value()
                final_end = end_input.input_value()
                
                # Check if end date matches our target
                if date_str in final_end or str(day) in final_end:
                    if date_str in final_start and date_str in final_end:
                        print(f"✅ Date range verified: Start={final_start}, End={final_end}")
                        break
                    elif date_str in final_start:
                        print(f"⚠️  Date verification: Start={final_start}, End={final_end} (end date mismatch, retrying...)")
                    else:
                        print(f"⚠️  Date verification: Start={final_start}, End={final_end} (both dates mismatch)")
                else:
                    print(f"⚠️  Date verification: Start={final_start}, End={final_end} (end date is wrong, retrying...)")
                
                # If end date is wrong, try to fix it
                if retry < max_retries - 1 and (date_str not in final_end and str(day) not in final_end):
                    print(f"Retrying end date selection (attempt {retry + 2}/{max_retries})...")
                    end_input.click()
                    time.sleep(2)
                    
                    # Re-select the end date with more precision
                    retry_result = page.evaluate(f"""
                        () => {{
                            const visibleDropdown = Array.from(document.querySelectorAll('div.ant-picker-dropdown')).find(
                                dropdown => {{
                                    const style = window.getComputedStyle(dropdown);
                                    return style.display !== 'none' && style.visibility !== 'hidden';
                                }}
                            );
                            
                            const calendarBody = visibleDropdown 
                                ? visibleDropdown.querySelector('div.ant-picker-body')
                                : document.querySelector('div.ant-picker-body');
                                
                            if (!calendarBody) {{
                                return {{ error: 'Calendar body not found' }};
                            }}
                            
                            const cells = calendarBody.querySelectorAll('td.ant-picker-cell');
                            let targetCell = null;
                            
                            // Find cell with exact date match
                            for (const cell of cells) {{
                                const cellText = cell.textContent.trim();
                                const cellTitle = cell.getAttribute('title') || '';
                                
                                if (cellText === '{day}' && !cell.classList.contains('ant-picker-cell-disabled')) {{
                                    // Require exact date match in title
                                    if (cellTitle.includes('{date_str}') || 
                                        (cellTitle.includes('{target_month_name}') && cellTitle.includes('{target_year}'))) {{
                                        targetCell = cell;
                                        break;
                                    }}
                                }}
                            }}
                            
                            // If still not found, try without title requirement but skip "today" if it's wrong
                            if (!targetCell) {{
                                for (const cell of cells) {{
                                    const cellText = cell.textContent.trim();
                                    const cellTitle = cell.getAttribute('title') || '';
                                    
                                    if (cellText === '{day}' && !cell.classList.contains('ant-picker-cell-disabled')) {{
                                        // Skip "today" if it doesn't match our date
                                        if (cell.classList.contains('ant-picker-cell-today')) {{
                                            if (!cellTitle.includes('{date_str}') && 
                                                !(cellTitle.includes('{target_month_name}') && cellTitle.includes('{target_year}'))) {{
                                                continue;
                                            }}
                                        }}
                                        targetCell = cell;
                                        break;
                                    }}
                                }}
                            }}
                            
                            if (targetCell) {{
                                targetCell.click();
                                return {{ success: true, clicked: targetCell.textContent.trim(), title: targetCell.getAttribute('title') }};
                            }} else {{
                                return {{ error: 'Date cell not found for day {day}' }};
                            }}
                        }}
                    """)
                    
                    if retry_result.get('error'):
                        print(f"⚠️  Retry failed: {retry_result.get('error')}")
                    else:
                        print(f"✅ Retry clicked: {retry_result.get('clicked')} (title: {retry_result.get('title', '')})")
                    
                    time.sleep(2)
                    page.keyboard.press('Escape')
                    time.sleep(1)
                    
            except Exception as e:
                print(f"⚠️  Error verifying dates: {e}")
                if retry < max_retries - 1:
                    time.sleep(1)
        
    except Exception as e:
        print(f"⚠️  Warning: Error setting single date: {str(e)}")


def extract_single_day_data(page, target_date=None):
    """Extract broker summary data for a single day"""
    if target_date is None:
        target_date = datetime.now()
    
    try:
        broker_summary_data = page.evaluate("""
            () => {
                // Find the Broker Summary container
                const brokerSummary = document.querySelector('div.sc-f10b1c12-0.jQepBs') || 
                                     Array.from(document.querySelectorAll('div')).find(el => 
                                         el.innerText && el.innerText.includes('Broker Summary') && 
                                         el.innerText.includes('BY')
                                     );
                
                if (!brokerSummary) {
                    return { error: 'Broker Summary container not found' };
                }
                
                // Extract date range from date pickers
                let dateRange = null;
                const datePickers = brokerSummary.querySelectorAll('div.ant-picker, .ant-picker-input input');
                if (datePickers.length >= 2) {
                    const startDateInput = datePickers[0].querySelector('input') || datePickers[0];
                    const endDateInput = datePickers[1].querySelector('input') || datePickers[1];
                    
                    const startDate = startDateInput.value || startDateInput.getAttribute('value') || startDateInput.textContent || '';
                    const endDate = endDateInput.value || endDateInput.getAttribute('value') || endDateInput.textContent || '';
                    
                    if (startDate && endDate) {
                        dateRange = {
                            start: startDate.trim(),
                            end: endDate.trim()
                        };
                    }
                }
                
                // Also try to find date range in text format
                if (!dateRange) {
                    const dateText = brokerSummary.innerText;
                    const dateMatch = dateText.match(/(\\d{1,2}[\\s/\\-]\\w{3}[\\s/\\-]\\d{2,4}|\\w{3}[\\s/\\-]\\d{1,2}[\\s/\\-]\\d{2,4})/gi);
                    if (dateMatch && dateMatch.length >= 2) {
                        dateRange = {
                            start: dateMatch[0].trim(),
                            end: dateMatch[1].trim()
                        };
                    }
                }
                
                // Find the data table with class sc-4858c0ef-27
                const dataTable = brokerSummary.querySelector('div.sc-4858c0ef-27.fhVdvL') ||
                                  brokerSummary.querySelector('div[class*="sc-4858c0ef-27"]') ||
                                  Array.from(brokerSummary.querySelectorAll('div')).find(el => 
                                      el.innerText && el.innerText.includes('BY') && 
                                      el.innerText.includes('B.val') && el.innerText.includes('B.lot')
                                  );
                
                if (!dataTable) {
                    return { 
                        error: 'Data table not found',
                        containerText: brokerSummary.innerText.substring(0, 500),
                        dateRange: dateRange
                    };
                }
                
                // Extract all text content
                const fullText = dataTable.innerText;
                
                // Parse the text - split by whitespace and filter empty strings
                const tokens = fullText.split(/\\s+/).filter(t => t.trim().length > 0);
                
                // Find header row
                let headerStart = -1;
                for (let i = 0; i < tokens.length - 7; i++) {
                    if (tokens[i] === 'BY' && tokens[i+1] === 'B.val' && tokens[i+2] === 'B.lot' && 
                        tokens[i+3] === 'B.avg' && tokens[i+4] === 'SL' && tokens[i+5] === 'S.val' &&
                        tokens[i+6] === 'S.lot' && tokens[i+7] === 'S.avg') {
                        headerStart = i;
                        break;
                    }
                }
                
                if (headerStart === -1) {
                    return {
                        success: true,
                        rawText: fullText,
                        tokens: tokens,
                        error: 'Could not find header row'
                    };
                }
                
                // Parse data rows (start after header which is 8 tokens)
                const rows = [];
                let i = headerStart + 8;
                
                while (i < tokens.length) {
                    // Look for broker code pattern (2 uppercase letters)
                    if (/^[A-Z]{2}$/.test(tokens[i])) {
                        const buyBroker = tokens[i];
                        
                        // Check if we have enough tokens for a complete row (7 more)
                        if (i + 7 < tokens.length) {
                            const buyValue = tokens[i + 1];
                            const buyLot = tokens[i + 2];
                            const buyAvg = tokens[i + 3];
                            const sellBroker = tokens[i + 4];
                            const sellValue = tokens[i + 5];
                            const sellLot = tokens[i + 6];
                            const sellAvg = tokens[i + 7];
                            
                            // Validate - sell broker should also be 2 letters
                            if (/^[A-Z]{2}$/.test(sellBroker)) {
                                rows.push({
                                    buyBroker: buyBroker,
                                    buyValue: buyValue,
                                    buyLot: buyLot,
                                    buyAvg: buyAvg,
                                    sellBroker: sellBroker,
                                    sellValue: sellValue,
                                    sellLot: sellLot,
                                    sellAvg: sellAvg
                                });
                                i += 8;
                                continue;
                            }
                        }
                    }
                    i++;
                }
                
                return {
                    success: true,
                    rawText: fullText,
                    tokens: tokens,
                    rows: rows,
                    headerStart: headerStart,
                    dateRange: dateRange
                };
            }
        """)
        
        if broker_summary_data.get('error'):
            print(f"Error: {broker_summary_data['error']}")
            if 'containerText' in broker_summary_data:
                print(f"Container text: {broker_summary_data['containerText']}")
            return None
        
        if not broker_summary_data.get('success'):
            print("Failed to extract data")
            return None
        
        rows = broker_summary_data.get('rows', [])
        if not rows:
            print("No data rows found")
            print(f"Raw text: {broker_summary_data.get('rawText', '')[:500]}")
            return None
        
        print(f"✅ Successfully extracted {len(rows)} broker summary rows!")
        
        date_range = broker_summary_data.get('dateRange')
        if date_range:
            print(f"📅 Date Range: {date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}")
        
        return {
            'rows': rows,
            'rawText': broker_summary_data.get('rawText', ''),
            'dateRange': date_range
        }
        
    except Exception as e:
        print(f"Error extracting broker summary: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main(manual_login=False, stock_symbol=None, extract_data=False, days=1):
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
                
                if extract_data and stock_symbol:
                    broker_data = extract_broker_summary(page, stock_symbol, days=days)
                    
                    # Handle multi-day extraction
                    if broker_data and broker_data.get('all_days'):
                        print("\n" + "="*100)
                        print("BROKER SUMMARY DATA - ALL DAYS")
                        print("="*100)
                        
                        for day_data in broker_data['all_days']:
                            print(f"\n{'='*100}")
                            print(f"Day {day_data.get('day', 'N/A')}: {day_data.get('date', 'N/A')}")
                            print(f"{'='*100}")
                            
                            if day_data.get('rows'):
                                print(format_broker_summary_table(day_data['rows'], day_data.get('dateRange')))
                            else:
                                print("No data available for this day")
                        
                        print("\n" + "="*100)
                        print(f"Summary: {broker_data.get('summary', '')}")
                        print("="*100)
                    
                    # Handle single day extraction
                    elif broker_data and broker_data.get('rows'):
                        print("\n" + "="*100)
                        print("BROKER SUMMARY DATA")
                        print("="*100)
                        print(format_broker_summary_table(broker_data['rows'], broker_data.get('dateRange')))
                        print("="*100)
                    elif broker_data:
                        print("\n" + "="*70)
                        print("BROKER SUMMARY DATA (Raw)")
                        print("="*70)
                        print(broker_data.get('rawText', 'No data'))
                        print("="*70)
                
                if manual_login:
                    if not extract_data:
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
            if not extract_data or not manual_login:
                context.close()
            else:
                print("\nBrowser will remain open. Press Ctrl+C to close.")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nClosing browser...")
                    context.close()



if __name__ == "__main__":
    main()
