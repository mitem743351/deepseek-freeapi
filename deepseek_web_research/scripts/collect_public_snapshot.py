"""Public-only collector. Run from a normal browser-authorized Windows environment.
It fetches only URLs entered in `allowlist.txt`, hashes response bodies, and stores no headers.
Do not add authenticated endpoints, credentials, cookie jars, or bypass logic.
"""
from __future__ import annotations
import hashlib, json, pathlib, urllib.request
ROOT=pathlib.Path(__file__).parents[1]; RAW=ROOT/'raw'; RAW.mkdir(exist_ok=True)
manifest=[]; seen={}
for line in (ROOT/'allowlist.txt').read_text().splitlines():
    url=line.strip()
    if not url or url.startswith('#'): continue
    try:
        r=urllib.request.urlopen(url, timeout=30)
        body=r.read(); digest=hashlib.sha256(body).hexdigest()
        if digest not in seen:
            name=f'{digest}.bin'; (RAW/name).write_bytes(body); seen[digest]=name
        manifest.append({'url':url,'type':'public_text','http_status':r.status,
          'content_type':r.headers.get_content_type(),'size':len(body),'hash_sha256':digest,
          'source':'public_browser_resource','stored_as':seen[digest]})
    except Exception as e:
        manifest.append({'url':url,'type':'public_text','http_status':None,'error':str(e),
          'source':'public_browser_resource'})
(ROOT/'snapshots'/'resource_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
