import math
from adversarial import ED, chi_at_est, D_of, gl, region, diam
import adversarial as A

print("="*74)
print("精化命题 B：R=1200 已知时，E[D] 最优点与 χ 的关系")
print("  (a) 含失效分支（|S2-G|>r_G 退化为扇形）  (b) 条件于成功（纯几何）")
def ED_cond(psi,d,R,**kw):
    """条件于第二次测量成功：r_G 固定 1500，且只在成功样本上平均"""
    xd,wd=gl(9); tot=wt=fw=0.0
    for a in range(9):
        d1=1.0*xd[a]; w1=wd[a]*0.5
        for b in range(9):
            d2=1.0*xd[b]; w2=wd[b]*0.5
            v,f=D_of(psi,d,R,d1,d2,1500.0)
            if f: fw+=w1*w2; continue
            tot+=w1*w2*v; wt+=w1*w2
    return (tot/wt if wt>0 else float('nan')), fw

best=None; bestc=None
print(f"{'psi':>6}{'d':>7}{'E[D]全':>10}{'失效%':>8}{'E[D]|成功':>11}{'chi(R=1200)':>13}")
for psi in (10.,12.5,15.,17.5,20.,22.5,25.,30.,35.,40.,45.,50.,60.,90.):
    for d in (1000.,1100.,1200.,1300.,1400.,1500.):
        e,f=ED(psi,d,("fixed",1200.0),nR=1,nd=9,nrg=5)
        ec,_=ED_cond(psi,d,1200.0)
        ch=chi_at_est(psi,d,1200.0)
        if best is None or e<best[0]: best=(e,psi,d,f,ch)
        if bestc is None or (ec==ec and ec<bestc[0]): bestc=(ec,psi,d,ch)
    e,f=ED(psi,1200.0,("fixed",1200.0),nR=1,nd=9,nrg=5); ec,_=ED_cond(psi,1200.0,1200.0)
    print(f"{psi:>6.1f}{1200.0:>7.0f}{e:>10.2f}{f*100:>8.2f}{ec:>11.2f}{chi_at_est(psi,1200.,1200.):>13.2f}")
print()
print(f"  全口径最优:  E[D]={best[0]:.3f} @ psi={best[1]}, d={best[2]}  失效={best[3]*100:.2f}%  chi={best[4]:.2f}deg")
print(f"  条件成功最优: E[D]={bestc[0]:.3f} @ psi={bestc[1]}, d={bestc[2]}  chi={bestc[3]:.2f}deg")
print()
print("  对照 harness 判据 phi=90 的垂线族（偏移 t，|S1G|=1200）：")
for t in (300.,600.,900.,1200.,1500.):
    d=math.hypot(1200.,t); psi=math.degrees(math.atan2(t,1200.))
    e,f=ED(psi,d,("fixed",1200.0),nR=1,nd=9,nrg=5); ec,_=ED_cond(psi,d,1200.0)
    print(f"    偏移={t:6.0f}  psi={psi:5.2f}  d={d:7.1f}  chi=90.00  E[D]|成功={ec:7.2f}  E[D]全={e:8.2f}")
