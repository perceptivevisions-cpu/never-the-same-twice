import asyncio,sys,json,time
from playwright.async_api import async_playwright
FILM=sys.argv[2] if len(sys.argv)>2 else 'next.html'
ENG=sys.argv[1]
B='http://localhost:8766/'
IPH='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
IPAD='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
R=[]
AUDIO_OK=ENG!='firefox'
def rec(ctx,name,ok,detail=''):
    if not AUDIO_OK and any(k in name for k in ('sound','music')): return
    R.append((ENG,ctx,name,'PASS' if ok else 'FAIL',str(detail)[:230]))
async def film_frame(pg):
    for _ in range(40):
        fr=[f for f in pg.frames if f!=pg.main_frame and '8766' in f.url]
        if fr: return fr[0]
        await pg.wait_for_timeout(250)
    return pg.main_frame
async def ready(fr): await fr.wait_for_function("!document.getElementById('go').disabled",timeout=45000)
ST="JSON.stringify(Object.assign(window.__d.st(),{lv:window.__lvmax?window.__lvmax():window.__d.level(),log:window.__d.log.slice(-12),cls:document.body.className}))"
async def st(fr):
    await fr.evaluate("window.__lvmax=window.__lvmax||(()=>window.__d.level());window.__lvs=[]")
    for i in range(4):
        await fr.evaluate("window.__lvs.push(window.__d.level())");await asyncio.sleep(0.5)
    await fr.evaluate("window.__lvmax=()=>{const a=window.__lvs.filter(Boolean);if(!a.length)return null;return {all:Math.max(...a.map(x=>x.all)),music:Math.max(...a.map(x=>x.music))}}")
    return json.loads(await fr.evaluate(ST))
