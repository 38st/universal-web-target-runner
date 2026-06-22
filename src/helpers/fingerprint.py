"""
Browser fingerprint randomization module.
Randomizes Canvas, WebGL, Audio, and other browser signals.
"""

import random
import hashlib
import time


class FingerprintRandomizer:
    """Fingerprint randomizer."""
    
    def __init__(self):
        # Generate a random seed.
        self.seed = int(time.time() * 1000) % 10000
        random.seed(self.seed)
    
    def get_canvas_noise_script(self):
        """
        Canvas fingerprint randomization script.
        Adds small rendering noise to change the fingerprint without visible impact.
        """
        noise_r = random.randint(1, 10)
        noise_g = random.randint(1, 10)
        noise_b = random.randint(1, 10)
        
        script = f"""
        (function() {{
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            
            // Add noise to Canvas.
            const addNoise = function(canvas) {{
                const ctx = canvas.getContext('2d');
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                for (let i = 0; i < imageData.data.length; i += 4) {{
                    imageData.data[i] = imageData.data[i] + {noise_r}; // R
                    imageData.data[i + 1] = imageData.data[i + 1] + {noise_g}; // G
                    imageData.data[i + 2] = imageData.data[i + 2] + {noise_b}; // B
                }}
                ctx.putImageData(imageData, 0, 0);
            }};
            
            // Override toDataURL.
            HTMLCanvasElement.prototype.toDataURL = function() {{
                addNoise(this);
                return originalToDataURL.apply(this, arguments);
            }};
            
            // Override toBlob.
            HTMLCanvasElement.prototype.toBlob = function() {{
                addNoise(this);
                return originalToBlob.apply(this, arguments);
            }};
            
            // Override getImageData.
            CanvasRenderingContext2D.prototype.getImageData = function() {{
                const imageData = originalGetImageData.apply(this, arguments);
                for (let i = 0; i < imageData.data.length; i += 4) {{
                    imageData.data[i] = imageData.data[i] + {noise_r};
                    imageData.data[i + 1] = imageData.data[i + 1] + {noise_g};
                    imageData.data[i + 2] = imageData.data[i + 2] + {noise_b};
                }}
                return imageData;
            }};
        }})();
        """
        return script
    
    def get_webgl_noise_script(self):
        """
        WebGL fingerprint randomization script.
        Changes WebGL renderer info and parameters.
        """
        vendors = ['Intel Inc.', 'NVIDIA Corporation', 'AMD', 'Apple Inc.']
        renderers = [
            'Intel(R) UHD Graphics 620',
            'NVIDIA GeForce GTX 1660',
            'AMD Radeon RX 580',
            'Apple M1',
            'Intel(R) Iris(R) Plus Graphics'
        ]
        
        vendor = random.choice(vendors)
        renderer = random.choice(renderers)
        
        script = f"""
        (function() {{
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{
                    return '{vendor}'; // UNMASKED_VENDOR_WEBGL
                }}
                if (parameter === 37446) {{
                    return '{renderer}'; // UNMASKED_RENDERER_WEBGL
                }}
                return getParameter.call(this, parameter);
            }};
            
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{
                    return '{vendor}';
                }}
                if (parameter === 37446) {{
                    return '{renderer}';
                }}
                return getParameter2.call(this, parameter);
            }};
        }})();
        """
        return script
    
    def get_audio_noise_script(self):
        """
        Audio fingerprint randomization script.
        Adds small noise to AudioContext.
        """
        noise = random.uniform(0.00001, 0.0001)
        
        script = f"""
        (function() {{
            const audioContext = window.AudioContext || window.webkitAudioContext;
            if (audioContext) {{
                const originalCreateOscillator = audioContext.prototype.createOscillator;
                audioContext.prototype.createOscillator = function() {{
                    const oscillator = originalCreateOscillator.call(this);
                    const originalStart = oscillator.start;
                    oscillator.start = function() {{
                        // Add a small frequency offset.
                        oscillator.frequency.value = oscillator.frequency.value + {noise};
                        return originalStart.apply(this, arguments);
                    }};
                    return oscillator;
                }};
            }}
        }})();
        """
        return script
    
    def get_navigator_override_script(self):
        """
        Navigator override script.
        Randomizes hardware concurrency, device memory, and related values.
        """
        hardware_concurrency = random.choice([2, 4, 6, 8, 12, 16])
        device_memory = random.choice([4, 8, 16, 32])
        max_touch_points = random.choice([0, 1, 5, 10])
        
        script = f"""
        (function() {{
            // Hardware concurrency.
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {hardware_concurrency}
            }});
            
            // Device memory.
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {device_memory}
            }});
            
            // Touch point count.
            Object.defineProperty(navigator, 'maxTouchPoints', {{
                get: () => {max_touch_points}
            }});
            
            // Hide webdriver property.
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined
            }});
            
            // Randomize plugin list.
            const plugins = ['Chrome PDF Plugin', 'Chrome PDF Viewer', 'Native Client'];
            Object.defineProperty(navigator, 'plugins', {{
                get: () => plugins
            }});
        }})();
        """
        return script
    
    def get_screen_randomize_script(self):
        """
        Screen info randomization script.
        """
        resolutions = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 2560, 'height': 1440}
        ]
        
        resolution = random.choice(resolutions)
        color_depth = random.choice([24, 32])
        pixel_depth = random.choice([24, 32])
        
        script = f"""
        (function() {{
            Object.defineProperty(screen, 'width', {{
                get: () => {resolution['width']}
            }});
            
            Object.defineProperty(screen, 'height', {{
                get: () => {resolution['height']}
            }});
            
            Object.defineProperty(screen, 'availWidth', {{
                get: () => {resolution['width']}
            }});
            
            Object.defineProperty(screen, 'availHeight', {{
                get: () => {resolution['height'] - 40}
            }});
            
            Object.defineProperty(screen, 'colorDepth', {{
                get: () => {color_depth}
            }});
            
            Object.defineProperty(screen, 'pixelDepth', {{
                get: () => {pixel_depth}
            }});
        }})();
        """
        return script
    
    def get_webrtc_protect_script(self):
        """
        WebRTC IP leak protection script.
        """
        script = """
        (function() {
            // Prevent WebRTC from leaking the real IP.
            const originalRTCPeerConnection = window.RTCPeerConnection;
            window.RTCPeerConnection = function(config = {}) {
                // Force proxy usage to prevent IP leaks.
                if (!config.iceServers) {
                    config.iceServers = [];
                }
                // Disable mDNS.
                config.iceCandidatePoolSize = 0;
                return new originalRTCPeerConnection(config);
            };
        })();
        """
        return script
    
    def get_all_scripts(self):
        """
        Get all fingerprint randomization scripts.
        """
        scripts = [
            self.get_canvas_noise_script(),
            self.get_webgl_noise_script(),
            self.get_audio_noise_script(),
            self.get_navigator_override_script(),
            self.get_screen_randomize_script(),
            self.get_webrtc_protect_script()
        ]
        
        # Combine all scripts.
        return '\n'.join(scripts)
    
    def inject_to_driver(self, driver):
        """
        Inject all fingerprint randomization scripts into the browser.
        
        Args:
            driver: Selenium WebDriver instance.
        """
        try:
            # Inject all scripts.
            combined_script = self.get_all_scripts()
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': combined_script
            })
            print("✅ Fingerprint randomization scripts injected")
            return True
        except Exception as e:
            print(f"⚠️  Fingerprint randomization injection failed: {e}")
            return False


# Global instance.
fingerprint_randomizer = FingerprintRandomizer()
