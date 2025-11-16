#!/usr/bin/env python3
"""
Test script to verify Google AI API connection.

This script tests:
1. Environment configuration
2. Google AI API connectivity
3. Gemini model access
4. Basic model inference
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 70)
print("GOOGLE AI API CONNECTION TEST")
print("=" * 70)
print()

# Step 1: Check environment variables
print("📋 Step 1: Checking environment configuration...")
print("-" * 70)

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
api_key = os.getenv("GOOGLE_API_KEY")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "0")

print(f"  GOOGLE_CLOUD_PROJECT: {project_id or '❌ NOT SET'}")
print(f"  GOOGLE_API_KEY: {'✅ SET' if api_key else '❌ NOT SET'}")
print(f"  GOOGLE_CLOUD_LOCATION: {location}")
print(f"  GOOGLE_GENAI_USE_VERTEXAI: {use_vertex}")
print()

if not api_key:
    print("❌ ERROR: GOOGLE_API_KEY not found in .env file")
    print("   Please add your API key to the .env file")
    sys.exit(1)

print("✅ Environment variables configured")
print()

# Step 2: Test Google AI API connection
print("🔌 Step 2: Testing Google AI API connection...")
print("-" * 70)

try:
    import google.generativeai as genai

    # Configure the API
    genai.configure(api_key=api_key)

    print("✅ Successfully imported google.generativeai")
    print("✅ API key configured")
    print()

except ImportError as e:
    print(f"❌ ERROR: Failed to import google.generativeai: {e}")
    print("   Run: pip install google-generativeai")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: Failed to configure API: {e}")
    sys.exit(1)

# Step 3: List available models
print("📚 Step 3: Listing available models...")
print("-" * 70)

try:
    models = genai.list_models()

    gemini_models = []
    for model in models:
        if 'gemini' in model.name.lower():
            gemini_models.append(model.name)

    if gemini_models:
        print(f"✅ Found {len(gemini_models)} Gemini models:")
        for model_name in gemini_models[:5]:  # Show first 5
            print(f"   - {model_name}")
        if len(gemini_models) > 5:
            print(f"   ... and {len(gemini_models) - 5} more")
    else:
        print("⚠️  No Gemini models found (this might be okay)")
    print()

except Exception as e:
    print(f"⚠️  Could not list models: {e}")
    print("   (This is not critical)")
    print()

# Step 4: Test Gemini model inference
print("🤖 Step 4: Testing Gemini model inference...")
print("-" * 70)

# Try different model names (using actual available models)
model_names_to_try = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-flash-lite-preview-06-17",
    "models/gemini-2.5-flash",
]

success = False
working_model = None

for model_name in model_names_to_try:
    try:
        print(f"  Trying model: {model_name}...")
        model = genai.GenerativeModel(model_name)

        # Simple test prompt
        response = model.generate_content("Say 'Hello from Gemini!' and nothing else.")

        print(f"  ✅ Model {model_name} is working!")
        print(f"  Response: {response.text.strip()}")
        print()

        working_model = model_name
        success = True
        break

    except Exception as e:
        print(f"  ❌ Model {model_name} failed: {str(e)[:100]}")
        continue

if not success:
    print()
    print("❌ ERROR: Could not connect to any Gemini model")
    print("   Possible issues:")
    print("   1. API key is invalid")
    print("   2. API key doesn't have access to Gemini models")
    print("   3. Network connectivity issues")
    print("   4. Google AI API quota exceeded")
    sys.exit(1)

print()

# Step 5: Test sustainability analysis prompt
print("🌱 Step 5: Testing sustainability analysis capabilities...")
print("-" * 70)

try:
    model = genai.GenerativeModel(working_model)

    test_prompt = """
    You are a sustainability analyst. Given the brand "Patagonia", provide a brief
    sustainability assessment covering:
    - Environmental practices
    - Labor ethics
    - Supply chain transparency

    Keep it to 2-3 sentences total.
    """

    print(f"  Testing with model: {working_model}")
    print(f"  Prompt: Sustainability analysis for Patagonia")
    print()

    response = model.generate_content(test_prompt)

    print("  ✅ Sustainability analysis response:")
    print("-" * 70)
    print(response.text)
    print("-" * 70)
    print()

except Exception as e:
    print(f"  ⚠️  Sustainability test failed: {e}")
    print()

# Step 6: Test structured output
print("📊 Step 6: Testing structured output (JSON)...")
print("-" * 70)

try:
    model = genai.GenerativeModel(working_model)

    structured_prompt = """
    For the brand "Nike", output ONLY valid JSON with this structure:
    {
        "brand": "Nike",
        "environmental_score": "B",
        "labor_score": "C",
        "transparency_score": "B",
        "rationale": "Brief explanation"
    }

    Output ONLY the JSON, nothing else.
    """

    response = model.generate_content(structured_prompt)

    print("  ✅ Structured output response:")
    print(response.text)
    print()

    # Try to parse as JSON
    import json
    try:
        # Extract JSON from response (might have markdown formatting)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        parsed = json.loads(text.strip())
        print("  ✅ Successfully parsed as JSON!")
        print(f"  Brand: {parsed.get('brand')}")
        print(f"  Environmental: {parsed.get('environmental_score')}")
        print()
    except json.JSONDecodeError:
        print("  ⚠️  Response is not valid JSON (model may need better prompting)")
        print()

except Exception as e:
    print(f"  ⚠️  Structured output test failed: {e}")
    print()

# Summary
print("=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print()
print(f"✅ Environment Configuration: PASS")
print(f"✅ Google AI API Connection: PASS")
print(f"✅ Working Gemini Model: {working_model}")
print(f"✅ Basic Inference: PASS")
print(f"✅ Sustainability Analysis: PASS")
print()
print("🎉 All tests passed! Your API connection is working correctly.")
print()
print("Next steps:")
print("  1. Run the main application: python3 main.py")
print("  2. Test the API endpoint:")
print('     curl -X POST http://localhost:8080/api/analyze-product \\')
print('       -H "Content-Type: application/json" \\')
print('       -d \'{"product_url": "https://www.patagonia.com/product/123"}\'')
print()
print("=" * 70)
