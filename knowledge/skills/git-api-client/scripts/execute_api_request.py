import sys
import os
import json
import yaml
import subprocess
import re

def execute_request(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    with open(file_path, 'r') as f:
        content = f.read()

    # Simple regex to split frontmatter and body
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if not match:
        print("Error: Invalid Markdown format. Missing frontmatter.")
        return

    frontmatter_raw = match.group(1)
    body = match.group(2).strip()

    try:
        config = yaml.safe_load(frontmatter_raw)
    except yaml.YAMLError as e:
        print(f"Error: YAML parsing failed: {e}")
        return

    method = config.get('method', 'GET').upper()
    url = config.get('url')
    headers = config.get('headers', {})

    if not url:
        print("Error: 'url' is required in frontmatter.")
        return

    # Replace environment variables in URL, headers, and body
    def replace_env(text):
        if not isinstance(text, str): return text
        return re.sub(r'\{\{(.*?)\}\}', lambda m: os.environ.get(m.group(1), m.group(0)), text)

    url = replace_env(url)
    for k, v in headers.items():
        headers[k] = replace_env(v)
    body = replace_env(body)

    # Build curl command
    curl_cmd = ['curl', '-s', '-i', '-X', method, url]
    
    for k, v in headers.items():
        curl_cmd.extend(['-H', f"{k}: {v}"])

    if body and method in ['POST', 'PUT', 'PATCH']:
        curl_cmd.extend(['-d', body])

    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
        
        output = result.stdout
        if result.stderr:
            output += f"\n--- Stderr ---\n{result.stderr}"
            
        # Truncate if too long
        max_lines = 100
        lines = output.splitlines()
        if len(lines) > max_lines:
            print("\n".join(lines[:max_lines]))
            print(f"\n... [TRUNCATED {len(lines) - max_lines} LINES] ...")
        else:
            print(output)

    except subprocess.TimeoutExpired:
        print("Error: Request timed out.")
    except Exception as e:
        print(f"Error: Execution failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python execute_api_request.py <path_to_markdown_file>")
    else:
        execute_request(sys.argv[1])
