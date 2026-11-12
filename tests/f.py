import asyncio,sys,json
from playwright.async_api import async_playwright
FILM=sys.argv[1] if len(sys.argv)>1 else 'next.html'
B='http://localhost:8766/'
R=[]
def rec(ctx,name,ok,detail=''): R.append(('forced failure',ctx,name,'PASS' if ok else 'FAIL',str(detail)[:260]))
ST="JSON.stringify(Object.assign(window.__d.st(),{lv:window.__d.level(),log:window.__d.log.slice(-14),cls:document.body.className}))"
async def st(fr): return json.loads(await fr.evaluate(ST))
async def ready(fr,t=60000): await fr.wait_for_function("!document.getElementById('go').disabled",timeout=t)
async def ff(pg):
    for _ in range(40):
        fr=[f for f in pg.frames if f!=pg.main_frame and '8766' in f.url]
        if fr:return fr[0]
        await pg.wait_for_timeout(250)
ONLY="if(location.hostname==='127.0.0.1'||location.pathname.indexOf('next')>=0||location.pathname.indexOf('index')>=0){%s}"
async def case(p,name,init,after_s,check,host='t_art.html',route=None,cdp=None,args=None):
    b=await p.chromium.launch(args=args or ["--autoplay-policy=document-user-activation-required"])
    try:
        c=await b.new_context(viewport={"width":1280,"height":800});pg=await c.new_page();errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)[:140]))
        if init: await pg.add_init_script(ONLY%init)
        if route: await route(c)
        if cdp:
            await pg.goto('about:blank')
        await pg.goto(B+host+('?f='+FILM if host.startswith('t_') else ''))
        fr=await ff(pg) if host.startswith('t_') else pg.main_frame
        if cdp: await cdp(c,pg,fr)
        await ready(fr,120000);await fr.click('#go')
        res=[]
        for t in after_s:
            await pg.wait_for_timeout(int(t*1000));res.append(await st(fr))
        await check(name,res,pg,fr,errs)
    except Exception as e: rec(name,'TEST CRASHED',False,repr(e)[:220])
    await b.close()
