# Pen-style ESP32-S3 case v1.0 - flat-oval barrel, two printed parts (top + bottom lid)
# TOP half   : shell, board rails (+gussets, lead-ins), USB slots, enclosed switch tunnel
# BOTTOM lid : floor, battery holster (side guides + corner stops), switch clamp posts, lap-joint lip
# Layout along X: [HW-373 | battery | XIAO ESP32-S3]. Units mm. Split plane = cavity floor (z = -IHH).
import os, numpy as np, trimesh, manifold3d as m3

# ---------------- parameters ----------------
WALL, END, FLOOR = 1.5, 1.2, 1.2
IWH, IHH = 9.1, 4.5                       # inner half width / half height (18.2 x 9.0 cavity)
OWH, OHT, OHB = IWH+WALL, IHH+WALL, IHH+FLOOR
RT, RB, RI = 3.0, 1.2, 0.2
XIAO = dict(L=21.0, W=17.8, T=1.2, G=1.65)   # T = assumed PCB thickness, G = rail gap (T+0.45)
TP   = dict(L=26.0, W=17.0, T=1.2, G=1.65)   # HW-373
BAT  = dict(L=38.0, W=14.6)
LEDGE_T, OVER, SIDE = 1.0, 0.6, 0.15
SW_L, SW_W, SW_H = 8.6, 3.6, 3.6
USB_W, XIAO_CONN_CTR, TP_CONN_CTR = 9.6, 1.63, 1.6
LIP, LIP_H, REB_CUT, REB_H = 0.6, 1.2, 0.8, 1.5   # lap joint: lip 0.6, rebate removes 0.8 (0.2 clearance)

# ---------------- layout ----------------
tp0 = END+0.05;  tp1 = tp0+TP['L']
bat0 = tp1+2.2;  bat1 = bat0+BAT['L']
esp0 = bat1+1.2; esp1 = esp0+XIAO['L']
L = esp1+0.05+END
ZS = -IHH

# ---------------- helpers ----------------
def box(x0,x1,y0,y1,z0,z1):
    b=trimesh.creation.box(extents=(x1-x0,y1-y0,z1-z0)); b.apply_translation(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)); return b
def cylz(r,x,y,z0,z1):
    c=trimesh.creation.cylinder(radius=r,height=z1-z0,sections=48); c.apply_translation((x,y,(z0+z1)/2)); return c
U=lambda *m: trimesh.boolean.union(list(m),engine='manifold')
D=lambda a,*m: trimesh.boolean.difference([a]+list(m),engine='manifold')
I=lambda *m: trimesh.boolean.intersection(list(m),engine='manifold')
def rr(hw,ht,hb,rt,rb,n=24):
    pts=[]
    def arc(cx,cz,r,a0,a1):
        for t in np.linspace(a0,a1,n): pts.append((cx+r*np.cos(t),cz+r*np.sin(t)))
    arc(hw-rb,-hb+rb,rb,-np.pi/2,0); arc(hw-rt,ht-rt,rt,0,np.pi/2)
    arc(-hw+rt,ht-rt,rt,np.pi/2,np.pi); arc(-hw+rb,-hb+rb,rb,np.pi,1.5*np.pi)
    return np.array(pts)
def prism(poly,x0,x1):                      # extrude a (y,z) polygon along X
    poly=np.asarray(poly,float)
    if 0.5*np.sum(poly[:,0]*np.roll(poly[:,1],-1)-np.roll(poly[:,0],-1)*poly[:,1])<0: poly=poly[::-1]
    mm=m3.Manifold.extrude(m3.CrossSection([poly]),x1-x0).to_mesh()
    t=trimesh.Trimesh(np.array(mm.vert_properties)[:,:3],np.array(mm.tri_verts))
    T=np.eye(4); T[:3,:3]=[[0,0,1],[1,0,0],[0,1,0]]
    t.apply_transform(T); t.apply_translation((x0,0,0)); return t
