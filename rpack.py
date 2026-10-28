#!/usr/bin/env python3
"""
rpack.py - extract / repack Eiyu Senki Gold "RepiPack" archives (tested on AUGGame/Define/Define.dat)

  python rpack.py extract  Define.dat  outdir          -> outdir/*.txt  (UTF-8, CRLF preserved)
  python rpack.py repack   Define.dat  outdir  new.dat -> new.dat (edited files stored uncompressed; others copied byte-for-byte)
  add  --hints file.txt [file2.txt ...]  (last) to give file names found inside other text files, e.g. team.txt for BattleSet.dat.
  Names are hashed/keyed as lowercase Shift-JIS (cp932) bytes.

Format (reverse-engineered from the exe):
  "RepiPack", u32 ver=5, u32 namelen, name, u32 count, count*32-byte table entries, data
  table entry (decrypted with running-key dword cipher, key 0xfb4a25f1):
      16 bytes MD5(lowercase filename) | u32 offset | u32 stored size | u32 real size | u32 0
  data: first min(size,1024) bytes XOR keystream; if stored size != real size the rest is LZSS (4096 ring, start 0xfee).
  keystream: s = reversed lowercase filename; 64 x 16-byte blocks of a *chained* MD5 (state and bit count carry over),
             block 0 = MD5(s), block k = MD5(s[k mod len(s):]).
"""
import struct,sys,os,hashlib,math
M=0xffffffff
NAMES="""ability.txt
attribute.txt
attributetable.txt
battleai.txt
battleback.txt
battlefield.txt
battlekind.txt
battlepanel.txt
battleset.txt
battlestate.txt
bgm.txt
bgm2_101.txt
bgm2_103_eu.txt
bgm2_103_prt.txt
bgm2_103_uk.txt
bgm2_103_usa.txt
bgm2_104.txt
bgm2_105_africa.txt
bgm2_105_america.txt
bgm2_105_asia.txt
bgm2_105_australia.txt
bgm2_105_carib.txt
bgm2_105_europe.txt
bgm2_105_gaia.txt
bgm2_105_kelt.txt
bgm2_105_middleeast.txt
bgm2_105_oceania.txt
bgm2_105_russia.txt
bgm2_105_seabed.txt
bgm2_105_southamerica.txt
bgm2_106.txt
bgm2_107.txt
bgm2_108.txt
bgm2_109.txt
bgm2_110.txt
bgm2_121.txt
bgm2_122.txt
bgm2_123.txt
bgm2_124.txt
city.txt
country.txt
episode.txt
event.txt
item.txt
itemmix.txt
medal.txt
mission.txt
missionkind.txt
route.txt
skill.txt
spot.txt
spotarea.txt
spotback.txt
spotkind.txt
succession.txt
team.txt
tech.txt
techkind.txt
trophy.txt
unit.txt
unitmodel.txt
voice.txt
voicesub.txt""".split()
def rol(x,n): return ((x<<n)|(x>>(32-n)))&M
def dec(buf,key):
    out=bytearray(buf)
    for i in range(len(buf)//4):
        c=struct.unpack_from('<I',buf,i*4)[0]; p=c^key
        struct.pack_into('<I',out,i*4,p)
        key=(key+(rol(p,16)^0x57cc4ec0))&M
    return bytes(out)
def enc(buf,key):
    out=bytearray(buf)
    for i in range(len(buf)//4):
        p=struct.unpack_from('<I',buf,i*4)[0]
        struct.pack_into('<I',out,i*4,p^key)
        key=(key+(rol(p,16)^0x57cc4ec0))&M
    return bytes(out)
K=[int(abs(math.sin(i+1))*2**32)&M for i in range(64)]
S=[7,12,17,22]*4+[5,9,14,20]*4+[4,11,16,23]*4+[6,10,15,21]*4
def rol(x,n): return ((x<<n)|(x>>(32-n)))&M
def transform(st,block):
    X=struct.unpack('<16I',block); a,b,c,d=st
    for i in range(64):
        if i<16: f=(b&c)|(~b&d); g=i
        elif i<32: f=(d&b)|(~d&c); g=(5*i+1)%16
        elif i<48: f=b^c^d; g=(3*i+5)%16
        else: f=c^(b|(~d&M)); g=(7*i)%16
        t=(a+f+K[i]+X[g])&M
        a,d,c=d,c,b
        b=(b+rol(t,S[i]))&M
    return [(st[0]+a)&M,(st[1]+b)&M,(st[2]+c)&M,(st[3]+d)&M]
def keystream(s):
    s=s.encode() if isinstance(s,str) else s
    st=[0x67452301,0xefcdab89,0x98badcfe,0x10325476]; cnt=0; ks=b''
    for k in range(64):
        t=s if k==0 else s[k%len(s):]
        assert len(t)<56
        cnt+=8*len(t)
        buf=bytearray(64); buf[:len(t)]=t; buf[len(t)]=0x80
        struct.pack_into('<II',buf,56,cnt&M,cnt>>32)
        st=transform(st,bytes(buf)); ks+=struct.pack('<4I',*st)
    return ks
def lzss(src,usz):
    ring=bytearray(4096); r=0xfee; out=bytearray(); i=0; flags=0
    while len(out)<usz:
        flags>>=1
        if not flags&0x100:
            flags=src[i]|0xff00; i+=1
        if flags&1:
            c=src[i]; i+=1; out.append(c); ring[r]=c; r=(r+1)&0xfff
        else:
            b1=src[i]; b2=src[i+1]; i+=2
            pos=b1|((b2&0xf0)<<4); ln=(b2&0xf)+2
            for k in range(ln+1):
                c=ring[(pos+k)&0xfff]; out.append(c); ring[r]=c; r=(r+1)&0xfff
                if len(out)>=usz: break
    return bytes(out)

def load(path):
    f=open(path,'rb').read()
    assert f[:8]==b'RepiPack'
    ver,nl=struct.unpack_from('<II',f,8)
    o=16+nl; cnt=struct.unpack_from('<I',f,o)[0]; o+=4
    ents=[]
    for i in range(cnt):
        d=dec(f[o+i*32:o+i*32+32],0xfb4a25f1)
        ents.append((d[:16],)+struct.unpack_from('<III',d,16))
    return f,o,ents
def plain(f,e,name):
    h,off,csz,usz=e
    raw=bytearray(f[off:off+csz]); ks=keystream(name.encode('cp932')[::-1])
    for j in range(min(csz,1024)): raw[j]^=ks[j]
    raw=bytes(raw)
    return raw if csz==usz else lzss(raw,usz)
HINTS=[]
def hint_names(paths):
    import re
    out=set()
    for p in paths:
        raw=open(p,'rb').read()
        try: t=raw.decode('utf-8')
        except UnicodeDecodeError: t=raw.decode('cp932','ignore')
        for q in re.findall(r'"([^"\r\n]+\.txt)"',t):
            out.add(q.replace('\\','/').split('/')[-1].lower())
    return out
def resolve(ents,pack_f=None):
    m={e[0]:e for e in ents}; res={}
    def try_(n):
        h=hashlib.md5(n.encode('cp932','ignore')).digest()
        if h in m and h not in res: res[h]=n; return True
        return False
    for n in list(NAMES)+sorted(HINTS): try_(n)
    if pack_f is not None:                       # follow #include / quoted .txt references inside decoded files
        import re; seen=set()
        while True:
            new=False
            for h,n in list(res.items()):
                if n in seen: continue
                seen.add(n); d=plain(pack_f,m[h],n)
                for q in re.findall(rb'"([^"\r\n]+\.txt)"',d):
                    if try_(q.decode('cp932','ignore').replace('\\','/').split('/')[-1].lower()): new=True
            if not new: break
    return res
def cmd_extract(pack,outdir):
    f,o,ents=load(pack); res=resolve(ents,f); os.makedirs(outdir,exist_ok=True); bad=0
    for e in ents:
        n=res.get(e[0])
        if not n: continue
        d=plain(f,e,n)
        try:
            t=d.decode('cp932')
            assert t.encode('cp932')==d
            open(os.path.join(outdir,n),'w',encoding='utf-8',newline='').write(t)
        except Exception:
            bad+=1; open(os.path.join(outdir,n+'.cp932raw'),'wb').write(d)
    print('extracted',len(res),'files;',len(ents)-len(res),'other entries (kept as-is on repack);',bad,'non-roundtrippable')
def cmd_repack(pack,outdir,newpack):
    f,o,ents=load(pack); res=resolve(ents,f)
    hdr=f[:o]; blobs=[]
    for e in ents:
        n=res.get(e[0]); h,off,csz,usz=e
        blob=f[off:off+csz]; real=usz
        if n:
            p=os.path.join(outdir,n); pr=p+'.cp932raw'
            if os.path.exists(p):
                try: new=open(p,'r',encoding='utf-8',newline='').read().encode('cp932')
                except UnicodeEncodeError as ex: sys.exit('ERROR %s: %s (character not representable in Shift-JIS/cp932)'%(n,ex))
            elif os.path.exists(pr): new=open(pr,'rb').read()
            else: new=None
            if new is not None and new!=plain(f,e,n):
                ks=keystream(n.encode('cp932')[::-1]); b=bytearray(new)
                for j in range(min(len(b),1024)): b[j]^=ks[j]
                blob=bytes(b); real=len(new); print('modified',n,usz,'->',real)
        blobs.append((h,blob,real))
    off=len(hdr)+32*len(ents); table=b''; data=b''
    for h,blob,real in blobs:
        table+=enc(h+struct.pack('<IIII',off,len(blob),real,0),0xfb4a25f1)
        data+=blob; off+=len(blob)
    out=hdr+table+data
    open(newpack,'wb').write(out)
    print('wrote',newpack,len(out),'bytes')
if __name__=='__main__':
    a=sys.argv[1:]
    if '--hints' in a:
        i=a.index('--hints'); HINTS.extend(hint_names(a[i+1:])); a=a[:i]
    if len(a)>=3 and a[0]=='extract': cmd_extract(a[1],a[2])
    elif len(a)>=4 and a[0]=='repack': cmd_repack(a[1],a[2],a[3])
    else: print(__doc__)
