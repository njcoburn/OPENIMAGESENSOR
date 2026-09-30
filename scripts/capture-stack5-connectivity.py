"""Canonicalize the four private nodes in each extracted five-NMOS capture path."""
def identify(records, find, canonical, columns=None):
    paths=[]
    mos=[r for r in records if len(r)>5 and r[0].startswith('X') and r[5]=='nfet_03v3']
    for c in ([None] if columns is None else range(columns)):
        suffix='' if c is None else str(c)
        node=find('COL'+suffix); devices=[];private=[]
        for i in range(5):
            matches=[r for r in mos if find(r[1])==node and find(r[2])==find('SC') and find(r[4])==find('GND')]
            device,=matches
            assert device[0] not in devices
            assert 'w=1u' in device and 'l=0.5u' in device
            devices.append(device[0]);node=find(device[3])
            if i<4:
                name=f'HN{i+1}'+suffix
                assert node not in canonical, ('Private capture node shorted to another net',name)
                canonical[node]=name;private.append(dict(name=name,extracted_node=device[3]))
        assert node==find('STORE'+suffix), ('Capture path does not end at STORE',suffix)
        paths.append(dict(column=c,instances=devices,private_nodes=private))
    return paths
