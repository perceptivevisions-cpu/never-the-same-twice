import asyncio,sys,json,time
from playwright.async_api import async_playwright
FILM=sys.argv[1];ENG=sys.argv[2];SEEDS=sys.argv[3].split(',')
B='http://localhost:8766/'
async def one(p,seed):
    args=["--autoplay-policy=document-user-activation-required"] if ENG=='chromium' else []
    b=await getattr(p,ENG).launch(args=args);pg=await b.new_page(viewport={"width":1280,"height":720});errs=[]
    pg.on("pageerror",lambda e:errs.append(str(e)[:140]))
    await pg.goto(B+FILM+'#diag'+('' if seed=='first' else '&v='+seed)+'&deal');await pg.wait_for_function("!document.getElementById('go').disabled",timeout=60000)
    await pg.click('#go');t0=time.time();await pg.wait_for_timeout(1500)
    total=await pg.evaluate("window.__plan.total");deal=await pg.evaluate("window.__plan.audio.deal")
    quietM=0;worstM=(0,0);quietA=0;worstA=0;n=0;notplaying=0;ended=None;lowfps=0
    while time.time()-t0<total+25:
        await pg.wait_for_timeout(2000);t=time.time()-t0
        s=json.loads(await pg.evaluate("JSON.stringify({p:document.body.classList.contains('playing'),lv:window.__d.level(),m:window.__d.st().media,ctx:window.__d.st().ctx,end:!document.getElementById('end').classList.contains('hide')})"))
        if not s['p']:
            ended=t;break
        n+=1
        if 3<t<total-9:
            if s['lv']['music']<1e-4:
                quietM+=2
                if quietM>worstM[0]: worstM=(quietM,round(t))
            else: quietM=0
            if s['lv']['all']<1e-4: quietA+=2;worstA=max(worstA,quietA)
            else: quietA=0
            if any('NOT PLAYING' in m for m in s['m']): notplaying+=1
    fin=json.loads(await pg.evaluate("JSON.stringify({end:!document.getElementById('end').classList.contains('hide'),log:window.__d.log,fb:window.__d.st().fb})"))
    await pg.wait_for_timeout(7000);fs=await pg.evaluate("!!document.fullscreenElement")
    r=dict(seed=seed,deal=deal[:60],total=round(total),ended_at=ended and round(ended),end_screen=fin['end'],left_fullscreen=not fs,longest_music_silence_s=worstM,longest_total_silence_s=worstA,samples=n,not_playing_samples=notplaying,backups=fin['fb'],errors=errs,log=[l for l in fin['log'] if 'start' not in l and 'audio running' not in l])
    print(json.dumps(r));await b.close();return r
async def main():
    async with async_playwright() as p:
        rs=await asyncio.gather(*[one(p,s) for s in SEEDS])
        json.dump(rs,open(f'/tmp/suite/soak_{ENG}_{SEEDS[0]}.json','w'))
asyncio.run(main())
