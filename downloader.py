import os
import time
import urllib.request
import shutil
import tempfile
import logging
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class ImageDownloader:
    def __init__(self, download_path: str = "downloads", log_dir: str = "logs"):
        self.download_path = os.path.abspath(download_path)
        self.log_dir = os.path.abspath(log_dir)
        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

    @contextmanager
    def _safe_file_operation(self):
        """Context manager for safe file operations"""
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'temp_image.jpg')
        try:
            yield temp_file
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Error cleaning temp files: {e}")

    def download_images(
        self,
        query: str,
        num_images: int = 5,
        min_size_kb: int = 180,
        image_type: str = "photo"
    ) -> Dict:
        """Download high-resolution images from Google Images."""
        driver = None
        downloaded_files = []
        total_attempts = 0
        
        try:
            logger.info(f"Starting download for query: {query}")
            min_size_bytes = min_size_kb * 1024
            search_dir = os.path.join(self.download_path, query.replace(" ", "_"))
            os.makedirs(search_dir, exist_ok=True)

            # Setup Chrome
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            # Use webdriver-manager for portability
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            logger.info("Navigating to Google Images...")
            driver.get("https://www.google.com/imghp")
            search_box = driver.find_element(By.NAME, "q")
            search_box.clear()
            search_box.send_keys(query + Keys.RETURN)
            time.sleep(2)

            if image_type != "all":
                try:
                    logger.info(f"Setting image type filter: {image_type}")
                    tools_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[text()='Tools']"))
                    )
                    tools_button.click()
                    time.sleep(1)
                    
                    type_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[text()='Type']"))
                    )
                    type_button.click()
                    time.sleep(1)
                    
                    type_option = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//div[text()='{image_type.capitalize()}']"))
                    )
                    type_option.click()
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"Could not set image type filter: {str(e)}")

            downloaded = 0
            scrolls = 0
            
            while downloaded < num_images and scrolls < 10:
                containers = driver.find_elements(By.CSS_SELECTOR, 'div[jsname="dTDiAc"]')
                logger.debug(f"Found {len(containers)} image containers")
                
                for container in containers[downloaded:]:
                    if downloaded >= num_images:
                        break

                    try:
                        total_attempts += 1
                        driver.execute_script("arguments[0].scrollIntoView(true);", container)
                        time.sleep(0.5)
                        container.click()
                        time.sleep(1)

                        # High-res image selector (this might need updates if Google changes UI)
                        high_res_selectors = [
                            'img.sFlh5c.FyHeAf.iPVvYb',
                            'img.n3VNCb',
                            'img.r48_rs'
                        ]
                        
                        high_res_img = None
                        for selector in high_res_selectors:
                            try:
                                high_res_img = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                )
                                if high_res_img:
                                    break
                            except:
                                continue

                        if not high_res_img:
                            continue
                            
                        img_url = high_res_img.get_attribute('src')
                        if not img_url or not img_url.startswith('http'):
                            continue
                            
                        with self._safe_file_operation() as temp_file:
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
                            }
                            
                            req = urllib.request.Request(img_url, headers=headers)
                            with urllib.request.urlopen(req, timeout=10) as response, open(temp_file, 'wb') as out_file:
                                data = response.read()
                                out_file.write(data)
                            
                            file_size = os.path.getsize(temp_file)
                            logger.debug(f"Downloaded file size: {file_size/1024:.1f}KB")
                            
                            if file_size >= min_size_bytes:
                                timestamp = datetime.now().strftime("%H%M%S")
                                filename = f"{query.replace(' ', '_')}_{timestamp}_{downloaded+1}.jpg"
                                filepath = os.path.join(search_dir, filename)
                                
                                shutil.move(temp_file, filepath)
                                downloaded += 1
                                downloaded_files.append(filepath)
                                logger.info(f"Downloaded image {downloaded}/{num_images}: {filename}")

                    except Exception as e:
                        logger.debug(f"Error processing image: {str(e)}")
                        continue

                if downloaded < num_images:
                    scrolls += 1
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)

            return {
                "status": "success",
                "downloaded": len(downloaded_files),
                "files": downloaded_files,
                "attempts": total_attempts
            }

        except Exception as e:
            logger.error(f"Error in download_images: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "downloaded": len(downloaded_files),
                "files": downloaded_files
            }
        finally:
            if driver:
                driver.quit()
