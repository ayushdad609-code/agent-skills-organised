---
name: shadcn-registry-extractor
description: Extract React components from Shadcn-style JSON registries directly to disk using curl and python to bypass context truncation limits.
---

# Shadcn-Style Registry Extractor

When a user requests to use a component from a library that uses a Shadcn-style registry (e.g., VengenceUI, MagicUI, Aceternity) but lacks a dedicated CLI—or if the CLI fails—do NOT attempt to read the HTML docs or use `read_url_content` on the `.json` blobs, as the code strings are too large and will be truncated in your context window.

Follow this workflow instead:

1. **Locate the Registry**: Find the raw URL for the component's JSON file in the source repository (typically under `public/r/` or `registry/`).
2. **Fetch and Extract Directly to Disk**:
   Use the `run_command` tool to execute a script that downloads the JSON via `curl`, parses it, and writes the `content` directly to the `src/components/ui/` directory.

   Example script:
   ```bash
   mkdir -p src/components/ui
   python3 -c "
   import json, urllib.request, os
   urls = [
       'https://raw.githubusercontent.com/Ashutoshx7/VengenceUI/main/public/r/image-trail.json'
   ]
   for url in urls:
       req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
       data = json.loads(urllib.request.urlopen(req).read())
       for f in data.get('files', []):
           out_path = os.path.join('src/components/ui', os.path.basename(f['path']))
           with open(out_path, 'w') as out:
               out.write(f['content'])
           print(f'Wrote {out_path}')
   "
   ```
3. **Handle Dependencies & Utils**:
   - Ensure `clsx` and `tailwind-merge` are installed: `npm i clsx tailwind-merge`
   - If `src/lib/utils.ts` doesn't exist, create it with the standard `cn` utility.
   - Install `framer-motion` and `lucide-react` if required.
4. **Fix Import Paths**:
   If the project doesn't use path aliases (e.g., `@/lib/utils`), run a `sed` command to fix the imports in the downloaded components:
   ```bash
   sed -i 's|@/lib/utils|../../lib/utils|g' src/components/ui/*.tsx
   ```
