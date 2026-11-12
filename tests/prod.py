import asyncio,sys,json
from playwright.async_api import async_playwright
ENG=sys.argv[1];R=[]
def rec(c,n,ok,d=''): R.append((ENG+' live site',c,n,'PASS' if ok else 'FAIL',str(d)[:240]))
IPH='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
async def ff(pg):
    for _ in range(80):
        fr=[f for f in pg.frames if 'film.jasonlindsey' in f.url]
        if fr:return fr[0]
        await pg.wait_for_timeout(250)
async def main():
  async with async_playwright() as p:
    b=await getattr(p,ENG).launch(args=["--autoplay-policy=document-user-activation-required"] if ENG=='chromium' else [])
    for site,url,frm in [('jasonlindsey.art film page','https://www.jasonlindsey.art/nobody-remembers','art'),('jasonlindsey.com film page','https://jasonlindsey.com/Short-Films/Nobody-Remembers/1','com')]:
      try:
        pg=await b.new_page(viewport={"width":1440,"height":860});errs=[];pg.on("pageerror",lambda e:errs.append(str(e)[:120]))
        await pg.goto(url,wait_until="domcontentloaded",timeout=60000);fr=await ff(pg)
        await fr.wait_for_function("!document.getElementById('go').disabled",timeout=90000)
        r=await pg.evaluate("(()=>{const f=document.querySelector('iframe[src*=\"film.jasonlindsey\"]');const q=f.getBoundingClientRect();return [q.width,q.height].map(Math.round)})()")
        rec(site,'player is 16:9 on the page',abs(r[0]/r[1]-16/9)<0.03 and r[0]>300,r)
        for i in range(5): await fr.click('#start .ver',force=True)
        await pg.wait_for_timeout(1200);d=await fr.evaluate("(document.getElementById('diag')||{}).textContent||''")
        rec(site,'running the new build',('build r4' in d),d[:40]);rec(site,'film knows which site it is on',('from '+frm) in d,d[:60])
        await fr.click('#go');await pg.wait_for_timeout(9000)
        s=json.loads(await fr.evaluate("JSON.stringify(Object.assign(window.__d.st(),{lv:window.__d.level(),cls:document.body.className,t:window.__d.t(),log:window.__d.log.slice(-6)}))"))
        t2=None;await pg.wait_for_timeout(3000);t2=await fr.evaluate("window.__d.t()")
        rec(site,'begin: film playing, picture moving','playing' in s['cls'] and 2.4<t2-s['t']<3.6,(s['cls'],s['t'],t2))
        if ENG!='firefox':
            rec(site,'sound running, music measured',s['ctx']=='running' and s['lv'] and s['lv']['music']>0.0005,(s['ctx'],s['lv'],s['media']))
            rec(site,'no backup needed',s['fb']==0,s['media'])
        if ENG=='chromium': rec(site,'full screen on begin',await pg.evaluate("!!document.fullscreenElement"))
        rec(site,'no errors',not errs and not any('ERR' in l or 'REJ' in l for l in s['log']),(errs,s['log']))
        await pg.close()
      except Exception as e: rec(site,'TEST CRASHED',False,repr(e)[:200])
    if ENG=='chromium':
      for site,url,frm in [('iPhone on jasonlindsey.com','https://jasonlindsey.com/Short-Films/Nobody-Remembers/1','com'),('iPhone on jasonlindsey.art','https://www.jasonlindsey.art/nobody-remembers','art')]:
        try:
          c=await b.new_context(viewport={"width":390,"height":844},user_agent=IPH,has_touch=True,is_mobile=True);pg=await c.new_page()
          await pg.add_init_script("if(location.hostname==='film.jasonlindsey.art'){Element.prototype.requestFullscreen=undefined;Element.prototype.webkitRequestFullscreen=undefined;}")
          await pg.goto(url,wait_until="domcontentloaded",timeout=60000);fr=await ff(pg);await fr.wait_for_function("!document.getElementById('go').disabled",timeout=90000)
          bad=await fr.evaluate("(()=>{const out=[];for(const sel of ['#start .t1','#go']){const r=document.querySelector(sel).getBoundingClientRect();if(r.left<-1||r.top<-1||r.right>innerWidth+1||r.bottom>innerHeight+1)out.push(sel)}return out})()")
          rec(site,'start screen fits in the page player',not bad,bad)
          await fr.tap('#go');await pg.wait_for_timeout(4000)
          rec(site,'begin opens film window that remembers the site',pg.url.startswith('https://film.jasonlindsey.art/') and ('from='+frm) in pg.url,pg.url)
          await pg.set_viewport_size({"width":844,"height":390});await pg.wait_for_function("!document.getElementById('go').disabled",timeout=90000)
          h=await pg.evaluate("[document.getElementById('home').textContent,document.getElementById('home').href]");rec(site,'end-screen link points back to the right site',('jasonlindsey.'+frm) in h[0] and ('jasonlindsey.'+frm) in h[1],h)
          await c.close()
        except Exception as e: rec(site,'TEST CRASHED',False,repr(e)[:200])
      pg=await b.new_page(viewport={"width":1440,"height":860})
      await pg.goto('https://jasonlindsey.com/Short-Films/thumbs',wait_until="domcontentloaded",timeout=60000);await pg.wait_for_timeout(7000);t=await pg.evaluate("document.body.innerText")
      names=['NOBODY REMEMBERS','UNFINISHED','BREAKING ICE','IT\'S TIME','MUSSEL GRUBBING','CANCER SURVIVOR','THANK YOU MOTHER EARTH'];pos=[t.find(n) for n in names]
      rec('jasonlindsey.com Short Films','all 7 films listed, in order',all(x>=0 for x in pos) and pos==sorted(pos),pos)
      await pg.goto('https://www.jasonlindsey.art/',wait_until="domcontentloaded",timeout=60000);await pg.wait_for_timeout(6000);t=(await pg.evaluate("document.body.innerText")).upper()
      rec('jasonlindsey.art home','Nobody Remembers in menu / home page',t.count('NOBODY REMEMBERS')>=1,t.count('NOBODY REMEMBERS'))
    await b.close()
  json.dump(R,open(f'/tmp/suite/prod_{ENG}.json','w'));f=[r for r in R if r[3]=='FAIL'];print(ENG,'live-site checks',len(R),'failed',len(f))
  for r in f: print('  FAIL',r[1],'|',r[2],'|',r[4])
asyncio.run(main())