def inset(d): return rr(OWH-d,OHT-d,OHB-d,RT-d,RB-d)
def ring(d0,d1,x0,x1): return D(prism(inset(d0),x0,x1),prism(inset(d1),x0-1,x1+1))

# ---------------- outer shell (hull of 8 spheres) ----------------
pts=[]
for sy in (-1,1):
    for cz,r in ((OHT-RT,RT),(-OHB+RB,RB)):
        for cx in (r,L-r):
            pts.append(trimesh.creation.icosphere(subdivisions=3,radius=r).vertices+np.array([cx,sy*(OWH-r),cz]))
outer=trimesh.Trimesh(vertices=np.vstack(pts)).convex_hull
clip=U(cylz(1.5,12,0,OHT-0.5,OHT+0.8),cylz(1.5,40,0,OHT-0.5,OHT+0.8),box(12,40,-1.5,1.5,OHT-0.5,OHT+0.8))
solid=outer

# ---------------- cuts ----------------
cavity=prism(rr(IWH,IHH,IHH,RI,RI),END,L-END)
def usb(zc,h,tail):
    if tail: a=(-1,END+0.3,-1,0.6)
    else:    a=(L-END-0.3,L+1,L-0.6,L+1)
    return [box(a[0],a[1],-USB_W/2,USB_W/2,zc-h/2,zc+h/2),
            box(a[2],a[3],-USB_W/2-0.5,USB_W/2+0.5,zc-h/2-0.5,zc+h/2+0.5)]
zl_x=IHH-XIAO['G']; zl_t=IHH-TP['G']
mid = lambda b: IHH-(b['G']+b['T'])/2            # PCB underside, mid-way between rail and roof
z_tp  = mid(TP)-TP_CONN_CTR
z_esp = mid(XIAO)-XIAO_CONN_CTR
cuts=usb(z_tp,4.1,True)+usb(z_esp,4.1,False)
SWZ=-1.9                                        # switch raised so the slot clears the lap joint
swx=tp1-6.0
cuts+=[box(swx-3.0,swx+3.0,-OWH-1,-IWH+0.3,SWZ-1.2,SWZ+1.2),
       box(swx-5.5,swx+5.5,-OWH-1,-OWH+0.7,SWZ-2.0,SWZ+2.0)]
for xr in (L-17,L-14.5): cuts.append(ring(0,0.4,xr,xr+0.8))
body=D(solid,cavity,*cuts)
cavity_deep=prism(rr(IWH,IHH,IHH+1.0,RI,RI),END,L-END)          # runs past the split plane so the top half is cleanly open
body_top=D(solid,cavity_deep,*cuts)

# ---------------- top-half internal features ----------------
feat=[]
def chamfer_cut(x,y0,y1,z,c=0.9):
    k=trimesh.creation.box(extents=(c*1.414,y1-y0,c*1.414))
    k.apply_transform(trimesh.transformations.rotation_matrix(np.pi/4,[0,1,0]))
    k.apply_translation((x,(y0+y1)/2,z)); return k
def rails(xa,xb,b,inner_is_xb,guides):
    zl=IHH-b['G']
    for s in (1,-1):
        yi=b['W']/2-OVER; yw=IWH+0.3
        y0,y1=sorted((s*yi,s*yw))
        led=box(xa,xb,y0,y1,zl-LEDGE_T,zl)
        led=D(led,chamfer_cut(xb if inner_is_xb else xa,y0,y1,zl))        # lead-in at the entrance
        feat.append(led)
        dpt=yw-yi                                                          # 45-degree gusset under the rail
        feat.append(prism([(s*yw,zl-LEDGE_T),(s*yi,zl-LEDGE_T),(s*yw,zl-LEDGE_T-dpt)],xa,xb))
        if guides:
            gy=b['W']/2+SIDE; y0,y1=sorted((s*gy,s*yw)); feat.append(box(xa,xb,y0,y1,zl-LEDGE_T,IHH+0.3))
