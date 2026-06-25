import urllib.request
import json

def main():
    url = "https://smart-attend-ai-20u4.onrender.com/openapi.json"
    print("Fetching deployed openapi.json...")
    try:
        response = urllib.request.urlopen(url)
        data = json.loads(response.read().decode('utf-8'))
        schemas = data.get("components", {}).get("schemas", {})
        session_create = schemas.get("SessionCreate", {})
        print("SessionCreate schema:")
        print(json.dumps(session_create, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
