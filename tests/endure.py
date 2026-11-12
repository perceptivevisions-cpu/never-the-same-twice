import asyncio,sys,json
from playwright.async_api import async_playwright
FILM=sys.argv[1];N=int(sys.argv[2]);ENG=sys.argv[3] if len(sys.argv)>3 else 'chromium'
async def main():
  async with async_playwright() as p:
    b=await getattr(p,ENG).launch(args=["--autoplay-policy=document-user-activation-required"] if ENG=='chromium' else []);pg=await b.new_page(viewport={"width":1100,"height":620});errs=[];cons=[]
    pg.on("pageerror",lambda e:errs.append(str(e)[:120]));pg.on("console",lambda m:(m.type in('error','warning')) and cons.append(m.text[:110]))
    await pg.add_init_script("window.__pl=0;window.__rej=0;const P=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){const r=P.call(this);if((this.currentSrc||this.src||'').includes('.mp3')){r.then(()=>{window.__pl++}).catch(e=>{if(e.name!=='AbortError')window.__rej++})}return r};const C=window.Audio;let n=0;window.Audio=function(){n++;window.__made=n;return new C()}")
    await pg.goto('http://localhost:8766/'+FILM);await pg.wait_for_function("!document.getElementById('go').disabled",timeout=60000)
    res=[]
    for i in range(N):
        await pg.evaluate("window.__pl=0;window.__rej=0");await pg.click('#go');await pg.wait_for_timeout(5000)
        r=await pg.evaluate("(()=>{const d=window.__d;const l=d.level();return [l.music>0.0005?1:0,d.st().fb,window.__made||0]})()")
        res.append(r)
        await pg.mouse.move(300,200);await pg.mouse.move(340,220);await pg.wait_for_timeout(300);await pg.hover('#stop',force=True);await pg.click('#stop',force=True);await pg.wait_for_timeout(700);await pg.click('#again');await pg.wait_for_timeout(500)
    bad=[i+1 for i,r in enumerate(res) if r[0]<1]
    print(FILM,ENG,'plays',N,'| plays where NO music player started:',bad,'| audio elements created in total:',res[-1][2]);print(' per play [started,refused,total made]:',res);print(' warnings:',list(dict.fromkeys(cons))[:4],'errors:',errs[:3])
    await b.close()
asyncio.run(main())
