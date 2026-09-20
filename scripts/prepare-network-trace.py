"""Instrument an ignored Magic checkout; no installed tools are modified."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];src=ROOT/'build/magic-8.3.664-source'
p=src/'resis/ResMerge.c';s=p.read_text();needle='resptr->rn_status |= RES_TRUE;';assert s.count(needle)==1
s=s.replace(needle,needle+'\n    if (getenv("OIS_NO_REDUCE") != NULL) return;')
s='#include <stdlib.h>\n'+s;p.write_text(s)
p=src/'resis/ResRex.c';s=p.read_text();needle='\t    ResDoSimplify(resisdata);';assert s.count(needle)==1
trace='''
            { resResistor *q;
              TxPrintf("OIS_BEGIN %s\\n", node->name);
              for (q=ResResList; q; q=q->rr_nextResistor)
                TxPrintf("OIS_EDGE %p %p %.12g %s %s\\n",
                  (void *)q->rr_connection1, (void *)q->rr_connection2,
                  (double)q->rr_value / 1000.0,
                  q->rr_connection1->rn_name ? q->rr_connection1->rn_name : "-",
                  q->rr_connection2->rn_name ? q->rr_connection2->rn_name : "-");
              TxPrintf("OIS_END\\n");
            }
'''
s=s.replace(needle,trace+needle);p.write_text(s)
