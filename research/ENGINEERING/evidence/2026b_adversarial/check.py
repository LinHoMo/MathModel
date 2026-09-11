import math, itertools, random
EPS=1.0
def _dir(a):
    r=math.radians(a); return math.cos(r), math.sin(r)
def wedge_hp(sx,sy,th,eps):
    out=[]
    for ang in (th-eps, th+eps):
        dx,dy=_dir(ang); a,b=-dy,dx; c=a*sx+b*sy; out.append((a,b,c))
    return [(out[0][0],out[0][1],out[0][2],"ge"),(out[1][0],out[1][1],out[1][2],"le")]
def clip(poly,a,b,c,sense):
    if not poly: return []
    def ins(p):
        v=a*p[0]+b*p[1]
        return v>=c-1e-9 if sense=="ge" else v<=c+1e-9
    def inter(p,q):
        fp=a*p[0]+b*p[1]-c; fq=a*q[0]+b*q[1]-c
        t=fp/(fp-fq) if (fp-fq)!=0 else 0.0
        return (p[0]+t*(q[0]-p[0]), p[1]+t*(q[1]-p[1]))
    out=[];n=len(poly)
    for i in range(n):
        p,q=poly[i],poly[(i+1)%n]; pi,qi=ins(p),ins(q)
        if pi: out.append(p)
        if pi!=qi: out.append(inter(p,q))
    return out
def region(pts,bears,eps=EPS,bbox=8000.0):
    poly=[(-bbox,-bbox),(bbox,-bbox),(bbox,bbox),(-bbox,bbox)]
    for (sx,sy),th in zip(pts,bears):
        for (a,b,c,s) in wedge_hp(sx,sy,th,eps):
            poly=clip(poly,a,b,c,s)
            if len(poly)<3: return poly
    return poly
def hull(pts):
    P=sorted(set((round(x,9),round(y,9)) for x,y in pts))
    if len(P)<=2: return P
    def cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[]
    for p in P:
        while len(lo)>=2 and cr(lo[-2],lo[-1],p)<=0: lo.pop()
        lo.append(p)
    up=[]
    for p in reversed(P):
        while len(up)>=2 and cr(up[-2],up[-1],p)<=0: up.pop()
        up.append(p)
    return lo[:-1]+up[:-1]
def diam(V):
    H=hull(V); best=0; pair=None
    for i in range(len(H)):
        for j in range(i+1,len(H)):
            d=math.dist(H[i],H[j])
            if d>best: best,pair=d,(H[i],H[j])
    return best,pair,H
def circ3(a,b,c):
    d=2*(a[0]*(b[1]-c[1])+b[0]*(c[1]-a[1])+c[0]*(a[1]-b[1]))
    if abs(d)<1e-12: return None
    ux=((a[0]**2+a[1]**2)*(b[1]-c[1])+(b[0]**2+b[1]**2)*(c[1]-a[1])+(c[0]**2+c[1]**2)*(a[1]-b[1]))/d
    uy=((a[0]**2+a[1]**2)*(c[0]-b[0])+(b[0]**2+b[1]**2)*(a[0]-c[0])+(c[0]**2+c[1]**2)*(b[0]-a[0]))/d
    return (ux,uy)
def mec(V):
    H=hull(V); best=None
    for i in range(len(H)):
        for j in range(i+1,len(H)):
            c=((H[i][0]+H[j][0])/2,(H[i][1]+H[j][1])/2); r=math.dist(H[i],H[j])/2
            if all(math.dist(p,c)<=r+1e-7 for p in H):
                if best is None or r<best[1]: best=(c,r)
    for i in range(len(H)):
        for j in range(i+1,len(H)):
            for k in range(j+1,len(H)):
                c=circ3(H[i],H[j],H[k])
                if c is None: continue
                r=math.dist(c,H[i])
                if all(math.dist(p,c)<=r+1e-7 for p in H):
                    if best is None or r<best[1]: best=(c,r)
    return best
