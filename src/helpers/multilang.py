"""
Multilingual selector module.
Supports localized UI element lookup for different regions.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from selenium.webdriver.common.by import By
from config import REGION_CURRENT


class MultiLangSelector:
    """Multilingual selector helper."""
    
    def __init__(self):
        # Load language config from the project config directory.
        lang_config_path = Path(__file__).parent.parent.parent / "config" / "languages.yaml"
        with open(lang_config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        # Get the language for the current region.
        self.current_lang = self._config['region_language_map'].get(
            REGION_CURRENT, 
            'en'
        )
        
        # Load all language texts for compatibility selectors.
        self.texts = self._config['languages']
        self.current_texts = self.texts.get(self.current_lang, self.texts['en'])
    
    def get_text(self, key):
        """Get text for the current language."""
        return self.current_texts.get(key, key)
    
    def get_all_text_variations(self, key):
        """Get all text variations for a key."""
        variations = []
        for lang_code, lang_texts in self.texts.items():
            text = lang_texts.get(key)
            if text and text not in variations:
                variations.append(text)
        return variations
    
    def get_button_xpath(self, key):
        """
        Build a button XPath that matches all configured language variants.
        Example: //button[contains(., 'Continue') or contains(., 'Weiter') or contains(., 'Continue')]
        """
        variations = self.get_all_text_variations(key)
        if not variations:
            return f"//button"
        
        # Build OR conditions.
        conditions = [f"contains(., '{text}')" for text in variations]
        xpath = f"//button[{' or '.join(conditions)}]"
        return xpath
    
    def get_link_xpath(self, key):
        """
        Build a link XPath that matches all configured language variants.
        """
        variations = self.get_all_text_variations(key)
        if not variations:
            return f"//a"
        
        conditions = [f"contains(., '{text}')" for text in variations]
        xpath = f"//a[{' or '.join(conditions)}]"
        return xpath
    
    def get_text_xpath(self, key):
        """
        Build an element XPath that matches all configured language variants.
        """
        variations = self.get_all_text_variations(key)
        if not variations:
            return f"//*"
        
        conditions = [f"contains(., '{text}')" for text in variations]
        xpath = f"//*[{' or '.join(conditions)}]"
        return xpath
    
    def get_by_xpath(self, key, element_type='button'):
        """
        Get a Selenium By tuple.
        
        Args:
            key: Text key.
            element_type: 'button', 'link', 'any'
        
        Returns:
            (By.XPATH, xpath_string)
        """
        if element_type == 'button':
            xpath = self.get_button_xpath(key)
        elif element_type == 'link':
            xpath = self.get_link_xpath(key)
        else:
            xpath = self.get_text_xpath(key)
        
        return (By.XPATH, xpath)
    
    def print_current_language(self):
        """Print the current language."""
        lang_names = {
            'de': 'German (Deutsch)',
            'ja': 'Japanese',
            'en': 'English'
        }
        lang_name = lang_names.get(self.current_lang, self.current_lang)
        print(f"🌍 UI language: {lang_name}")
    
    def update_region(self, region_name):
        """Update the active region."""
        self.current_lang = self._config['region_language_map'].get(
            region_name,
            'en'
        )
        self.current_texts = self.texts.get(self.current_lang, self.texts['en'])



# Global selector instance.
lang_selector = MultiLangSelector()


def get_continue_button_selector():
    """Get the multilingual selector for the Continue button."""
    return lang_selector.get_by_xpath('continue', 'button')


def get_signup_button_selector():
    """Get the multilingual selector for the signup button."""
    return lang_selector.get_by_xpath('sign_up_with_builder_id', 'any')
