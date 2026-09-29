"""Refresh current sections while preserving the notebook's historical evidence.

The full build-overview.py also loads these sections on a complete rebuild.
This update avoids rerendering unrelated historical waveforms and images.
"""
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
SECTIONS=[('64x64-first-silicon-section.html','first-silicon-64','Current 64×64 plan'),
          ('wafer-space-run3-section.html','wafer-space-run3','Run 3, cost and die fit'),
          ('compact-bank-solver-section.html','compact-bank-solver','Bank solver progress'),
          ('compact-bank-16-section.html','compact-bank-16','16-column accuracy'),
          ('compact-bank-16-screen-section.html','compact-bank-16-screen','16-column thermal and patterns'),
          ('compact-bank-16-extension-section.html','compact-bank-16-extension','16-column refinement and placement'),
          ('compact-bank-64-ground8-section.html','compact-bank-64-ground8','64-column ground and capture'),
          ('compact-bank-64-read-probes-section.html','compact-bank-64-read-probes','64-column matched readout'),
          ('compact-bank-64-full-section.html','compact-bank-64-full','64-column complete scans'),
          ('compact-bank-64-cross-section.html','compact-bank-64-cross','64-column temperature/pattern matrix')]


class Audit(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[];self.sections=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag=='a' and attrs.get('href','').startswith('#'):self.links.append(attrs['href'][1:])
        if tag=='section':self.sections+=1
    def handle_endtag(self,tag):
        if tag=='section':self.sections-=1;assert self.sections>=0


def main():
    path=ROOT/'docs/overview.html';text=path.read_text()
    for filename,anchor,label in SECTIONS:
        if filename=='compact-bank-64-cross-section.html' and not (ROOT/'docs'/filename).exists():continue
        section=(ROOT/'docs'/filename).read_text()
        assert section.count('<section ')==section.count('</section>')==1
        pattern=rf'<section id="{re.escape(anchor)}">.*?</section>'
        if re.search(pattern,text,re.S):text,count=re.subn(pattern,lambda _:section,text,flags=re.S);assert count==1
        else:text=text.replace('<main>','<main>'+section,1)
        if f'href="#{anchor}"' not in text.split('</nav>',1)[0]:
            text=text.replace('<nav>',f'<nav><a href="#{anchor}">{label}</a>',1)
    audit=Audit();audit.feed(text)
    assert len(audit.ids)==len(set(audit.ids)), 'Duplicate HTML anchors'
    assert not set(audit.links)-set(audit.ids), 'Broken in-page link'
    assert audit.sections==0
    path.write_text(text)
    print(f'Updated {len(SECTIONS)} current sections; {len(audit.ids)} unique anchors checked.')


if __name__=='__main__':main()