def bear(x1,y1,x2,y2): return math.degrees(math.atan2(y2-y1,x2-x1))%360.0
def bdiff(b1,b2): return abs(((b1-b2+180.0)%360.0)-180.0)

print("="*70)
print("A) Q1 演示算例的物理可行性（源接收半径 <=1500 m）")
cases={
 "A 正交交会":([(0.,0.),(3000.,0.)],(1500.,1500.)),
 "B 钝角交会":([(0.,0.),(3000.,0.)],(1200.,500.)),
 "C 三站交会":([(0.,0.),(3000.,0.),(1500.,2600.)],(1500.,1200.)),
}
for n,(S,G) in cases.items():
    ds=[math.dist(s,G) for s in S]
    print(f"  {n}: |S_i - G| = {[round(d,1) for d in ds]}  max={max(ds):.1f}  "
          f"{'OK' if max(ds)<=1500 else '*** 超过 1500 m 接收上限，物理不可测 ***'}")

print()
print("="*70)
print("B) 合成反例 vs 真实两站楔形交会的 rho = R_MEC / D")
tri=[(0.,0.),(10.,0.),(5.,6.)]
D,_,_=diam(tri); _,r=mec(tri)
print(f"  harness 合成锐角三角形: D={D:.4f}  R_mec={r:.4f}  rho={r/D:.6f}")
print("  该三角形是否可由真实示向度楔形交会得到？ -> 两站楔形交会恒为平行四边形（4 顶点）")

# 真实两站族：扫描 chi, t1,t2
print("  真实两站楔形交会扫描 (chi 步长 0.25°, t1,t2 in {1,3,10,40,200,1000}):")
worst=0; worst_at=None
ts=[1,3,10,40,200,1000]
chi=60.0
rows=[]
while chi<=120.0001:
    mx=0
    for t1 in ts:
        for t2 in ts:
            # 交点在原点，两站在各自直线反向延长线上
            S1=(-t1,0.0)
            a=math.radians(chi)
            S2=(-t2*math.cos(a), -t2*math.sin(a)) if False else (-t2*math.cos(a), t2*math.sin(a))
            # 从 S1 指向原点方位
            b1=bear(S1[0],S1[1],0.,0.)
            b2=bear(S2[0],S2[1],0.,0.)
            if abs(bdiff(b1,b2)-chi)>1e-6 and abs(bdiff(b1,b2)-(180-chi))>1e-6:
                pass
            reg=region([S1,S2],[b1,b2])
            if len(reg)<3: continue
            D2,_,H=diam(reg)
            if D2<=0: continue
            _,r2=mec(H)
            rho=r2/D2
            if rho>mx: mx=rho
    rows.append((chi,mx))
    if mx>worst: worst,worst_at=mx,chi
    chi+=0.25
fail=[(c,v) for c,v in rows if v>0.5+1e-9]
print(f"    在窗 (90,92) 外 rho 是否恒 = 0.5 : {all(abs(v-0.5)<1e-9 for c,v in rows if not (90<c<92))}")
print(f"    全族 rho 最大值 = {worst:.7f}  出现在 chi = {worst_at}°")
print(f"    合成反例 rho = {r/D:.6f}  是真实两站上确界的 {(r/D-0.5)/(worst-0.5):.1f} 倍超出量")

print()
print("="*70)
print("C) 用 harness 的同一套几何内核复算答案稿的 Q1 算例（检验算法是否一致）")
S=[(0.,0.),(1000.,0.),(500.,900.)]
TH=[50.1987,119.1449,-63.1349]
reg=region(S,TH)
D,pair,H=diam(reg)
def area(V):
    s=0
    for i in range(len(V)):
        x1,y1=V[i]; x2,y2=V[(i+1)%len(V)]
        s+=x1*y2-x2*y1
    return abs(s)/2
print(f"  顶点数={len(reg)}  D={D:.4f} m  面积={area(reg):.4f} m^2")
print(f"  答案稿: D=39.1317 m  面积=257.5738 m^2  -> 算法{'一致' if abs(D-39.1317)<0.01 else '不一致'}")
print(f"  端点: {pair[0]} -- {pair[1]}")