FITS="""(()=>{const out=[];for(const sel of ['#start .t1','#start .ver','#go']){const e=document.querySelector(sel);const r=e.getBoundingClientRect();const cs=getComputedStyle(e);if(cs.display==='none')continue;if(r.left<-1||r.top<-1||r.right>innerWidth+1||r.bottom>innerHeight+1)out.push(sel+' '+[r.left,r.top,r.right,r.bottom].map(Math.round))}return out})()"""
CAN="(()=>{const r=document.getElementById('c').getBoundingClientRect();return [Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height)]})()"
async def desktop(b,ctxname,url,w,h,embed=True):
    c=await b.new_context(viewport={"width":w,"height":h});pg=await c.new_page();errs=[]
    pg.on("pageerror",lambda e:errs.append(str(e)[:120]))
    try:
        await pg.goto(url);fr=await film_frame(pg) if embed else pg.main_frame
        await ready(fr);rec(ctxname,'loads, begin enabled',True)
        bad=await fr.evaluate(FITS);rec(ctxname,'start screen fits in player',not bad,bad)
        # double click begin
        await fr.click('#go');
        try: await fr.click('#go',timeout=700,force=True)
        except Exception: pass
        await pg.wait_for_timeout(3500);s=await st(fr)
        rec(ctxname,'film starts after begin','playing' in s['cls'],s['cls'])
        rec(ctxname,'double-click starts only one film',sum(1 for l in s['log'] if ' start ' in l)==1,[l for l in s['log'] if 'start' in l])
        fs=await pg.evaluate("!!document.fullscreenElement")
        if ENG!='webkit': rec(ctxname,'goes full screen on begin',fs)
        cr=await fr.evaluate(CAN);iw=await fr.evaluate("[innerWidth,innerHeight]")
        if fs: rec(ctxname,'full screen: picture fills the screen',cr[2]>=iw[0]-2 and cr[3]>=iw[1]-2,(cr,iw))
        await pg.wait_for_timeout(5500);s=await st(fr)
        t1=await fr.evaluate("window.__d.t()");await pg.wait_for_timeout(3000);t2=await fr.evaluate("window.__d.t()");sy=await fr.evaluate("window.__d.sync()")
        rec(ctxname,'picture is moving in real time',2.4<t2-t1<3.6,(t1,t2))
        if ENG!='firefox': rec(ctxname,'music in step with the picture (within %ss)'%('0.6' if ENG=='chromium' else '1.5'),sy<(0.6 if ENG=='chromium' else 1.5),sy)
        s=await st(fr)
        rec(ctxname,'sound engine running',s['ctx']=='running',s['ctx'])
        rec(ctxname,'sound output measured (any)',s['lv'] and s['lv']['all']>0.0005,s['lv'])
        rec(ctxname,'music output measured',s['lv'] and s['lv']['music']>0.0005,(s['lv'],s['media']))
        rec(ctxname,'music pieces playing (no NOT PLAYING)',s['media'] and all('NOT PLAYING' not in m for m in s['media']),s['media'])
        rec(ctxname,'no backup needed in normal case',s['fb']==0,s['media'])
        # X / END controls
        box=await pg.evaluate("(()=>{const f=document.getElementById('f');if(!f)return [0,0];const r=f.getBoundingClientRect();return [r.left,r.top]})()") if embed and not fs else [0,0]
        await pg.mouse.move(box[0]+200,box[1]+150);await pg.mouse.move(box[0]+240,box[1]+170);await pg.wait_for_timeout(700)
        vis=await fr.evaluate("['x','stop'].map(i=>{const e=document.getElementById(i),c=getComputedStyle(e);return +c.opacity>0.3&&c.pointerEvents!=='none'&&c.display!=='none'})")
        rec(ctxname,'corner button appears on mouse move',vis[0]);rec(ctxname,'END button appears on mouse move',vis[1])
        if fs:
            await fr.hover('#x',force=True);await fr.click('#x',force=True);await pg.wait_for_timeout(1200)
            fs2=await pg.evaluate("!!document.fullscreenElement");cr=await fr.evaluate(CAN)
            rec(ctxname,'X leaves full screen',not fs2)
            rec(ctxname,'after X the picture is 16:9 (not square)',abs(cr[2]/max(cr[3],1)-16/9)<0.03,cr)
            s=await st(fr);rec(ctxname,'film keeps playing after X','playing' in s['cls'])
            await pg.mouse.move(box[0]+210,box[1]+160);b2=await pg.evaluate("(()=>{const f=document.getElementById('f');if(!f)return [0,0];const r=f.getBoundingClientRect();return [r.left,r.top]})()") if embed else [0,0]
            await pg.mouse.move(b2[0]+220,b2[1]+120);await pg.mouse.move(b2[0]+260,b2[1]+140);await pg.wait_for_timeout(300)
            await fr.hover('#x',force=True);await fr.click('#x',force=True);await pg.wait_for_timeout(1200)
            rec(ctxname,'corner button goes back into full screen',await pg.evaluate("!!document.fullscreenElement"))
        # END
        b2=await pg.evaluate("(()=>{const f=document.getElementById('f');if(!f||document.fullscreenElement)return [0,0];const r=f.getBoundingClientRect();return [r.left,r.top]})()") if embed else [0,0]
        await pg.mouse.move(b2[0]+230,b2[1]+130);await pg.mouse.move(b2[0]+270,b2[1]+150);await pg.wait_for_timeout(500)
        await fr.hover('#stop',force=True);await fr.click('#stop',force=True);await pg.wait_for_timeout(1500)
        endv=await fr.evaluate("!document.getElementById('end').classList.contains('hide')&&!document.body.classList.contains('playing')")
        rec(ctxname,'END button ends the film, end screen shows',endv)
        home=await fr.evaluate("getComputedStyle(document.getElementById('home')).display")
        rec(ctxname,'end screen back-link '+('hidden inside site page' if embed else 'shown on own page'),(home=='none')==embed,home)
        # quick restart keeps full screen (old bug)
        await fr.click('#again');await pg.wait_for_timeout(500);await ready(fr);await fr.click('#go');await pg.wait_for_timeout(8500)
        s=await st(fr);R.append((ENG,ctxname,'debug','INFO',str(s['log'])))
        if ENG!='webkit': rec(ctxname,'quick restart: still full screen 8s later',await pg.evaluate("!!document.fullscreenElement"))
        rec(ctxname,'quick restart: playing with music','playing' in s['cls'] and s['lv']['music']>0.0005 and all('NOT PLAYING' not in m for m in s['media']),(s['lv'],s['media']))
        # natural-style finish leaves full screen by itself
        await fr.evaluate("window.__d.finish()");await pg.wait_for_timeout(7200)
        rec(ctxname,'film end: leaves full screen by itself',not await pg.evaluate("!!document.fullscreenElement"))
        # repeat plays
        okc=0
        for i in range(3):
            await fr.click('#again');await pg.wait_for_timeout(450);await fr.click('#go');await pg.wait_for_timeout(7500);s=await st(fr)
            if 'playing' in s['cls'] and (not AUDIO_OK or (s['ctx']=='running' and s['lv']['music']>0.0005 and all('NOT PLAYING' not in m for m in s['media']))): okc+=1
            await fr.evaluate("window.__d.finish()");await pg.wait_for_timeout(700)
        rec(ctxname,'3 more plays in a row all have music' if AUDIO_OK else '3 more plays in a row all start',okc==3,okc)
        rec(ctxname,'only one set of 10 music players in use',await fr.evaluate('window.__d.players()')==10,await fr.evaluate('window.__d.players()'))
        s=await st(fr);rec(ctxname,'no script errors',not errs and not any('ERR' in l or 'REJ' in l for l in s['log']),(errs,[l for l in s['log'] if 'ERR' in l or 'REJ' in l]))
    except Exception as e:
        rec(ctxname,'TEST CRASHED',False,repr(e)[:200])
    await c.close()
async def main():
    async with async_playwright() as p:
        args=["--autoplay-policy=document-user-activation-required"] if ENG=='chromium' else []
        kw={'firefox_user_prefs':{'media.autoplay.default':5,'media.autoplay.blocking_policy':0,'full-screen-api.allow-trusted-requests-only':False}} if ENG=='firefox' else {}
        specs0=[('own page 1440x800',B+FILM+'#diag',1440,800,False),('art-site style player 1440x900',B+'t_art.html?f='+FILM,1440,900,True),
              ('com-site style player 1260x690',B+'t_com.html?f='+FILM,1260,690,True),('com-site style player 1920x1080',B+'t_com.html?f='+FILM,1920,1080,True),
              ('small window 900x600 art style',B+'t_art.html?f='+FILM,900,600,True),('square window 800x800 own page',B+FILM+'#diag',800,800,False)]
        specs=[x for x in specs0 if len(sys.argv)<5 or sys.argv[4] in x[0]]
        sem=asyncio.Semaphore(int(sys.argv[3]) if len(sys.argv)>3 else 1)
        async def run(sp):
            async with sem:
                b=await getattr(p,ENG).launch(args=args,**kw)
                try: await desktop(b,*sp)
                finally: await b.close()
        await asyncio.gather(*[run(sp) for sp in specs])
    json.dump(R,open(f'/tmp/suite/a_{ENG}.json','w'))
    f=[r for r in R if r[3]=='FAIL'];print(ENG,'checks',len(R),'failed',len(f))
    for r in f: print('  FAIL',r[1],'|',r[2],'|',r[4])
asyncio.run(main())