music=lambda s:s['lv'] and s['lv']['music']>0.0005
async def main():
  async with async_playwright() as p:
    async def c1(n,r,pg,fr,errs):
        rec(n,'backup kicks in for every blocked piece',r[-1]['media'] and all('BACKUP(' in m for m in r[-1]['media']),r[-1]['media'])
        rec(n,'music is really coming out',music(r[-1]),r[-1]['lv']);rec(n,'film still playing, no errors','playing' in r[-1]['cls'] and not errs,errs)
        first=next((i for i,x in enumerate(r) if music(x)),None);rec(n,'music back within ~6 seconds of start',first is not None and first<=1,[x['lv'] for x in r])
    await case(p,'music players refuse to play (iPad-style block)',"const P=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){if((this.src||'').includes('.mp3'))return Promise.reject(new DOMException('blocked','NotAllowedError'));return P.call(this)}",[3,3,4],c1)
    async def c2(n,r,pg,fr,errs):
        rec(n,'silence detected and backup takes over',r[-1]['media'] and all('BACKUP(silent)' in m for m in r[-1]['media']),r[-1]['media']);rec(n,'music is really coming out',music(r[-1]),r[-1]['lv'])
    await case(p,'players "play" but send no sound (the static-only case)',"AudioContext.prototype.createMediaElementSource=function(el){return this.createGain()}",[6,6],c2)
    async def c3(n,r,pg,fr,errs):
        rec(n,'stuck piece replaced by backup',any('BACKUP(' in m for m in r[-1]['media']),r[-1]['media']);rec(n,'music is really coming out',music(r[-1]),r[-1]['lv'])
    async def stall(c):
        async def h(route):
            rq=route.request
            if rq.resource_type=='media' and 'unknown' in rq.url: return   # never answer: stream hangs
            await route.continue_()
        await c.route('**/*.mp3*',h)
    await case(p,'music stream hangs (bad connection mid-film)',None,[10,10],c3,route=stall)
    async def c4(n,r,pg,fr,errs):
        rec(n,'film still starts and plays','playing' in r[-1]['cls'],r[-1]['cls']);rec(n,'background sound still there',r[-1]['lv']['all']>0.0003,r[-1]['lv']);rec(n,'no crash',not errs,errs)
    async def gone(c): await c.route('**/unknown_*.mp3*',lambda route:route.fulfill(status=404,body='no'))
    await case(p,'two music files missing entirely',None,[9],c4,route=gone)
    async def c5(n,r,pg,fr,errs):
        rec(n,'film starts anyway within 3s (no hang)','playing' in r[0]['cls'],r[0]['cls']);rec(n,'"tap for sound" note appears',r[1]['hint'],r[1]['ctx'])
        t1=await fr.evaluate("window.__d.t()");await pg.wait_for_timeout(3000);t2=await fr.evaluate("window.__d.t()")
        rec(n,'picture keeps moving even with no sound (film does not freeze)',2.4<t2-t1<3.6 and t2>5,(t1,t2))
        await fr.evaluate("window.__allow=1");await fr.click('body',position={"x":300,"y":200},force=True);await pg.wait_for_timeout(2500);s=await st(fr)
        rec(n,'one tap brings sound back, note goes away',s['ctx']=='running' and not s['hint'] and s['lv']['all']>0.0003,(s['ctx'],s['hint'],s['lv']))
        await pg.wait_for_timeout(6000);s=await st(fr);sy=await fr.evaluate("window.__d.sync()")
        rec(n,'music joins in, in step with the picture',s['lv']['music']>0.0005 and sy<0.6 and any('playing' in m or 'BACKUP(' in m for m in s['media']),(s['lv'],sy,s['media'],s['log'][-4:]))
    await case(p,'browser keeps sound switched off',"const R=AudioContext.prototype.resume;AudioContext.prototype.resume=function(){if(!window.__allow){try{this.suspend()}catch(e){}return new Promise(()=>{})}return R.call(this)}",[3,2],c5)
    async def c5b(n,r,pg,fr,errs):
        t1=await fr.evaluate("window.__d.t()");await pg.wait_for_timeout(4000);t2=await fr.evaluate("window.__d.t()")
        rec(n,'film plays through silently instead of freezing','playing' in r[0]['cls'] and 3.3<t2-t1<4.7,(t1,t2));rec(n,'no errors',not errs,errs)
    await case(p,'computer with no working sound at all',"const R=AudioContext.prototype.resume;AudioContext.prototype.resume=function(){try{this.suspend()}catch(e){}return new Promise(()=>{})}",[4],c5b)
    async def c6(n,r,pg,fr,errs):
        rec(n,'film plays inside the box instead','playing' in r[0]['cls'] and not await pg.evaluate("!!document.fullscreenElement"),r[0]['cls']);rec(n,'music fine',music(r[0]),r[0]['lv']);rec(n,'no errors',not errs and not any('ERR' in l or 'REJ' in l for l in r[0]['log']),(errs,r[0]['log'][-4:]))
    await case(p,'site does not allow full screen',None,[8],c6,host='t_nofs.html')
    async def c7(n,r,pg,fr,errs): rec(n,'film plays with music','playing' in r[0]['cls'] and music(r[0]),(r[0]['cls'],r[0]['lv']));rec(n,'no errors',not errs,errs)
    await case(p,'private mode (browser storage blocked)',"Object.defineProperty(window,'localStorage',{get(){throw new DOMException('denied','SecurityError')}})",[8],c7)
    await case(p,'sound decoder that never answers',"const D=BaseAudioContext.prototype.decodeAudioData;BaseAudioContext.prototype.decodeAudioData=function(ab,ok,no){if(this instanceof OfflineAudioContext)return new Promise(()=>{});return D.call(this,ab,ok,no)}",[8],c7)
    async def c8(n,r,pg,fr,errs): rec(n,'loads, plays, music arrives','playing' in r[-1]['cls'] and music(r[-1]),(r[-1]['cls'],r[-1]['lv'],r[-1]['media']));rec(n,'no errors',not errs,errs)
    async def slow(c,pg,fr):
        s=await c.new_cdp_session(pg);await s.send('Network.enable');await s.send('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':1500*1024/8,'uploadThroughput':750*1024/8})
        for t in c.pages: pass
    await case(p,'slow connection (1.5 Mbit, like weak wifi)',None,[12,8],c8,host=FILM+'#diag',cdp=slow)
    # tab hidden mid-film
    async def c9(n,r,pg,fr,errs):
        await fr.evaluate("Object.defineProperty(document,'hidden',{get:()=>true,configurable:true});document.dispatchEvent(new Event('visibilitychange'))");await pg.wait_for_timeout(1500)
        e=await fr.evaluate("[!document.getElementById('end').classList.contains('hide'),document.body.classList.contains('playing')]");rec(n,'film ends cleanly, end screen shown',e[0] and not e[1],e)
        await fr.evaluate("Object.defineProperty(document,'hidden',{get:()=>false,configurable:true})");await fr.click('#again');await pg.wait_for_timeout(500);await fr.click('#go');await pg.wait_for_timeout(8000);s=await st(fr)
        rec(n,'next film plays normally with music','playing' in s['cls'] and music(s) and s['ctx']=='running',(s['cls'],s['lv']))
    await case(p,'viewer switches to another tab mid-film',None,[6],c9)
    # window resized repeatedly mid-film
    async def c10(n,r,pg,fr,errs):
        await pg.evaluate("document.exitFullscreen&&document.fullscreenElement&&document.exitFullscreen()");await pg.wait_for_timeout(600)
        bad=[]
        for w,h in [(700,900),(1600,500),(500,500),(1280,800)]:
            await pg.set_viewport_size({"width":w,"height":h});await pg.wait_for_timeout(900)
            cr=await fr.evaluate("(()=>{const r=document.getElementById('c').getBoundingClientRect();return [r.width,r.height,innerWidth,innerHeight].map(Math.round)})()")
            if abs(cr[0]/max(1,cr[1])-16/9)>0.03 or cr[0]>cr[2]+1 or cr[1]>cr[3]+1: bad.append(((w,h),cr))
        s=await st(fr);rec(n,'picture stays 16:9 and inside the player at every size',not bad,bad);rec(n,'film and music keep going','playing' in s['cls'] and music(s),s['lv']);rec(n,'no errors',not errs,errs)
    await case(p,'window resized over and over mid-film',None,[5],c10)
  json.dump(R,open('/tmp/suite/f.json','w'));f=[r for r in R if r[3]=='FAIL'];print('forced-failure checks',len(R),'failed',len(f))
  for r in f: print('  FAIL',r[1],'|',r[2],'|',r[4])
asyncio.run(main())
