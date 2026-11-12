import asyncio,sys,json
from playwright.async_api import async_playwright
FILM=sys.argv[1] if len(sys.argv)>1 else 'next.html'
B='http://localhost:8766/'
IPH='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
IPAD='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
AND='Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36'
R=[]
def rec(ctx,name,ok,detail=''): R.append(('phone/tablet',ctx,name,'PASS' if ok else 'FAIL',str(detail)[:230]))
ST="JSON.stringify(Object.assign(window.__d.st(),{lv:window.__d.level(),log:window.__d.log.slice(-12),cls:document.body.className}))"
async def st(fr): return json.loads(await fr.evaluate(ST))
async def ready(fr): await fr.wait_for_function("!document.getElementById('go').disabled",timeout=45000)
async def ff(pg):
    for _ in range(40):
        fr=[f for f in pg.frames if f!=pg.main_frame and '8766' in f.url]
        if fr:return fr[0]
        await pg.wait_for_timeout(250)
FITS="""(()=>{const out=[];for(const sel of ['#start .t1','#start .ver','#go']){const e=document.querySelector(sel);const r=e.getBoundingClientRect();if(getComputedStyle(e).display==='none')continue;if(r.left<-1||r.top<-1||r.right>innerWidth+1||r.bottom>innerHeight+1)out.push(sel+' '+[r.left,r.top,r.right,r.bottom].map(Math.round))}return out})()"""
NOFS="Element.prototype.requestFullscreen=undefined;Element.prototype.webkitRequestFullscreen=undefined;"
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(args=["--autoplay-policy=document-user-activation-required"])
    # ---------- iPhone inside each site's player (portrait) ----------
    for host,(w,h) in [('t_art.html',(390,844)),('t_com.html',(390,844))]:
      name='iPhone upright, '+('art' if 'art' in host else 'com')+'-style player'
      try:
        c=await b.new_context(viewport={"width":w,"height":h},user_agent=IPH,has_touch=True,is_mobile=True);pg=await c.new_page()
        await pg.add_init_script("if(window.self!==window.top){"+NOFS+"}")
        await pg.goto(B+host+'?f='+FILM+'&fq=from%3Dcom');
        if 'com' in host: await pg.add_style_tag(content="div{margin-left:0!important;padding:40px 39px!important}")
        fr=await ff(pg);await ready(fr)
        rec(name,'no "turn sideways" wall; start screen shows',not await fr.evaluate("document.getElementById('rotate').classList.contains('show')"))
        bad=await fr.evaluate(FITS);rec(name,'title, version and begin all fit in the small player',not bad,(bad,await fr.evaluate("[innerWidth,innerHeight]")))
        await fr.tap('#go');await pg.wait_for_timeout(2500)
        rec(name,'begin opens the film in its own window, remembering the site','from=com' in pg.url and '8766' in pg.url and 't_' not in pg.url,pg.url)
        await c.close()
      except Exception as e: rec(name,'TEST CRASHED',False,repr(e)[:200])
    # ---------- iPhone own window ----------
    for frm,site in [('com','jasonlindsey.com'),('art','jasonlindsey.art')]:
      name='iPhone film window (from '+frm+')'
      try:
        c=await b.new_context(viewport={"width":390,"height":844},user_agent=IPH,has_touch=True,is_mobile=True);pg=await c.new_page();errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)[:120]));await pg.add_init_script(NOFS)
        await pg.goto(B+FILM+'?from='+frm+'#diag');await ready(pg)
        await pg.wait_for_timeout(800)
        rec(name,'upright: asks to turn sideways, film waits',await pg.evaluate("document.getElementById('rotate').classList.contains('show')&&!document.body.classList.contains('playing')"))
        await pg.set_viewport_size({"width":844,"height":390});await pg.wait_for_timeout(700)
        rec(name,'turned sideways: prompt goes away',not await pg.evaluate("document.getElementById('rotate').classList.contains('show')"))
        bad=await pg.evaluate(FITS);rec(name,'sideways start screen fits',not bad,bad)
        await pg.tap('#go');await pg.wait_for_timeout(9000);s=await st(pg)
        rec(name,'film plays with music','playing' in s['cls'] and s['ctx']=='running' and s['lv']['music']>0.0005,(s['cls'],s['lv'],s['media']))
        cr=await pg.evaluate("(()=>{const r=document.getElementById('c').getBoundingClientRect();return [r.width,r.height,innerWidth,innerHeight].map(Math.round)})()")
        rec(name,'picture fills the phone screen edge to edge',cr[0]>=cr[2]-1 and cr[1]>=cr[3]-1,cr)
        # rotate upright mid-film pauses, sideways resumes
        await pg.set_viewport_size({"width":390,"height":844});await pg.wait_for_timeout(900);s1=await st(pg)
        await pg.set_viewport_size({"width":844,"height":390});await pg.wait_for_timeout(2500);s2=await st(pg)
        rec(name,'turning upright mid-film pauses; sideways resumes with music',s1['ctx']!='running' and s2['ctx']=='running' and s2['lv']['music']>0.0005 and not s2['hint'],(s1['ctx'],s2['ctx'],s2['lv'],s2['hint']))
        await pg.touchscreen.tap(400,200);await pg.wait_for_timeout(600)
        v=await pg.evaluate("['x','stop'].map(i=>{const e=document.getElementById(i),c=getComputedStyle(e);return [+c.opacity>0.3&&c.pointerEvents!=='none'&&c.display!=='none',e.textContent.trim()]})")
        rec(name,'tap shows an X (way out) and END',v[0][0] and v[1][0] and v[0][1]=='×',v)
        await pg.tap('#stop');await pg.wait_for_timeout(1500)
        hm=await pg.evaluate("[document.getElementById('home').textContent,document.getElementById('home').href,getComputedStyle(document.getElementById('home')).display,!document.getElementById('end').classList.contains('hide')]")
        rec(name,'end screen: "back to '+site+'" with the right link',hm[3] and hm[2]!='none' and site in hm[0] and site in hm[1],hm)
        await pg.tap('#again');await pg.wait_for_timeout(500);await pg.tap('#go');await pg.wait_for_timeout(3500);await pg.touchscreen.tap(400,200);await pg.wait_for_timeout(500)
        await pg.tap('#x');await pg.wait_for_timeout(2500)
        rec(name,'X takes you back to the '+frm+' page',site in pg.url,pg.url[:80]);rec(name,'no script errors',not errs,errs)
        await c.close()
      except Exception as e: rec(name,'TEST CRASHED',False,repr(e)[:200])
    # ---------- Android phone (has full screen) ----------
    name='Android phone, art-style player'
    try:
      c=await b.new_context(viewport={"width":412,"height":915},user_agent=AND,has_touch=True,is_mobile=True);pg=await c.new_page()
      await pg.goto(B+'t_art.html?f='+FILM);fr=await ff(pg);await ready(fr)
      bad=await fr.evaluate(FITS);rec(name,'start screen fits',not bad,bad)
      await fr.tap('#go');await pg.wait_for_timeout(2500)
      rec(name,'begin goes full screen (film then asks to turn sideways)',await pg.evaluate("!!document.fullscreenElement"),await fr.evaluate("document.body.className+' rotate:'+document.getElementById('rotate').classList.contains('show')"))
      await c.close()
    except Exception as e: rec(name,'TEST CRASHED',False,repr(e)[:200])
    # ---------- iPad ----------
    for label,vw,vh,sw,sh,host in [('iPad normal (art-style)',1080,810,810,1080,'t_art.html'),('iPad laid out too big, as in tester screenshots (com-style)',1280,960,810,1080,'t_com.html'),('iPad upright (art-style)',810,1080,810,1080,'t_art.html')]:
      try:
        c=await b.new_context(viewport={"width":vw,"height":vh},user_agent=IPAD,has_touch=True);pg=await c.new_page();errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)[:120]))
        await pg.add_init_script("Object.defineProperty(navigator,'maxTouchPoints',{get:()=>5});Object.defineProperty(screen,'width',{get:()=>%d});Object.defineProperty(screen,'height',{get:()=>%d});"%(sw,sh))
        await pg.goto(B+host+'?f='+FILM);fr=await ff(pg);await ready(fr)
        rec(label,'recognised as an iPad',await fr.evaluate("document.body.classList.contains('ipad')"))
        bad=await fr.evaluate(FITS);rec(label,'start screen fits',not bad,bad)
        await fr.tap('#go');await pg.wait_for_timeout(9000);s=await st(fr)
        fs=await pg.evaluate("!!document.fullscreenElement")
        rec(label,'begin: full screen and playing',fs and 'playing' in s['cls'],s['cls'])
        rec(label,'music measured',s['ctx']=='running' and s['lv']['music']>0.0005 and all('NOT PLAYING' not in m for m in s['media']),(s['lv'],s['media']))
        g=await fr.evaluate("(()=>{const r=document.getElementById('c').getBoundingClientRect();const L=Math.max(screen.width,screen.height),S=Math.min(screen.width,screen.height);const land=innerWidth>=innerHeight;return {c:[r.left,r.top,r.right,r.bottom].map(Math.round),scr:[land?L:S,land?S:L],tf:document.body.style.transform,xd:getComputedStyle(document.getElementById('x')).display}})()")
        rec(label,'whole picture sits inside the real screen (not cut off)',g['c'][0]>=-1 and g['c'][1]>=-1 and g['c'][2]<=g['scr'][0]+1 and g['c'][3]<=g['scr'][1]+1,g)
        rec(label,'picture fills the real screen',g['c'][2]-g['c'][0]>=g['scr'][0]-2 and g['c'][3]-g['c'][1]>=g['scr'][1]-2,g)
        rec(label,'only one X in full screen (ours hidden)',g['xd']=='none',g['xd'])
        tb=await fr.evaluate("(()=>{const e=document.getElementById('stop');return 1})()")
        await pg.evaluate("document.exitFullscreen()");await pg.wait_for_timeout(1500)
        g2=await fr.evaluate("(()=>{const r=document.getElementById('c').getBoundingClientRect();return {c:[r.width,r.height].map(Math.round),tf:document.body.style.transform,xd:getComputedStyle(document.getElementById('x')).display}})()")
        rec(label,'after leaving full screen: 16:9, sizing reset, our button is back',abs(g2['c'][0]/max(1,g2['c'][1])-16/9)<0.03 and not g2['tf'] and g2['xd']!='none',g2)
        s=await st(fr);rec(label,'no script errors',not errs and not any('ERR' in l for l in s['log']),(errs,s['log'][-3:]))
        await c.close()
      except Exception as e: rec(label,'TEST CRASHED',False,repr(e)[:200])
    await b.close()
  json.dump(R,open('/tmp/suite/m.json','w'));f=[r for r in R if r[3]=='FAIL'];print('phone/tablet checks',len(R),'failed',len(f))
  for r in f: print('  FAIL',r[1],'|',r[2],'|',r[4])
asyncio.run(main())
