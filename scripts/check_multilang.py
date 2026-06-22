#!/usr/bin/env python3
"""
Test multilingual selector generation.
"""

from multilang import lang_selector
from config import REGION_CURRENT

print("=" * 60)
print("Multilingual selector test")
print("=" * 60)

print(f"\n📍 Current region: {REGION_CURRENT.upper()}")
lang_selector.print_current_language()

print("\n🔍 Testing selector generation:")
print("-" * 60)

# Test button selector.
print("\n1. Continue button XPath:")
continue_xpath = lang_selector.get_button_xpath('continue')
print(f"   {continue_xpath}")

print("\n2. Sign up button XPath:")
signup_xpath = lang_selector.get_text_xpath('sign_up_with_builder_id')
print(f"   {signup_xpath}")

print("\n3. Continue text variations:")
variations = lang_selector.get_all_text_variations('continue')
for i, text in enumerate(variations, 1):
    print(f"   {i}. {text}")

print("\n4. Sign up text variations:")
variations = lang_selector.get_all_text_variations('sign_up_with_builder_id')
for i, text in enumerate(variations, 1):
    print(f"   {i}. {text}")

print("\n" + "=" * 60)
print("✅ Multilingual selector test complete")
print("=" * 60)
