    import os
    import time
    import cv2
    import uuid
    import requests
    from io import BytesIO
    from PIL import Image
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
    from seleniumbase import Driver
    from yt_dlp import YoutubeDL

    class MediaExtractor:
        """Simple media extractor for YouTube, Google, Instagram, and Twitter."""
        
        def __init__(self, output_dir="media_frames"):
            self.output_dir = output_dir
            self.driver = None
            os.makedirs(output_dir, exist_ok=True)
            
        def _setup_driver(self):
            """Setup Chrome driver."""
            self.driver = Driver(uc_cdp=True,uc=True)
            self.driver.implicitly_wait(5)
            
        def _save_image(self, image_data, prefix="image", min_resolution=400):
            """Save image with resolution check."""
            try:
                # Open image
                if isinstance(image_data, bytes):
                    img = Image.open(BytesIO(image_data))
                elif isinstance(image_data, str):  # URL
                    response = requests.get(image_data, timeout=10)
                    img = Image.open(BytesIO(response.content))
                else:
                    return None
                
                # Check resolution
                if img.width < min_resolution or img.height < min_resolution:
                    return None
                
                # Save image
                filename = f"{prefix}_{uuid.uuid4().hex[:8]}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                img.convert('RGB').save(filepath, 'JPEG', quality=85)
                return filepath
                
            except Exception as e:
                print(f"  Error saving image: {e}")
                return None

        # ============ YOUTUBE EXTRACTOR ============
        def extract_youtube(self, query, max_videos=5, frames_per_video=3):
            """Extract frames from YouTube videos."""
            print(f"\n[YouTube] Searching: {query}")
            results = []
            
            try:
                self._setup_driver()
                driver = self.driver
                
                # Search YouTube
                search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                driver.get(search_url)
                time.sleep(2)
                
                # Get video URLs
                urls = set()
                last_height = 0
                
                for _ in range(20):  # Scroll 20 times
                    for el in driver.find_elements(By.CSS_SELECTOR, "a#video-title"):
                        href = el.get_attribute("href")
                        if href and "/watch?v=" in href:
                            urls.add(href.split("&")[0])
                    
                    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                    time.sleep(1.5)
                    
                    new_height = driver.execute_script("return document.documentElement.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                
                print(f"  Found {len(urls)} videos")
                driver.quit()
                
                # Process videos
                video_urls = list(urls)[:max_videos]
                for i, url in enumerate(video_urls, 1):
                    print(f"  [{i}/{len(video_urls)}] Processing video...")
                    
                    try:
                        # Download video
                        ydl_opts = {
                            'format': 'best[ext=mp4]',
                            'outtmpl': f'{self.output_dir}/temp_video.mp4',
                            'quiet': True,
                        }
                        
                        with YoutubeDL(ydl_opts) as ydl:
                            ydl.extract_info(url, download=True)
                        
                        # Extract frames
                        cap = cv2.VideoCapture(f'{self.output_dir}/temp_video.mp4')
                        
                        # Check resolution
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        
                        if width < 400 or height < 400:
                            print(f"    Skipping: Resolution {width}x{height} too small")
                            cap.release()
                            os.remove(f'{self.output_dir}/temp_video.mp4')
                            continue
                        
                        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        interval = max(1, total_frames // frames_per_video)
                        
                        video_id = url.split("=")[-1][:8]
                        saved = 0
                        
                        for f in range(frames_per_video):
                            cap.set(cv2.CAP_PROP_POS_FRAMES, interval * f)
                            ret, frame = cap.read()
                            
                            if ret:
                                frame_path = os.path.join(self.output_dir, f"yt_{video_id}_{uuid.uuid4().hex[:6]}.jpg")
                                cv2.imwrite(frame_path, frame)
                                saved += 1
                                results.append(frame_path)
                        
                        cap.release()
                        os.remove(f'{self.output_dir}/temp_video.mp4')
                        print(f"    ✓ Saved {saved} frames")
                        
                    except Exception as e:
                        print(f"    ✗ Error: {e}")
                        
            except Exception as e:
                print(f"  Error: {e}")
                if self.driver:
                    self.driver.quit()
            
            return results

        # ============ GOOGLE IMAGES EXTRACTOR ============
        def extract_google_images(self, query, max_images=20):
            """Extract images from Google Images."""
            print(f"\n[Google Images] Searching: {query}")
            results = []
            
            try:
                self._setup_driver()
                driver = self.driver
                
                # Search Google Images
                search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
                driver.get(search_url)
                time.sleep(2)
                
                # Scroll to load more images
                for _ in range(5):  # Scroll 5 times
                    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                    time.sleep(1.5)
                
                # Get image elements
                image_elements = driver.find_elements(By.XPATH, '//*[@id="rso"]/div/div/div/div/div[1]/div')
                print(f"  Found {len(image_elements)} images")
                
                # Download images
                for i, img_element in enumerate(image_elements[:max_images], 1):
                    try:
                        # Get image URL
                        img_url = img_element.get_attribute("src")
                        print(f"img_url : {img_url}")
                        if not img_url or not img_url.startswith("http"):
                            # Click to load high-res image
                            driver.execute_script("arguments[0].click();", img_element)
                            time.sleep(1)
                            
                            # Get high-res URL
                            high_res = driver.find_elements(By.CSS_SELECTOR, "img.n3VNCb")
                            if high_res:
                                img_url = high_res[0].get_attribute("src")
                        
                        if img_url and img_url.startswith("http"):
                            filepath = self._save_image(img_url, f"google_{i}")
                            if filepath:
                                results.append(filepath)
                                print(f"  [{i}/{max_images}] ✓ Saved image")
                            else:
                                print(f"  [{i}/{max_images}] ✗ Resolution too small")
                        else:
                            print(f"  [{i}/{max_images}] ✗ No valid image URL")
                            
                    except Exception as e:
                        print(f"  [{i}/{max_images}] ✗ Error: {e}")
                
                driver.quit()
                
            except Exception as e:
                print(f"  Error: {e}")
                if self.driver:
                    self.driver.quit()
            
            return results

        # ============ MAIN EXTRACTION METHOD ============
        def extract_all(self, query, platforms=None, **kwargs):
            """
            Extract from multiple platforms.
            
            Args:
                query: Search term
                platforms: List of platforms ['youtube', 'google', 'instagram', 'twitter']
                **kwargs: Platform-specific arguments (max_videos, max_images, etc.)
            """
            if platforms is None:
                platforms = ['youtube', 'google', 'instagram', 'twitter']
            
            all_results = {}
            
            """if 'youtube' in platforms:
                all_results['youtube'] = self.extract_youtube(
                    query, 
                    max_videos=kwargs.get('max_videos', 5),
                    frames_per_video=kwargs.get('frames_per_video', 3)
                )"""
            
            if 'google' in platforms:
                all_results['google'] = self.extract_google_images(
                    query,
                    max_images=kwargs.get('max_images', 20)
                )
            

            
            # Print summary
            print("\n" + "="*60)
            print("EXTRACTION COMPLETE!")
            print("="*60)
            total = 0
            for platform, results in all_results.items():
                count = len(results)
                total += count
                print(f"{platform.capitalize():10} : {count} images")
            print("-"*60)
            print(f"TOTAL IMAGES: {total}")
            print(f"Saved in: {self.output_dir}/")
            print("="*60)
            
            return all_results

    # ============ USAGE ============
    if __name__ == "__main__":
        # Create extractor
        extractor = MediaExtractor(output_dir="my_media")
        
        # Extract from all platforms
        results = extractor.extract_all(
            query="Thieboudienne",  # Search term
            platforms=['google','youtube'],
            max_videos=5,        # YouTube videos
            frames_per_video=3,  # Frames per YouTube video
            max_images=20,       # Google images
            max_posts=10,        # Instagram posts
            max_tweets=10        # Twitter posts
        )
        
