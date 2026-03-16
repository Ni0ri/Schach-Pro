"""
Schach Pro – Kivy Android App
Android-sicher: keine module-level Kivy-Calls, kein Unicode in kritischen Stellen,
alle UI-Updates über Clock, robustes Threading
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
import threading, time

# ══════════════════════════════════════════════════════════════════════
# FARBEN (einfache Tupel, kein get_color_from_hex → kein Crash)
# ══════════════════════════════════════════════════════════════════════
BG       = (0.10, 0.10, 0.10, 1)
ACCENT   = (0.79, 0.64, 0.15, 1)
ACCENT_T = (0.10, 0.10, 0.10, 1)   # Text auf Accent-Buttons
SQ_L     = (0.94, 0.91, 0.77, 1)
SQ_D     = (0.29, 0.49, 0.35, 1)
HL_L     = (0.96, 0.96, 0.41, 1)
HL_D     = (0.73, 0.79, 0.17, 1)
SEL_C    = (0.67, 0.87, 0.40, 1)
CHK_C    = (0.80, 0.13, 0.13, 1)
DOT_C    = (0.40, 0.85, 0.20, 1)
BTN_DK   = (0.18, 0.16, 0.14, 1)
TXT_LT   = (0.90, 0.85, 0.75, 1)
TXT_DIM  = (0.55, 0.50, 0.40, 1)

# ══════════════════════════════════════════════════════════════════════
# FIGUREN-BUCHSTABEN (Android-sicher, immer sichtbar)
# Weiss: K=Koenig D=Dame T=Turm L=Laeufer S=Springer B=Bauer
# Schwarz: k=Koenig d=Dame t=Turm l=Laeufer s=Springer b=Bauer
# ══════════════════════════════════════════════════════════════════════
PL = {'K':'K','Q':'D','R':'T','B':'L','N':'S','P':'B',
      'k':'k','q':'d','r':'t','b':'l','n':'s','p':'b'}
FILES = 'abcdefgh'

# ══════════════════════════════════════════════════════════════════════
# SCHACH-ENGINE
# ══════════════════════════════════════════════════════════════════════
INIT = [
    ['r','n','b','q','k','b','n','r'],
    ['p','p','p','p','p','p','p','p'],
    [None]*8,[None]*8,[None]*8,[None]*8,
    ['P','P','P','P','P','P','P','P'],
    ['R','N','B','Q','K','B','N','R']
]
PVAL = {'P':100,'N':320,'B':330,'R':500,'Q':950,'K':0,
        'p':100,'n':320,'b':330,'r':500,'q':950,'k':0}
CONTEMPT = 70

def iw(p): return p is not None and p == p.upper()
def ok(r,c): return 0 <= r < 8 and 0 <= c < 8

def gen_pseudo(board, r, c, w, castle, ep):
    p = board[r][c]; pt = p.upper(); mvs = []
    def add(tr,tc):
        if ok(tr,tc) and not(board[tr][tc] and iw(board[tr][tc])==w):
            mvs.append((r,c,tr,tc))
    def slide(dirs):
        for dr,dc in dirs:
            nr,nc = r+dr,c+dc
            while ok(nr,nc):
                q = board[nr][nc]
                if q:
                    if iw(q)!=w: mvs.append((r,c,nr,nc))
                    break
                mvs.append((r,c,nr,nc)); nr+=dr; nc+=dc
    if pt=='P':
        d=-1 if w else 1; st=6 if w else 1
        if ok(r+d,c) and not board[r+d][c]:
            mvs.append((r,c,r+d,c))
            if r==st and not board[r+2*d][c]: mvs.append((r,c,r+2*d,c))
        for dc in [-1,1]:
            nr,nc = r+d,c+dc
            if ok(nr,nc):
                if board[nr][nc] and iw(board[nr][nc])!=w: mvs.append((r,c,nr,nc))
                elif ep==(nr,nc): mvs.append((r,c,nr,nc))
    elif pt=='N':
        for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]: add(r+dr,c+dc)
    elif pt=='B': slide([(-1,-1),(-1,1),(1,-1),(1,1)])
    elif pt=='R': slide([(-1,0),(1,0),(0,-1),(0,1)])
    elif pt=='Q': slide([(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)])
    elif pt=='K':
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                if dr or dc: add(r+dr,c+dc)
        kr=7 if w else 0; rt='R' if w else 'r'
        if r==kr and c==4:
            ks='K' if w else 'k'; qs='Q' if w else 'q'
            if ks in castle and not board[kr][5] and not board[kr][6] and board[kr][7]==rt:
                mvs.append((r,c,kr,6))
            if qs in castle and not board[kr][3] and not board[kr][2] and not board[kr][1] and board[kr][0]==rt:
                mvs.append((r,c,kr,2))
    return mvs

def do_move(board, mv, castle, ep):
    b=[list(row) for row in board]
    r1,c1,r2,c2=mv; p=b[r1][c1]; pt=p.upper()
    cap=b[r2][c2]; nep=None
    b[r2][c2]=p; b[r1][c1]=None
    if pt=='P':
        if r2==0: b[r2][c2]='Q'
        elif r2==7: b[r2][c2]='q'
        elif ep==(r2,c2):
            er=r2+(1 if iw(p) else -1); cap=b[er][c2]; b[er][c2]=None
        if abs(r2-r1)==2: nep=((r1+r2)//2,c2)
    if pt=='K':
        if c1==4 and c2==6: b[r1][5]=b[r1][7]; b[r1][7]=None
        elif c1==4 and c2==2: b[r1][3]=b[r1][0]; b[r1][0]=None
    nc=set(castle)
    if pt=='K': nc -= ({'K','Q'} if iw(p) else {'k','q'})
    for k,pos in [('K',(7,7)),('Q',(7,0)),('k',(0,7)),('q',(0,0))]:
        if (r1,c1)==pos or (r2,c2)==pos: nc.discard(k)
    return b, frozenset(nc), nep, cap

def sq_att(board,r,c,by_w):
    for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nr,nc=r+dr,c+dc
        if ok(nr,nc):
            q=board[nr][nc]
            if q and q.upper()=='N' and iw(q)==by_w: return True
    for dr,dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        nr,nc=r+dr,c+dc; d=0
        while ok(nr,nc):
            q=board[nr][nc]
            if q:
                if iw(q)==by_w:
                    t=q.upper()
                    if t in ('B','Q'): return True
                    if d==0 and t=='K': return True
                    if d==0 and t=='P':
                        if by_w and dr==-1: return True
                        if not by_w and dr==1: return True
                break
            nr+=dr; nc+=dc; d+=1
    for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr,nc=r+dr,c+dc; d=0
        while ok(nr,nc):
            q=board[nr][nc]
            if q:
                if iw(q)==by_w:
                    t=q.upper()
                    if t in ('R','Q'): return True
                    if d==0 and t=='K': return True
                break
            nr+=dr; nc+=dc; d+=1
    return False

def king_pos(board,w):
    k='K' if w else 'k'
    for r in range(8):
        for c in range(8):
            if board[r][c]==k: return r,c
    return None

def in_check(board,w):
    p=king_pos(board,w)
    return bool(p and sq_att(board,p[0],p[1],not w))

def legal_moves(board,w,castle,ep):
    res=[]
    for r in range(8):
        for c in range(8):
            q=board[r][c]
            if not q or iw(q)!=w: continue
            for mv in gen_pseudo(board,r,c,w,castle,ep):
                r1,c1,r2,c2=mv; pt=q.upper()
                if pt=='K' and abs(c2-c1)==2:
                    if in_check(board,w): continue
                    step=1 if c2>c1 else -1
                    if any(sq_att(board,r1,cc,not w) for cc in range(c1,c2+step,step)): continue
                nb,nc2,ne,_=do_move(board,mv,castle,ep)
                if not in_check(nb,w): res.append(mv)
    return res

def evaluate(board,w_persp):
    score=0
    for r in range(8):
        for c in range(8):
            p=board[r][c]
            if not p: continue
            score+=(1 if iw(p) else -1)*PVAL.get(p.upper(),0)
    return score if w_persp else -score

def ab(board,depth,alpha,beta,w,castle,ep,stop_ev,phist):
    if stop_ev.is_set(): return 0,None
    mvs=legal_moves(board,w,castle,ep)
    if not mvs:
        return(-29000 if in_check(board,w) else -CONTEMPT),None
    if depth==0:
        return evaluate(board,w),None
    mvs.sort(key=lambda m:-(PVAL.get((board[m[2]][m[3]] or ' ').upper(),0)))
    best=-999999; bestmv=mvs[0]
    for mv in mvs:
        if stop_ev.is_set(): break
        nb,nc,ne,_=do_move(board,mv,castle,ep)
        key=''.join(p or '.' for row in nb for p in row)
        np2=dict(phist); np2[key]=np2.get(key,0)+1
        v=-CONTEMPT if np2[key]>=2 else -(ab(nb,depth-1,-beta,-alpha,not w,nc,ne,stop_ev,np2)[0])
        if v>best: best=v; bestmv=mv
        if v>alpha: alpha=v
        if alpha>=beta: break
    return best,bestmv

def think_ki(board,w,castle,ep,depth,stop_ev,phist):
    lm=legal_moves(board,w,castle,ep)
    if not lm: return None
    best=lm[0]
    for d in range(1,depth+1):
        if stop_ev.is_set(): break
        _,mv=ab(board,d,-999999,999999,w,castle,ep,stop_ev,dict(phist))
        if mv and mv in lm and not stop_ev.is_set(): best=mv
    return best if best in lm else lm[0]

# ══════════════════════════════════════════════════════════════════════
# BRETT-WIDGET  (GridLayout mit Buttons — zuverlässig auf Android)
# ══════════════════════════════════════════════════════════════════════
class SqBtn(Button):
    def __init__(self, row, col, **kw):
        super().__init__(**kw)
        self.row=row; self.col=col
        self.background_normal=''
        self.font_size=dp(18)
        self.bold=True
        self.border=(0,0,0,0)
        self._set_bg(False,False,False)

    def update(self, piece, sel, hl, dot, chk):
        light=(self.row+self.col)%2==0
        # Hintergrundfarbe
        if chk:      bg=CHK_C
        elif sel:    bg=SEL_C
        elif hl:     bg=HL_L if light else HL_D
        else:        bg=SQ_L if light else SQ_D
        self.background_color=bg
        # Text
        if piece:
            self.text=PL.get(piece,'?')
            self.color=(0.08,0.08,0.08,1) if iw(piece) else (0.98,0.98,0.98,1)
            self.font_size=dp(20)
        elif dot:
            self.text='*'
            self.color=DOT_C
            self.font_size=dp(14)
        else:
            self.text=''

    def _set_bg(self,sel,hl,chk):
        light=(self.row+self.col)%2==0
        if chk: self.background_color=CHK_C
        elif sel: self.background_color=SEL_C
        elif hl: self.background_color=HL_L if light else HL_D
        else: self.background_color=SQ_L if light else SQ_D


class BoardGrid(GridLayout):
    def __init__(self, app_ref, **kw):
        super().__init__(cols=8, spacing=0, **kw)
        self.app_ref=app_ref
        self.sqs={}
        # Rank 7..0 von oben nach unten
        for rank in range(7,-1,-1):
            for fil in range(8):
                btn=SqBtn(rank,fil,size_hint=(1,None))
                btn.bind(on_press=lambda b,r=rank,c=fil: self.app_ref.on_tap(r,c))
                self.sqs[(rank,fil)]=btn
                self.add_widget(btn)
        self.bind(width=self._resize)

    def _resize(self,*a):
        sq=self.width/8
        for btn in self.sqs.values():
            btn.height=sq
            btn.font_size=sq*0.55

    def refresh(self, board, selected, legal_hl, last_mv, chkside):
        for (r,c),btn in self.sqs.items():
            p=board[r][c]
            sel=selected==(r,c)
            hl=bool(last_mv and(
                (last_mv[0]==r and last_mv[1]==c) or
                (last_mv[2]==r and last_mv[3]==c)))
            dot=(r,c) in legal_hl
            chk=(p=='K' and chkside is True) or (p=='k' and chkside is False)
            btn.update(p,sel,hl,dot,chk)


# ══════════════════════════════════════════════════════════════════════
# HAUPT-APP
# ══════════════════════════════════════════════════════════════════════
class ChessApp(App):

    def __init__(self,**kw):
        super().__init__(**kw)
        # Spielzustand
        self._reset_state()
        # Einstellungen
        self.mode      ='kiki'    # 'kiki' | 'human_ki' | 'human_human'
        self.human_col =True      # True=Weiss spielt Mensch
        self.depth_w   =2
        self.depth_b   =2
        # Threading
        self._stop_ev  =threading.Event()
        self._ki_busy  =False
        # UI-Refs (werden in build() gesetzt)
        self.board_grid=None
        self.status_lbl=None
        self.clock_w   =None
        self.clock_b   =None
        self.log_lbl   =None

    def _reset_state(self):
        self.board  =[list(r) for r in INIT]
        self.wturn  =True
        self.castle =frozenset('KQkq')
        self.ep     =None
        self.phist  ={}
        self.hclk   =0
        self.mc     =0
        self.last_mv=None
        self.chkside=None
        self.selected=None
        self.legal_hl=[]
        self.log_lines=[]
        self.running=False

    # ── Build UI ──────────────────────────────────────────────────────
    def build(self):
        Window.clearcolor=BG
        root=BoxLayout(orientation='vertical',spacing=dp(2),padding=dp(3))

        # Titel
        root.add_widget(Label(
            text='Schach Pro',
            size_hint_y=None,height=dp(30),
            font_size=dp(17),bold=True,color=ACCENT))

        # Status
        self.status_lbl=Label(
            text='Bereit  -  Einstellungen -> Start',
            size_hint_y=None,height=dp(20),
            font_size=dp(11),color=TXT_DIM)
        root.add_widget(self.status_lbl)

        # Uhr Schwarz
        self.clock_b=Label(
            text='Schwarz',size_hint_y=None,height=dp(24),
            font_size=dp(13),bold=True,color=(0.9,0.4,0.4,1))
        root.add_widget(self.clock_b)

        # Brett
        self.board_grid=BoardGrid(self)
        root.add_widget(self.board_grid)
        self.board_grid.refresh(self.board,None,[],None,None)

        # Uhr Weiss
        self.clock_w=Label(
            text='Weiss',size_hint_y=None,height=dp(24),
            font_size=dp(13),bold=True,color=(0.4,0.9,0.4,1))
        root.add_widget(self.clock_w)

        # Buttons
        btn_row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(4))
        for txt,fn in [('START',self.start_game),
                       ('STOPP',self.stop_game),
                       ('NEU',  self.new_game),
                       ('OPT',  self.open_settings)]:
            b=Button(text=txt,font_size=dp(13),bold=True,
                     background_normal='',
                     background_color=ACCENT if txt=='START' else BTN_DK,
                     color=ACCENT_T if txt=='START' else TXT_LT)
            b.bind(on_press=lambda x,f=fn:f())
            btn_row.add_widget(b)
        root.add_widget(btn_row)

        # Zuglog
        sv=ScrollView(size_hint_y=None,height=dp(70))
        self.log_lbl=Label(
            text='',font_size=dp(10),
            size_hint_y=None,color=TXT_LT,
            halign='left',valign='top')
        self.log_lbl.bind(texture_size=self.log_lbl.setter('size'))
        sv.add_widget(self.log_lbl)
        root.add_widget(sv)

        # Legende
        root.add_widget(Label(
            text='W: K=Koenig D=Dame T=Turm L=Laeufer S=Springer B=Bauer'
                 '  |  s: k d t l s b',
            size_hint_y=None,height=dp(22),
            font_size=dp(8),color=TXT_DIM))

        return root

    # ── Tap ───────────────────────────────────────────────────────────
    def on_tap(self,r,c):
        if not self.running or self._ki_busy: return
        if self.mode=='kiki': return

        # Welche Farbe darf klicken?
        if self.mode=='human_ki':
            if self.wturn!=self.human_col: return
            hw=self.human_col
        else:   # human_human
            hw=self.wturn

        # Figur auswählen
        if self.selected is None:
            p=self.board[r][c]
            if p and iw(p)==hw:
                self.selected=(r,c)
                lm=legal_moves(self.board,hw,self.castle,self.ep)
                self.legal_hl=[(m[2],m[3]) for m in lm if m[0]==r and m[1]==c]
        else:
            lm=legal_moves(self.board,hw,self.castle,self.ep)
            mv=(self.selected[0],self.selected[1],r,c)
            if mv in lm:
                self.selected=None; self.legal_hl=[]
                self._apply(mv,hw)
                Clock.schedule_once(self._refresh,0)
                if not self._check_end():
                    if self.mode=='human_ki':
                        threading.Thread(target=self._ki_one,daemon=True).start()
                    else:
                        nxt='Weiss' if self.wturn else 'Schwarz'
                        self._setstatus(nxt+' am Zug')
                return
            else:
                p=self.board[r][c]
                if p and iw(p)==hw:
                    self.selected=(r,c)
                    lm2=legal_moves(self.board,hw,self.castle,self.ep)
                    self.legal_hl=[(m[2],m[3]) for m in lm2 if m[0]==r and m[1]==c]
                else:
                    self.selected=None; self.legal_hl=[]

        Clock.schedule_once(self._refresh,0)

    # ── Zug anwenden ─────────────────────────────────────────────────
    def _apply(self,mv,w):
        pc=self.board[mv[0]][mv[1]]
        nb,nc,ne,cap=do_move(self.board,mv,self.castle,self.ep)
        self.board=nb; self.castle=nc; self.ep=ne; self.last_mv=mv
        self.wturn=not w; self.mc+=1
        if cap or(pc and pc.upper()=='P'): self.hclk=0
        else: self.hclk+=1
        ochk=in_check(self.board,not w)
        self.chkside=(not w) if ochk else None
        key=''.join(p or '.' for row in self.board for p in row)
        self.phist[key]=self.phist.get(key,0)+1
        cap_s=('x'+PL.get(cap,'?')) if cap else ''
        chk_s='+' if ochk else ''
        self.log_lines.append(
            f"{self.mc}. {PL.get(pc,'?')}{FILES[mv[1]]}{8-mv[0]}"
            f"{cap_s}{FILES[mv[3]]}{8-mv[2]}{chk_s}")

    # ── Start/Stopp/Neu ───────────────────────────────────────────────
    def start_game(self,*a):
        if self.running: return
        self._reset_state()
        self._stop_ev.clear()
        self.running=True
        Clock.schedule_once(self._refresh,0)
        if self.mode=='kiki':
            self._setstatus('KI vs KI...')
            threading.Thread(target=self._ki_loop,daemon=True).start()
        elif self.mode=='human_ki':
            if self.human_col:
                self._setstatus('Dein Zug (Weiss)')
            else:
                self._setstatus('KI denkt...')
                threading.Thread(target=self._ki_one,daemon=True).start()
        else:
            self._setstatus('Weiss am Zug')

    def stop_game(self,*a):
        self._stop_ev.set()
        self.running=False; self._ki_busy=False
        self._setstatus('Gestoppt.')

    def new_game(self,*a):
        self.stop_game()
        def _do(dt):
            self._reset_state()
            self._stop_ev.clear()
            Clock.schedule_once(self._refresh,0)
            self._setstatus('Bereit  -  druecke START')
        Clock.schedule_once(_do,0.3)

    # ── KI-Schleifen ─────────────────────────────────────────────────
    def _ki_loop(self):
        while self.running and not self._stop_ev.is_set():
            if self._check_end(): return
            w=self.wturn
            self._setstatus(('Weiss' if w else 'Schwarz')+' denkt...')
            self._ki_busy=True
            mv=think_ki(self.board,w,self.castle,self.ep,
                        self.depth_w if w else self.depth_b,
                        self._stop_ev,self.phist)
            self._ki_busy=False
            if self._stop_ev.is_set(): return
            if mv:
                self._apply(mv,w)
                Clock.schedule_once(self._refresh,0)
            time.sleep(0.3)

    def _ki_one(self):
        if self._stop_ev.is_set() or not self.running: return
        w=self.wturn
        self._setstatus(('Weiss' if w else 'Schwarz')+' (KI) denkt...')
        self._ki_busy=True
        mv=think_ki(self.board,w,self.castle,self.ep,
                    self.depth_w if w else self.depth_b,
                    self._stop_ev,self.phist)
        self._ki_busy=False
        if self._stop_ev.is_set() or not self.running: return
        if mv:
            self._apply(mv,w)
            Clock.schedule_once(self._refresh,0)
            if not self._check_end() and self.mode=='human_ki':
                hw=self.human_col
                nxt='Dein Zug ('+ ('Weiss' if hw else 'Schwarz')+')'
                self._setstatus(nxt)

    # ── Spielende ────────────────────────────────────────────────────
    def _check_end(self):
        lm=legal_moves(self.board,self.wturn,self.castle,self.ep)
        msg=None
        if not lm:
            if in_check(self.board,self.wturn):
                w='Schwarz' if self.wturn else 'Weiss'
                msg=w+' gewinnt! Schachmatt!'
            else:
                msg='Remis - Patt!'
        elif self.hclk>=100:
            msg='Remis - 50-Zuege-Regel'
        else:
            key=''.join(p or '.' for row in self.board for p in row)
            if self.phist.get(key,0)>=3:
                msg='Remis - 3x Wiederholung'
        if msg:
            self._stop_ev.set(); self.running=False
            self._setstatus(msg)
            Clock.schedule_once(lambda dt:self._popup(msg),0.3)
            Clock.schedule_once(self._refresh,0)
            return True
        return False

    # ── UI-Helfer ─────────────────────────────────────────────────────
    def _refresh(self,dt=0):
        try:
            self.board_grid.refresh(
                self.board,self.selected,self.legal_hl,
                self.last_mv,self.chkside)
            wt=self.wturn
            self.clock_w.text='Weiss'+(' < am Zug' if wt else '')
            self.clock_b.text='Schwarz'+(' < am Zug' if not wt else '')
            self.log_lbl.text='\n'.join(self.log_lines[-18:])
        except Exception:
            pass

    def _setstatus(self,txt):
        def _do(dt):
            try: self.status_lbl.text=str(txt)
            except Exception: pass
        Clock.schedule_once(_do,0)

    def _popup(self,msg):
        try:
            content=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8))
            content.add_widget(Label(text=str(msg),font_size=dp(16),color=TXT_LT))
            btn=Button(text='OK',size_hint_y=None,height=dp(44),
                       background_normal='',background_color=ACCENT,color=ACCENT_T,
                       font_size=dp(14),bold=True)
            content.add_widget(btn)
            pop=Popup(title='Spiel beendet',content=content,
                      size_hint=(0.85,0.38),auto_dismiss=False)
            btn.bind(on_press=pop.dismiss)
            pop.open()
        except Exception:
            pass

    # ── Einstellungen ─────────────────────────────────────────────────
    def open_settings(self,*a):
        try:
            content=BoxLayout(orientation='vertical',padding=dp(10),spacing=dp(8))

            def row_label(txt):
                content.add_widget(Label(
                    text=txt,size_hint_y=None,height=dp(22),
                    font_size=dp(12),color=ACCENT,halign='left'))

            def btn_row(options, current, on_pick):
                row=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(4))
                for lbl,val in options:
                    active=(current==val)
                    b=Button(text=lbl,font_size=dp(11),bold=active,
                             background_normal='',
                             background_color=ACCENT if active else BTN_DK,
                             color=ACCENT_T if active else TXT_LT)
                    b.bind(on_press=lambda x,v=val:on_pick(v))
                    row.add_widget(b)
                content.add_widget(row)

            # Modus
            row_label('Spielmodus')
            def set_mode(v): self.mode=v; pop.dismiss(); self.open_settings()
            btn_row([('KI vs KI','kiki'),('Mensch/KI','human_ki'),('Mensch/Mensch','human_human')],
                    self.mode, set_mode)

            # Farbe (nur bei human_ki)
            if self.mode=='human_ki':
                row_label('Ich spiele')
                def set_col(v): self.human_col=v; pop.dismiss(); self.open_settings()
                btn_row([('Weiss',True),('Schwarz',False)], self.human_col, set_col)

            # Staerke
            row_label('Weiss Staerke')
            def set_dw(v): self.depth_w=v; pop.dismiss(); self.open_settings()
            btn_row([('Einfach',1),('Mittel',2),('Stark',3)], self.depth_w, set_dw)

            row_label('Schwarz Staerke')
            def set_db(v): self.depth_b=v; pop.dismiss(); self.open_settings()
            btn_row([('Einfach',1),('Mittel',2),('Stark',3)], self.depth_b, set_db)

            close=Button(text='Schliessen',size_hint_y=None,height=dp(44),
                         background_normal='',background_color=BTN_DK,
                         color=TXT_LT,font_size=dp(13))
            content.add_widget(close)

            pop=Popup(title='Einstellungen',content=content,
                      size_hint=(0.95,0.88),auto_dismiss=True)
            close.bind(on_press=pop.dismiss)
            pop.open()
        except Exception as e:
            self._setstatus('Fehler: '+str(e))


if __name__ == '__main__':
    ChessApp().run()
