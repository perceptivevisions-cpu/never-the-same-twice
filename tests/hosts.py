# writes local host pages imitating the two sites' embeds
import sys
base=sys.argv[1]
open(base+'/t_art.html','w').write('<!doctype html><meta name="viewport" content="width=device-width, initial-scale=1"><body style="margin:0;padding:40px 60px;background:#fff"><iframe id="f" src="http://127.0.0.1:8766/FILM" style="width:100%;aspect-ratio:16/9;border:0;background:#000;display:block" allow="autoplay; fullscreen" allowfullscreen title="Nobody Remembers"></iframe></body>')
open(base+'/t_com.html','w').write('<!doctype html><meta name="viewport" content="width=device-width, initial-scale=1"><body style="margin:0;background:#fff"><div style="margin-left:240px;padding:100px 126px;max-width:912px"><iframe id="f" class="ql-video" frameborder="0" allowfullscreen="true" allow="autoplay; fullscreen" src="http://127.0.0.1:8766/FILM" height="563" width="1000" style="width:100%;height:auto;aspect-ratio:16/9;"></iframe></div></body>')
open(base+'/t_nofs.html','w').write('<!doctype html><body style="margin:0;padding:40px"><iframe id="f" src="http://127.0.0.1:8766/FILM" width="900" height="506" allow="autoplay"></iframe></body>')
