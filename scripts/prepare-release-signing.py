#!/usr/bin/env python3
"""Prepare unique package id + own signing key for Telegram Accessible.

Also disables minifyEnabled and shrinkResources specifically in
buildTypes.release, without accidentally changing signingConfigs.release
or standalone.
"""
from pathlib import Path
import base64, copy, json, os, re, subprocess, sys

ROOT=Path("telegram")
GP=ROOT/"gradle.properties"
KS_DIR=ROOT/"TMessagesProj"/"config"
KS_PATH=KS_DIR/"a11y-release.keystore"
DEFAULT_PACKAGE="org.telegram.messenger.accessible"
DEFAULT_ALIAS="a11ykey"
DEFAULT_PASS="telegram-a11y-local"

def set_prop(text,key,value):
    pat=rf"(?m)^{re.escape(key)}=.*$"
    if re.search(pat,text):
        return re.sub(pat,f"{key}={value}",text,count=1)
    return text.rstrip()+f"\n{key}={value}\n"

def patch_google_services(package):
    files=list(ROOT.rglob("google-services.json"))
    if not files:
        print("WARN: no google-services.json found"); return
    for path in files:
        try: data=json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"WARN: skip {path}: {e}"); continue
        clients=data.get("client") or []
        names=[]
        for c in clients:
            try: names.append(c["client_info"]["android_client_info"]["package_name"])
            except Exception: pass
        if package in names or not clients: continue
        new_c=copy.deepcopy(clients[0])
        try: new_c["client_info"]["android_client_info"]["package_name"]=package
        except Exception: continue
        clients.append(new_c); data["client"]=clients
        path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
        print(f"google-services.json + client {package}: {path}")

def find_block(text,name,start=0):
    m=re.search(rf"(?m)^[ \t]*{re.escape(name)}[ \t]*\{{",text[start:])
    if not m: return None
    s=start+m.start(); op=text.find("{",s); depth=0
    for i in range(op,len(text)):
        if text[i]=="{": depth+=1
        elif text[i]=="}":
            depth-=1
            if depth==0: return s,i+1
    return None

def patch_release_build_type(path):
    text=path.read_text(encoding="utf-8")
    outer=find_block(text,"buildTypes")
    if not outer:
        print("WARN: buildTypes block not found"); return
    inner=find_block(text,"release",outer[0])
    if not inner or inner[0]>=outer[1]:
        print("WARN: buildTypes.release block not found"); return
    s,e=inner
    block=text[s:e]
    indent=re.search(r"(?m)^([ \t]*)release\s*\{",block)
    indent=(indent.group(1) if indent else "")+"    "
    changed=False
    def replace_or_insert(setting,value,comment):
        nonlocal block,changed
        pat=rf"(?m)^([ \t]*){re.escape(setting)}\s+(?:true|false)\s*$"
        if re.search(pat,block):
            block=re.sub(pat,lambda m:f"{m.group(1)}{comment}\n{m.group(1)}{setting} {value}",block,count=1)
            changed=True
        elif not re.search(rf"(?m)^\s*{re.escape(setting)}\s+",block):
            block=block[:-1]+f"{indent}{comment}\n{indent}{setting} {value}\n}}"
            changed=True
    replace_or_insert("minifyEnabled","false","// a11y-fork: release no minify")
    replace_or_insert("shrinkResources","false","// a11y-fork: release no resource shrinking")
    if changed:
        path.write_text(text[:s]+block+text[e:],encoding="utf-8")
        print("buildTypes.release minifyEnabled=false, shrinkResources=false OK")

def main():
    if not GP.exists():
        print("ERROR: gradle.properties missing",file=sys.stderr); return 1
    package=os.environ.get("A11Y_APP_PACKAGE",DEFAULT_PACKAGE).strip() or DEFAULT_PACKAGE
    store_pass=os.environ.get("A11Y_STORE_PASSWORD",DEFAULT_PASS).strip() or DEFAULT_PASS
    key_pass=os.environ.get("A11Y_KEY_PASSWORD",store_pass).strip() or store_pass
    alias=os.environ.get("A11Y_KEY_ALIAS",DEFAULT_ALIAS).strip() or DEFAULT_ALIAS
    b64=os.environ.get("A11Y_KEYSTORE_BASE64","").strip()
    KS_DIR.mkdir(parents=True,exist_ok=True)
    if b64:
        KS_PATH.write_bytes(base64.b64decode(b64))
        print(f"Restored keystore from A11Y_KEYSTORE_BASE64 ({KS_PATH.stat().st_size} bytes)")
    elif not KS_PATH.exists():
        subprocess.check_call(["keytool","-genkeypair","-v","-keystore",str(KS_PATH),"-alias",alias,
            "-keyalg","RSA","-keysize","2048","-validity","10000","-storepass",store_pass,
            "-keypass",key_pass,"-dname","CN=Telegram Accessible, OU=A11y, O=TelegramA11y, L=Internet, ST=NA, C=IR"])
        print(f"Generated new keystore at {KS_PATH}")
    else: print(f"Using existing keystore {KS_PATH}")
    gp=GP.read_text(encoding="utf-8")
    for k,v in [("APP_PACKAGE",package),("RELEASE_STORE_PASSWORD",store_pass),
                ("RELEASE_KEY_PASSWORD",key_pass),("RELEASE_KEY_ALIAS",alias)]:
        gp=set_prop(gp,k,v)
    GP.write_text(gp,encoding="utf-8")
    patch_google_services(package)
    app=ROOT/"TMessagesProj_App"/"build.gradle"
    if app.exists():
        t=app.read_text(encoding="utf-8")
        old='storeFile file("../TMessagesProj/config/release.keystore")'
        new='storeFile file("../TMessagesProj/config/a11y-release.keystore") // a11y-fork unique signing'
        if old in t: t=t.replace(old,new); print("Signing path -> a11y-release.keystore OK")
        if 'applicationIdSuffix ".beta"' in t:
            t=t.replace('applicationIdSuffix ".beta"','// a11y-fork: no beta suffix\n            // applicationIdSuffix ".beta"',1)
        app.write_text(t,encoding="utf-8")
        patch_release_build_type(app)
    else: print("WARN: TMessagesProj_App/build.gradle missing")
    print("prepare-release-signing done"); return 0

if __name__=="__main__":
    raise SystemExit(main())
