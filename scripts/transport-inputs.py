#!/usr/bin/env python3
"""Index network API spellings in the hashed sources selected by an iOS Release build."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from source_state import require_source_state

# This is a source-navigation index, not a call graph. Include C headers and
# generated code, preserve comments and wrappers, and label every match as lexical.
PATTERNS = {
    'urlsession-task-or-stream': r'\b(?:dataTask|downloadTask|uploadTask|webSocketTask|bytes)\s*\(\s*(?:with|for|from)\s*:',
    'async-data-or-download': r'\.(?:data|download|upload)\s*\(\s*(?:for|from)\s*:',
    'network-framework': r'\b(?:NWConnection|NWListener|nw_connection_create|nw_listener_create)\s*\(',
    'socket-api': r'\b(?:socket|connect|sendto|recvfrom|SSL_connect|CFStreamCreatePairWithSocketToHost)\s*\(',
    'webview-load': r'\b(?:WKWebView|loadHTMLString|loadFileURL)\s*\(',
    'synchronous-url-read': r'\b(?:Data|NSData|String)\s*\(\s*contentsOf(?:URL)?\s*:',
}
def matches(text):
    rows=[]
    for kind,pattern in PATTERNS.items():
        for m in re.finditer(pattern,text):
            rows.append({'line':text.count('\n',0,m.start())+1,'kind':kind})
    return sorted(rows,key=lambda r:(r['line'],r['kind']))

def main():
    p=argparse.ArgumentParser()
    for name in ('source','derived','inputs','output'):p.add_argument(name,type=Path)
    a=p.parse_args()
    manifest=json.loads(a.inputs.read_bytes())
    pin=require_source_state(a.source,manifest['source_commit'])
    if manifest['status']!='passed' or manifest['check']!='release-inputs':
        raise ValueError('A successful source trace is required')
    derived=a.derived.resolve()
    roots={'application':a.source.resolve(),'package':derived/'SourcePackages/checkouts',
           'generated':derived/'Build/Intermediates.noindex','artifact':derived/'SourcePackages/artifacts','product':derived/'Build/Products'}
    rows=[];scanned=0;binary_modules=[]
    for entry in manifest['files']:
        prefix,name=entry['path'].split('/',1)
        root=roots[prefix]
        file=(root/name).resolve(strict=True)
        if not file.is_relative_to(root) or hashlib.sha256(file.read_bytes()).hexdigest()!=entry['sha256']:
            raise ValueError('Source identity mismatch: '+entry['path'])
        if file.suffix == '.pcm':
            binary_modules.append(entry['path'])
            continue
        findings=matches(file.read_text())
        scanned+=1
        if findings:rows.append({'path':entry['path'],'sha256':entry['sha256'],'targets':entry['targets'],'matches':findings})
    result={'source_commit':pin,'build_description':manifest['build_description'],'files_checked':scanned,'hashed_precompiled_modules':binary_modules,
            'paths_with_matches':len(rows),'patterns':PATTERNS,'entries':rows,
            'scope':'Lexical candidates in compiler-selected source and non-system Clang dependencies. Includes comments, wrappers and local file IO. Excludes opaque binaries, resources, dynamic dispatch and indirect or differently spelled calls. Does not confer manual review credit.'}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(scanned,'compiler inputs;',len(rows),'paths with lexical candidates')
if __name__=='__main__':main()