rails(END,tp1,TP,True,False); rails(esp0,L-END,XIAO,False,False)   # same rail style on both boards (no side guides)
# enclosed switch tunnel (open toward the cavity centre): pedestal + strap + end posts
pl=SW_L+0.2; yface=-IWH+SW_W; zb=SWZ-SW_H/2; zt_=SWZ+SW_H/2
feat+=[box(swx-pl/2,swx+pl/2,-IWH-0.3,yface,ZS,zb),
       box(swx-pl/2-0.8,swx+pl/2+0.8,-IWH-0.3,yface,zt_+0.1,zt_+0.8),
       box(swx-pl/2-0.8,swx-pl/2,-IWH-0.3,yface,ZS,zt_+0.8),
       box(swx+pl/2,swx+pl/2+0.8,-IWH-0.3,yface,ZS,zt_+0.8)]
body=U(body,*feat)
body_top=U(body_top,*feat)

# ---------------- split + lap joint ----------------
big=40
top=I(body_top,box(-1,L+1,-big,big,ZS,big)); lid=I(body,box(-1,L+1,-big,big,-big,ZS))
lip=I(ring(0,LIP,3.2,L-3.2),box(-1,L+1,-big,big,ZS-0.01,ZS+LIP_H))
reb=I(ring(-0.5,REB_CUT,3.0,L-3.0),box(-1,L+1,-big,big,ZS-0.01,ZS+REB_H))
top=D(top,reb)
# ---------------- lid features ----------------
lf=[]
for sy in (1,-1):
    y0,y1=sorted((sy*BAT['W']/2,sy*(IWH-0.25))); lf.append(box(bat0,bat1,y0,y1,ZS-0.3,0))             # battery holster: side guides
    y0,y1=sorted((sy*5.2,sy*(IWH-0.25)))
    lf+=[box(bat0-1.0,bat0,y0,y1,ZS-0.3,-0.5),box(bat1,bat1+1.0,y0,y1,ZS-0.3,-0.5)]                  # battery holster: corner stops
for dx in (-1,1):                                                                                      # switch clamp posts
    xa,xb=sorted((swx+dx*3.0,swx+dx*4.3)); lf.append(box(xa,xb,yface+0.05,yface+1.0,ZS-0.3,zt_-0.3))
lid=U(lid,lip,*lf)

out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","stl")+os.sep; os.makedirs(out,exist_ok=True)
for n,m in (("pen_top",top),("pen_bottom",lid)):
    m2=m.copy(); m2.apply_translation((0,0,-m2.bounds[0][2])); m2.export(out+n+".stl")
    print(n,"watertight:",m2.is_watertight,"size:",np.round(m2.extents,1))
print("overall: %.1f x %.1f x %.1f mm"%(L,2*OWH,OHT+OHB))

# ---------------- fit checks (volumes in mm^3, expect 0) ----------------
def vol(m,ref):
    r=I(ref,m); return round(float(r.volume),3) if len(r.faces) else 0.0
for name,x0,b in (("HW-373",tp0,TP),("XIAO",esp0,XIAO)):
    for pos,zlow in (("on rails",IHH-b['G']),("at roof",IHH-b['T'])):
        for dx in ((0,) if name=="HW-373" else (0,-5,-15)):
            pcb=box(x0+dx,x0+dx+b['L'],-b['W']/2,b['W']/2,zlow,zlow+b['T'])
            comp=box(x0+dx,x0+dx+b['L'],-(b['W']/2-OVER-0.1),(b['W']/2-OVER-0.1),zlow-(1.8 if name=='HW-373' else 2.4),zlow)   # component height under the PCB
            print(name,pos,"shift",dx,"PCB vs top",vol(pcb,top),"vs lid",vol(pcb,lid),"| parts vs top",vol(comp,top),"vs lid",vol(comp,lid))
bat=box(bat0,bat1,-7.0,7.0,-IHH,IHH-1.0)
print("battery vs top",vol(bat,top),"vs lid",vol(bat,lid))
sw=box(swx-SW_L/2,swx+SW_L/2,-IWH,yface,zb,zt_)
print("switch vs top",vol(sw,top),"vs lid",vol(sw,lid))
print("top vs lid",vol(top,lid))
