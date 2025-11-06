"""
Direct REST API test to list all available Gemini models for your API key
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in environment variables")
    exit(1)

print("=" * 80)
print("🔍 CHECKING AVAILABLE GEMINI MODELS FOR YOUR API KEY")
print("=" * 80)

# List all models endpoint
list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"

try:
    print("\n📡 Fetching available models...\n")
    response = requests.get(list_url, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    if 'models' not in data:
        print("❌ No models found in response")
        print(f"Response: {data}")
        exit(1)
    
    print(f"✅ Found {len(data['models'])} total models\n")
    print("-" * 80)
    
    # Filter models that support generateContent
    compatible_models = []
    
    for model in data['models']:
        model_name = model.get('name', 'Unknown')
        display_name = model.get('displayName', 'N/A')
        supported_methods = model.get('supportedGenerationMethods', [])
        
        # Check if it supports generateContent
        if 'generateContent' in supported_methods:
            compatible_models.append(model_name)
            print(f"✅ {model_name}")
            print(f"   Display Name: {display_name}")
            print(f"   Methods: {', '.join(supported_methods)}")
            print()
    
    print("=" * 80)
    print(f"\n📊 SUMMARY: {len(compatible_models)} models support generateContent\n")
    
    if compatible_models:
        print("🧪 Now testing each model with a simple prompt...\n")
        print("-" * 80)
        
        working_models = []
        
        for model_name in compatible_models:
            # Extract just the model name (remove 'models/' prefix)
            short_name = model_name.replace('models/', '')
            
            print(f"\n🔄 Testing: {short_name}")
            
            test_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"
            
            test_data = {
                "contents": [{
                    "parts": [{
                        "text": "Say 'Hello' in one word only."
                    }]
                }]
            }
            
            try:
                test_response = requests.post(test_url, json=test_data, timeout=10)
                test_response.raise_for_status()
                
                result = test_response.json()
                text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                
                print(f"   ✅ WORKS! Response: {text}")
                working_models.append(short_name)
                
            except Exception as e:
                error_msg = str(e)[:100]
                print(f"   ❌ Failed: {error_msg}...")
        
        print("\n" + "=" * 80)
        print("🎯 FINAL RESULTS")
        print("=" * 80)
        
        if working_models:
            print(f"\n✅ {len(working_models)} working model(s) found:\n")
            for model in working_models:
                print(f"   • {model}")
            
            print(f"\n💡 RECOMMENDED: Use '{working_models[0]}' in your gemini_service.py")
            print("\n📝 Update your code:")
            print(f"   self.model_name = '{working_models[0]}'")
        else:
            print("\n❌ No working models found")
            print("\n💡 Possible issues:")
            print("   1. API key doesn't have access to these models")
            print("   2. Billing not enabled on Google Cloud")
            print("   3. Regional restrictions")
    else:
        print("❌ No compatible models found for generateContent")
    
    print("\n" + "=" * 80)

except requests.exceptions.RequestException as e:
    print(f"\n❌ Network Error: {str(e)}")
    print("\n💡 Check your internet connection and API key")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print()
