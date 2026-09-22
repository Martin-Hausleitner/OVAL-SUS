#!/usr/bin/env python3
"""Reproducible browser smoke tests. Requires Playwright and Google Chrome.
python3 -m pip install playwright
python3 tests/smoke.py
python3 tests/smoke.py --url https://martin-hausleitner.github.io/OVAL-SUS/ --tag live
Test hooks are used to freeze bots and navigate the real game; screenshots are
browser captures, not generated artwork. Physical mobile devices are not tested.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import platform
import sys
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--url', default=(ROOT / 'index.html').as_uri())
parser.add_argument('--tag', default='local')
args = parser.parse_args()
if args.tag not in ('local', 'live'):
    parser.error('--tag must be local or live')
u = urlsplit(args.url)
query = dict(parse_qsl(u.query))
query['test'] = '1'
url = urlunsplit((u.scheme, u.netloc, u.path, urlencode(query), u.fragment))
checks, errors, captures = [], [], []

def check(name, passed, details=None):
    checks.append({'name': name, 'pass': bool(passed), 'details': details})
    print(('PASS ' if passed else 'FAIL ') + name, flush=True)

def screenshot(page, name):
    path = ROOT / 'screenshots' / (name + '.png')
    page.screenshot(path=str(path), full_page=True)
    captures.append({'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='chrome', headless=True)
    version = browser.version
    try:
        for name, width, height, mobile in [('desktop',1440,900,False),('mobile',390,844,True),('landscape',844,390,True)]:
            context = browser.new_context(viewport={'width':width,'height':height}, device_scale_factor=1, is_mobile=mobile, has_touch=mobile, locale='de-AT')
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            response = page.goto(url, wait_until='load', timeout=60000)
            page.wait_for_function('!!window.__OVAL_TEST__ && document.querySelector("#world").width > 0', timeout=30000)
            page.wait_for_timeout(650)
            check(name+' canvas initialized', page.locator('#world').evaluate('(c)=>c.width>0&&c.height>0'))
            check(name+' lobby fits viewport', page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
            if name in ('desktop','mobile'):
                screenshot(page, name+'-lobby')
            check(name+' 32 skins preserved', page.evaluate('window.__OVAL_TEST__.skins.length === 32'))
            page.evaluate("Object.assign(window.__OVAL_TEST__.settings,{role:'crew',size:12,difficulty:'easy'})")
            page.click('#startBtn')
            page.click('#introGo')
            page.wait_for_function('window.__OVAL_TEST__.game.phase === "play"')
            page.evaluate('window.__OVAL_TEST__.freezeBots()')
            check(name+' round starts with 12 actors', page.evaluate('window.__OVAL_TEST__.game.actors.length===12'))
            check(name+' all 9 task stations reachable', page.evaluate('window.__OVAL_TEST__.connectivity().every(t=>t.walkable&&t.path>0)'))
            before = page.evaluate('window.__OVAL_TEST__.game.actors[0].x')
            page.keyboard.down('a')
            page.wait_for_timeout(200)
            page.keyboard.up('a')
            after = page.evaluate('window.__OVAL_TEST__.game.actors[0].x')
            check(name+' keyboard movement', abs(after-before)>1, {'distance':round(abs(after-before),2)})
            check(name+' gameplay fits viewport', page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
            bounds = page.evaluate('''()=>['useBtn','reportBtn','mapBtn','photoBtn','graphicsBtn'].map(id=>{const e=document.getElementById(id),r=e.getBoundingClientRect();return {id,visible:r.width>0&&r.height>0,within:r.left>=-1&&r.top>=-1&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1}})''')
            check(name+' action buttons in viewport', all(b['within'] and b['visible'] for b in bounds), bounds)
            page.evaluate('''()=>{const t=window.__OVAL_TEST__;const goal=t.tasks.find(t=>t.id==='stamp');t.goTo(goal);for(let i=0;i<1200&&t.game.actors[0].path.length;i++)t.updateGame(.03);t.freezeBots();}''')
            page.wait_for_timeout(500)
            proximity = page.evaluate('''()=>{const t=window.__OVAL_TEST__,p=t.game.actors[0],a=t.tasks.find(t=>t.id==='stamp');return Math.hypot(p.x-a.x,p.y-a.y)}''')
            check(name+' real path reaches Oval Office task', proximity<35, {'distance':round(proximity,2)})
            screenshot(page,name+'-gameplay')
            if name=='desktop':
                page.click('#graphicsBtn')
                page.click('[data-light="night"]')
                page.evaluate('window.__OVAL_TEST__.closeModal()')
                page.wait_for_timeout(350)
                check('night theme switches',page.evaluate('document.documentElement.dataset.light === "night"'))
                screenshot(page,'desktop-night')
                page.click('#lightQuick')
                page.click('#photoBtn')
                page.wait_for_selector('#saveCapture')
                check('photo mode uses actual canvas PNG',page.locator('.capture-preview').evaluate('(e)=>e.src.startsWith("data:image/png;base64,")'))
                page.evaluate('window.__OVAL_TEST__.closeModal()')
            page.evaluate("window.__OVAL_TEST__.openTask(window.__OVAL_TEST__.tasks.find(t=>t.id==='wires'))")
            page.wait_for_selector('#taskArea')
            check(name+' wire minigame opens',page.evaluate('window.__OVAL_TEST__.task.type === "wires"'))
            if name=='mobile': screenshot(page,'mobile-minigame')
            context.close()
    except Exception as exc:
        check('browser test completes',False,{'error':str(exc)})
    finally:
        browser.close()
check('no unhandled JavaScript errors',not errors,errors)
report={'artifact':{'file':'index.html','sha256':hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest()},'environment':{'browser':'Google Chrome '+version,'platform':platform.platform(),'mode':'Headless Chrome with isolated profiles; mobile viewport and touch emulation','url':args.url if u.scheme != 'file' else 'index.html (local file)','generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'not_tested':['Native Safari','Physical iOS and Android devices','Online multiplayer (not implemented)']},'checks':checks,'errors':errors,'screenshots':captures,'summary':{'passed':sum(c['pass'] for c in checks),'total':len(checks)}}
(ROOT/'evidence'/('publish-smoke-'+args.tag+'.json')).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(report['summary']),flush=True)
sys.exit(0 if all(c['pass'] for c in checks) else 1)
