B1='            page = await context.new_page()'
B0='        try:'
A_='send_keys'
Az='open_tab'
Ay='scroll_up'
Ax='scroll_down'
Aw='go_back'
Av='scroll_to_text'
Au='go_to_url'
At='label='
As='text="([^"]*)"'
Ar='placeholder='
Aq='[data-testid='
Ap='[name="'
Ao='[name='
An='Smart scroll failed; used window.scrollBy fallback'
Am='(y) => window.scrollBy(0, y)'
Al='() => window.innerHeight'
Ak='networkidle'
Aj='select'
AN='switch_tab'
AM='height'
AL='width'
AK='click'
A8='\n'
A7='keys'
A6='seconds'
A5='wait'
A4=enumerate
A3=hasattr
u='select_dropdown_option'
t='click_element_by_index'
s='input_text'
n="'"
m='page_id'
l='selector'
k='="'
j='role='
i=open
d='domcontentloaded'
c='"'
a='"]'
Y='css_selector'
X='url'
W=False
V=str
T='xpath'
N='text'
M='action'
H=Exception
G=print
D=''
C=True
B=None
import asyncio as Q
from copy import deepcopy as v
import os
from playwright.async_api import async_playwright as B2,Page
import re,logging,json as I
from typing import Any
from browser_use.browser.browser import BrowserConfig,BrowserContextConfig
A=logging.getLogger(__name__)
AO='parentClass'
AP='parentTag'
AQ='src'
AR='attached'
AS='json_value'
AT='tab'
AU='menuitem'
AV='option'
AW='cell'
AX='listitem'
AY='.*_ngcontent-.*'
AZ='.*\\d{10,}.*'
Aa=Aj
Ab='textarea'
Ac=A3
Ad=isinstance
A9='href'
AA='name'
AB='placeholder'
AC='alt'
AD='reset'
AE='submit'
AF='link'
AG='a'
AH=W
w='.'
x='?'
y='class'
z='formClass'
A0='form'
A1=V
o='value'
p='aria-label'
e='img'
b=B
Z='heading'
R=' '
S='type'
O='input'
P=len
K='button'
L=H
J=D
E='\\"'
F=c
import re
from typing import Any,Awaitable,Callable,Dict,List,Optional
from playwright.async_api import ElementHandle,Page
B3=['data-testid','data-test-id','data-test','data-cy','test-id']
Ae=[O,Ab,Aa]
q=100
B4=20
B5=20
Bd=10
def AI(value,patterns):
	A=value
	if not A:return AH
	return any(re.match(B,A,re.IGNORECASE)for B in patterns)
def B6(id_value):A=[AZ,'[a-f0-9]{8}-[a-f0-9]{4}-','^[a-f0-9]{20,}$',AY,'^ember\\d+$','^react-.*','ui-id-\\d+','yui_3_\\d+_\\d+_\\d+_\\d+'];return AI(id_value,A)
def U(class_name):A=['.*\\d{8,}.*','.*[a-f0-9]{6,}.*','^css-[a-z0-9]+$','.*__[a-f0-9]{5,}$','.*_nghost-.*',AY,'^style-\\w+$','^class\\d+$'];return AI(class_name,A)
def A2(attr_value):A=[AZ,'[a-f0-9]{16,}','.*uuid.*','.*guid.*'];return AI(attr_value,A)
async def f(page,selector):
	A=selector
	if not A:return AH
	try:B=await page.locator(A).count();return B==1
	except L as C:return AH
async def AJ(element,tag_name):
	C='radio';D='checkbox';E=N;F='list';G='table';H='article';I='main';J=element;B=tag_name;A='textbox'
	try:
		M=await J.get_attribute('role')
		if M:return M.lower()
		P={AG:AF,K:K,Aa:'combobox',Ab:A,e:e,'nav':'navigation',I:I,'header':'banner','footer':'contentinfo','aside':'complementary',A0:A0,H:H,'h1':Z,'h2':Z,'h3':Z,'h4':Z,'h5':Z,'h6':Z,'ul':F,'ol':F,'li':AX,G:G,'th':'columnheader','td':AW,'tr':'row'}
		if B in P:return P[B]
		if B==O:Q=(await J.get_attribute(S)or E).lower();R={K:K,AE:K,AD:K,D:D,C:C,'search':'searchbox','email':A,'number':'spinbutton','tel':A,X:A,E:A,'password':A,'date':A,'time':A,'datetime-local':A,'month':A,'week':A};return R.get(Q,A)
		return
	except L:return
async def B7(element,tag_name):
	B=tag_name;A=element;C=await A.get_attribute(p)
	if C is not b:return C.strip()
	G=await AJ(A,B)
	if G in[AV,K,AF,AU,AT,Z]:
		D=await A.inner_text()
		if D is not b:return D.strip()
	if B==O:
		H=(await A.get_attribute(S)or J).lower()
		if H in[K,AE,AD]:
			E=await A.get_attribute(o)
			if E is not b:return E.strip()
	if B==e:
		F=await A.get_attribute(AC)
		if F is not b:return F.strip()
async def B8(element,tag_name):
	D=tag_name;A=element;B=[]
	try:
		E=await A.get_attribute(p)
		if E and E.strip():B.append(E.strip())
		if not B:
			C=J;G=await AJ(A,D)
			if G in[K,AF,Z,AV,AU,AT,AX,AW,'label']:C=await A.inner_text()
			elif D==O:
				H=(await A.get_attribute(S)or J).lower()
				if H in[AE,K,AD]:C=await A.get_attribute(o)or J
			elif D==e:C=await A.get_attribute(AC)or J
			if C and C.strip():B.append(C.strip())
		if not B:
			F=await A.get_attribute('title')
			if F and F.strip():B.append(F.strip())
		if B:return R.join(R.join(A.split()).strip()for A in B if A)
	except L:pass
	return J
async def g(value):
	A=value
	if A is not b and not Ad(A,(A1,int,float,bool,dict,list))and Ac(A,AS):
		try:return await A.json_value()
		except L:pass
	return A
async def B9(page,element):
	C=element
	try:
		D=await C.get_attribute('id')
		if D:
			try:
				E=page.locator(f'label[for="{D}"]').first;await E.wait_for(state=AR,timeout=200);A=await E.text_content()
				if A and A.strip():return R.join(A.strip().split())
			except L:pass
		F=await C.evaluate("(el) => el.closest('label') ? el.closest('label').textContent.trim() : null");B=await g(F)
		if B and A1(B).strip():return R.join(A1(B).strip().split())
	except L:pass
async def BA(page,element):
	for A in B3:
		B=await element.get_attribute(A)
		if B:
			C=f'[{A}="{B}"]';D=await page.locator(C).count()
			if D==1:return C
async def BB(page,element,tag_name):
	B=tag_name;D=element;G=page;A=await AJ(D,B)
	if not A:return
	H=await B7(D,B)
	if H is not b:
		try:
			M=await G.get_by_role(A,name=H,exact=C).count()
			if M==1:N=H.replace(F,E);O=f'role={A}[name="{N}"]';return O
		except L as Q:pass
	I=await B8(D,B)
	if I:
		P=I.replace(F,E);J=f'role={A}[name="{P}"]'
		if await f(G,J):return J
	K=f"role={A}"
	if await f(G,K):return K
async def BC(page,element,tag_name):
	C=tag_name;D=element;A=page
	if C not in Ae:return
	K=await B9(A,D)
	if K:
		T=K.replace(F,E);L=f'label="{T}"'
		if await f(A,L):return L
	G=await D.get_attribute(AB)
	if G and G.strip():
		U=R.join(G.strip().split());H=U.replace(F,E);M=f'[placeholder="{H}"]';B=await A.locator(M).count()
		if B==1:return M
		N=f'{C}[placeholder="{H}"]';B=await A.locator(N).count()
		if B==1:return N
		if C==O:
			P=await D.get_attribute(S)
			if P:
				I=f'input[type="{P}"][placeholder="{H}"]';B=await A.locator(I).count()
				if B==1:return I
				if B>1:
					J=f"{I}:visible";Q=await A.locator(J).count()
					if Q==1:return J
					elif Q>1:return f"{J} >> nth=0"
async def BD(page,element):
	C=await element.text_content()
	if not C:return
	A=C.strip()
	if not A or P(A)>q:return
	B=R.join(A.split());I=B.replace(F,E);D=f'text="{I}"'
	if await f(page,D):return D
	if P(B)>B4:
		G=B[:B5].strip()
		if G:
			J=G.replace(F,E);H=f'text="{J}"'
			if await f(page,H):return H
async def BE(page,element):
	A=await element.get_attribute('id')
	if not A:return
	if B6(A):return
	B=f"#{A}";C=await page.locator(B).count()
	if C==1:return B
	else:0
async def BF(page,element):
	A=await element.get_attribute(AA)
	if A and not A2(A):
		B=f'[name="{A}"]'
		if await f(page,B):return B
async def BG(page,element,tag_name):
	F=element;D=tag_name;E=page;B=await F.get_attribute(p)
	if not B:return
	H=f'[aria-label="{B}"]';A=await E.locator(H).count()
	if A==1:return H
	I=f'{D}[aria-label="{B}"]';A=await E.locator(I).count()
	if A==1:return I
	if D in[K,O]:
		J=await F.get_attribute(S)
		if J:
			L=f'{D}[type="{J}"][aria-label="{B}"]';A=await E.locator(L).count()
			if A==1:return L
	if A>1:
		C=await F.evaluate("\n            (el) => {\n                const parent = el.parentElement;\n                if (!parent) return null;\n                \n                // Look for form parent\n                const form = el.closest('form');\n                if (form) {\n                    return {\n                        type: 'form',\n                        formClass: form.className || '',\n                        formId: form.id || ''\n                    };\n                }\n                \n                // Look for div parent with meaningful class\n                const div = el.closest('div[class]');\n                if (div) {\n                    return {\n                        type: 'div',\n                        divClass: div.className || ''\n                    };\n                }\n                \n                return null;\n            }\n        ");C=await g(C)
		if C:
			if C.get(S)==A0:
				if C.get(z):
					M=[A for A in C[z].split()if not U(A)]
					if M:
						N=f'form.{M[0]} {D}[aria-label="{B}"]';A=await E.locator(N).count()
						if A==1:return N
			G=f'{D}[aria-label="{B}"]:visible';P=await E.locator(G).count()
			if P==1:return G
			elif P>1:return f"{G} >> nth=0"
async def BH(page,element,tag_name):
	G=element;D=tag_name;C=page
	if D not in[K,O]:return
	A=await G.get_attribute(o)
	if not A:return
	if A.isdigit()and 3<=P(A)<=10:
		H=f'[value="{A}"]';B=await C.locator(H).count()
		if B==1:return H
		I=f'{D}[value="{A}"]';B=await C.locator(I).count()
		if B==1:return I
		J=await G.get_attribute(AA)
		if J:
			E=f'{D}[name="{J}"][value="{A}"]';B=await C.locator(E).count()
			if B==1:return E
			if B>1:
				F=f"{E}:visible";L=await C.locator(F).count()
				if L==1:return F
				elif L>1:return f"{F} >> nth=0"
async def BI(page,element,tag_name):
	X='formRole';Y='formId';I=element;D=page;C=tag_name
	try:
		G=await I.evaluate("\n            (el) => {\n                const form = el.closest('form');\n                if (!form) return null;\n                \n                return {\n                    hasForm: true,\n                    formClass: form.className || '',\n                    formId: form.id || '',\n                    formAction: form.action || '',\n                    formRole: form.getAttribute('role') || ''\n                };\n            }\n        ");G=await g(G)
		if not G or not G.get('hasForm'):return
		M=[]
		if G.get(Y):M.append(f"form#{G[Y]}")
		if G.get(z):
			Z=[A for A in G[z].split()if not U(A)]
			if Z:M.append(f"form.{Z[0]}")
		if G.get(X):M.append(f'form[role="{G[X]}"]')
		if not M:M.append(A0)
		for H in M:
			A=f"{H} {C}";B=await D.locator(A).count()
			if B==1:return A
			Q=await I.get_attribute(AA)
			if Q:
				A=f'{H} {C}[name="{Q}"]';B=await D.locator(A).count()
				if B==1:return A
			if C in[K,O]:
				T=await I.get_attribute(p)
				if T:
					A=f'{H} {C}[aria-label="{T}"]';B=await D.locator(A).count()
					if B==1:return A
					a=await I.get_attribute(S)
					if a:
						A=f'{H} {C}[type="{a}"][aria-label="{T}"]';B=await D.locator(A).count()
						if B==1:return A
					if B>1:
						J=f'{H} {C}[aria-label="{T}"]:visible';N=await D.locator(J).count()
						if N==1:return J
						elif N>1:return f"{J} >> nth=0"
			if C in[K,O]:
				V=await I.get_attribute(o)
				if V:
					A=f'{H} {C}[value="{V}"]';B=await D.locator(A).count()
					if B==1:return A
					if Q:
						A=f'{H} {C}[name="{Q}"][value="{V}"]';B=await D.locator(A).count()
						if B==1:return A
			W=await I.text_content()
			if W and P(W.strip())<=q:
				d=R.join(W.strip().split());e=d.replace(F,E);A=f'{H} {C}:has-text("{e}")';B=await D.locator(A).count()
				if B==1:return A
			b=await I.get_attribute(y)
			if b:
				c=[A for A in b.split()if not U(A)]
				if c:
					A=f"{H} {C}.{c[0]}";B=await D.locator(A).count()
					if B==1:return A
					J=f"{A}:visible";N=await D.locator(J).count()
					if N==1:return J
					elif N>1:return f"{J} >> nth=0"
	except L as f:raise f
async def BJ(page,element,tag_name):
	G=element;C=page
	if tag_name!=e:return
	try:
		D=await G.get_attribute(AQ)
		if not D:return
		H=D.replace(F,E);I=f'img[src="{H}"]';A=await C.locator(I).count()
		if A==1:return I
		if x in D and A!=1:
			Q=D.split(x)[0];R=Q.replace(F,E);J=f'img[src^="{R}"]';A=await C.locator(J).count()
			if A==1:return J
		K=await G.get_attribute(AC)
		if K:
			S=K.replace(F,E);M=f'img[src="{H}"][alt="{S}"]';A=await C.locator(M).count()
			if A==1:return M
		B=await G.evaluate("\n            (el) => {\n                const parent = el.parentElement;\n                if (!parent) return null;\n                return {\n                    tag: parent.tagName.toLowerCase(),\n                    classes: parent.className || '',\n                    href: parent.getAttribute('href') || ''\n                };\n            }\n        ");B=await g(B)
		if B and B.get('tag')==AG and B.get(A9):
			N=B[A9].replace(F,E);O=f'a[href="{N}"] > img';A=await C.locator(O).count()
			if A==1:return O
			P=f'a[href="{N}"] > img[src="{H}"]';A=await C.locator(P).count()
			if A==1:return P
	except L as T:raise T
async def BK(page,element,tag_name):
	try:
		B=await element.get_attribute(y)
		if not B:return
		D=B.split();A=[A for A in D if not U(A)]
		if not A:return
		for E in range(1,min(P(A)+1,4)):
			F=A[:E];C=f"{tag_name}.{w.join(F)}";G=await page.locator(C).count()
			if G==1:return C
	except L as H:raise H
async def BL(page,element,tag_name):
	D=tag_name;G=element;A=page
	try:
		j=await G.text_content();H=j.strip()if j else J;B=[D];k=await G.get_attribute(y)
		if k:
			l=[A for A in k.split()if not U(A)]
			if l:B.append(w+w.join(l[:2]))
		if D==O:
			W=await G.get_attribute(S)
			if W and not A2(W):B.append(f'[type="{W}"]')
		if P(B)>1:
			N=J.join(B);AH=await A.locator(N).count()
			if AH==1:return N
			if D in Ae:
				m=await G.get_attribute(AB)
				if m:
					AI=m.replace(F,E);X=f'{N}[placeholder="{AI}"]';n=await A.locator(X).count()
					if n==1:return X
					if n>1:
						Y=f"{X}:visible";r=await A.locator(Y).count()
						if r==1:return Y
						elif r>1:return f"{Y} >> nth=0"
			if H:
				C=R.join(H.split())
				if C and P(C)<=q:
					M=C.replace(F,E);s=f'{N}:has-text("{M}")';AJ=await A.locator(s).count()
					if AJ==1:return s
				else:0
		if D==AG:
			Z=await G.get_attribute(A9)
			if Z and not A2(Z):
				t=Z.replace(F,E);I=f'{B[0]}[href="{t}"]';u=await A.locator(I).count()
				if P(B)>1 and B[1].startswith(w):
					I=f'{B[0]}{B[1]}[href="{t}"]';v=await A.locator(I).count()
					if v==1:return I
					u=v
				if u==1:return I
				if H:
					C=R.join(H.split())
					if C and P(C)<=q:
						M=C.replace(F,E);a=f'{I}:has-text("{M}")';AK=await A.locator(a).count()
						if AK==1:return a
						z=f"{a}:visible";AL=await A.locator(z).count()
						if AL>0:return z
			else:0
		if D in[K,O]:
			b=await G.get_attribute(o)
			if b and not A2(b):
				A0=b.replace(F,E);Q=f'{D}[value="{A0}"]';AM=await A.locator(Q).count()
				if AM==1:return Q
				if P(B)>1:
					A1=f'{J.join(B)}[value="{A0}"]';AN=await A.locator(A1).count()
					if AN==1:return A1
				if H:
					C=R.join(H.split())
					if C and P(C)<=q:
						M=C.replace(F,E);c=f'{Q}:has-text("{M}")';A3=await A.locator(c).count()
						if A3==1:return c
						if A3>1:
							d=f"{c}:visible";A4=await A.locator(d).count()
							if A4==1:return d
							elif A4>1:return f"{d} >> nth=0"
				f=f"{Q}:visible";A5=await A.locator(f).count()
				if A5==1:return f
				elif A5>1:return f"{f} >> nth=0"
			A6=await G.get_attribute(p)
			if A6:
				T=A6.replace(F,E);g=f'{D}[aria-label="{T}"]';AO=await A.locator(g).count()
				if AO==1:return g
				if P(B)>1:
					A7=f'{J.join(B)}[aria-label="{T}"]';AP=await A.locator(A7).count()
					if AP==1:return A7
				h=await G.get_attribute(S)
				if h:
					A8=f'{D}[type="{h}"][aria-label="{T}"]';AR=await A.locator(A8).count()
					if AR==1:return A8
					if P(B)>1:
						AA=f'{J.join(B)}[type="{h}"][aria-label="{T}"]';AS=await A.locator(AA).count()
						if AS==1:return AA
				i=f"{g}:visible";AC=await A.locator(i).count()
				if AC==1:return i
				elif AC>1:return f"{i} >> nth=0"
		if D==e:
			V=await G.get_attribute(AQ)
			if V:
				AT=V.replace(F,E);AD=f'img[src="{AT}"]';AE=await A.locator(AD).count()
				if AE==1:return AD
				if x in V and AE!=1:
					AU=V.split(x)[0];AV=AU.replace(F,E);AF=f'img[src^="{AV}"]';AW=await A.locator(AF).count()
					if AW==1:return AF
	except L as AX:raise AX
async def BM(page,element):
	try:
		A=await element.evaluate('\n            (el) => {\n                const parent = el.parentElement;\n                if (!parent) {\n                    return null;\n                }\n                const children = Array.from(parent.children);\n                const childIndex = children.indexOf(el) + 1; // 1-based index for :nth-child()\n\n                return {\n                    parentTag: parent.tagName.toLowerCase(),\n                    parentClass: parent.className || "",\n                    childTag: el.tagName.toLowerCase(),\n                    childIndex,\n                };\n            }\n            ')
		if A and not Ad(A,dict)and Ac(A,AS):
			try:A=await A.json_value()
			except L:A=b
		if not A:return
		B=A[AP];C=A['childIndex'];D=A['childTag'];E=f"{B} > {D}:nth-child({C})";I=await page.locator(E).count()
		if I==1:return E
		F=A.get(AO,J)
		if F:
			G=[A for A in F.split()if not U(A)]
			if G:
				H=f"{B}.{G[0]} > {D}:nth-child({C})";K=await page.locator(H).count()
				if K==1:return H
			else:0
		else:0
	except L as M:raise M
async def BN(page,element,tag_name):
	I=element;G=page;C=tag_name
	try:
		B=await I.evaluate("\n            (el) => {\n                const parent = el.parentElement;\n                if (!parent) return null;\n                \n                // Get grandparent info too\n                const grandparent = parent.parentElement;\n                \n                return {\n                    parentTag: parent.tagName.toLowerCase(),\n                    parentClass: parent.className || '',\n                    parentId: parent.id || '',                    grandparentTag: grandparent ? grandparent.tagName.toLowerCase() : '',\n                    grandparentClass: grandparent ? grandparent.className || '' : '',\n                    // Check if element is visible\n                    isVisible: el.offsetParent !== null || window.getComputedStyle(el).display !== 'none'\n                };\n            }\n        ");B=await g(B)
		if not B:return
		K=B.get(AP,J);Z=B.get(AO,J).split();M=[A for A in Z if not U(A)]
		if M:
			Q=f"{K}.{M[0]} > {C}";A=await G.locator(Q).count()
			if A==1:return Q
			H=[]
			if C==O:
				R=await I.get_attribute(S)
				if R:H.append(f'[type="{R}"]')
			D=await I.get_attribute(AB)
			if D:H.append(f'[placeholder="{D.replace(F,E)}"]')
			T=await I.get_attribute(y)
			if T:
				V=[A for A in T.split()if not U(A)]
				if V:H.append(f".{V[0]}")
			if H:
				a=J.join(H);W=f"{K}.{M[0]} > {C}{a}";A=await G.locator(W).count()
				if A==1:return W
		b=B.get('grandparentTag',J);c=B.get('grandparentClass',J).split();X=[A for A in c if not U(A)]
		if X and K:
			N=f"{b}.{X[0]} {K} > {C}";A=await G.locator(N).count()
			if A==1:return N
			if D:
				Y=f'{N}[placeholder="{D.replace(F,E)}"]';A=await G.locator(Y).count()
				if A==1:return Y
		if B.get('isVisible'):
			if C==O and D:
				P=f'{C}[placeholder="{D.replace(F,E)}"]:visible';A=await G.locator(P).count()
				if A==1:return P
				elif A>1:return f"{P} >> nth=0"
	except L as d:raise d
async def r(page,xpath,action=AK):
	D=xpath;B=page
	try:
		F=B.locator(D).first;await F.wait_for(state=AR,timeout=3000);A=await F.element_handle();K=await A.evaluate('el => el.outerHTML')
		if not A:return D
		E=await A.evaluate('(el) => el.tagName.toLowerCase()');E=await g(E);C=A1(E).lower();H=[lambda:BA(B,A),lambda:BB(B,A,C),lambda:BG(B,A,C),lambda:BC(B,A,C),lambda:BD(B,A),lambda:BE(B,A),lambda:BF(B,A),lambda:BH(B,A,C),lambda:BI(B,A,C),lambda:BJ(B,A,C),lambda:BK(B,A,C),lambda:BL(B,A,C),lambda:BN(B,A,C),lambda:BM(B,A)]
		for(M,I)in A4(H):
			G=await I()
			if G:return G
			else:0
		return D
	except L as J:raise J;return D
async def h(page,timeout=3000):
	B=timeout
	try:await page.wait_for_load_state(Ak,timeout=B);await page.wait_for_load_state(d,timeout=B);await Q.sleep(1)
	except H as C:A.debug(f"Timeout waiting for page to stabilize: {C}")
async def BO(url,page):await page.goto(url);await h(page);B=f"🔗  Navigated to {url}";A.info(B)
async def BP(text,page):
	E=page;C=text
	try:
		K=[E.get_by_text(C,exact=W),E.locator(f"text={C}"),E.locator(f"//*[contains(text(), '{C}')]")]
		for J in K:
			try:
				if await J.count()==0:continue
				F=await J.first;L=await F.is_visible();G=await F.bounding_box()
				if L and G is not B and G[AL]>0 and G[AM]>0:await F.scroll_into_view_if_needed();await Q.sleep(.5);D=f"🔍  Scrolled to text: {C}";A.info(D);return
			except H as I:A.debug(f"Locator attempt failed: {V(I)}");continue
		D=f"Text '{C}' not found or not visible on page";A.info(D)
	except H as I:D=f"Failed to scroll to text '{C}': {V(I)}";A.error(D)
async def BQ(seconds=3):B=seconds;C=f"🕒  Waiting for {B} seconds";A.info(C);await Q.sleep(B)
class Be(H):0
async def BR(page):
	try:await page.go_back(timeout=3000,wait_until=d);B=f"⏮️  Navigated back";A.info(B)
	except H as C:A.debug(f"⏮️  Error during go_back: {C}")
async def BS(page):
	B=page;C=await B.evaluate(Al)
	try:await B._scroll_container(C);D=f"🔍 Scrolled down the page by {C} pixels";A.info(D)
	except H as E:await B.evaluate(Am,C);A.debug(An,exc_info=E)
async def BT(page):
	B=page;C=await B.evaluate(Al)
	try:await B._scroll_container(-C);D=f"🔍 Scrolled up the page by {C} pixels";A.info(D)
	except H as E:await B.evaluate(Am,-C);A.debug(An,exc_info=E)
async def BU(url,page):B=await page.context.new_page();await B.goto(url);await h(B);await B.bring_to_front();C=f"🔗  Opened new tab with {url}";A.info(C);return B
async def BV(tab_index,page):
	C=tab_index;B=page.context.pages;G(B)
	if not B or C>=len(B):raise IndexError('Tab index out of range')
	D=B[C];await D.bring_to_front();A.info(f"Switched to tab {C}");return D
def BW(file_path):
	O='state';N='result';L='model_output';E='interacted_element'
	with i(file_path,'r')as P:Q=I.load(P)
	R=Q['history'];J=[];G=[];F=[]
	for H in R:
		K=H[L];S=H[N];C=H[O];C.pop('screenshot');U={L:K,N:S,O:C};J.append(U)
		for(D,A)in A4(K[M]):
			if len(F)>0 and A==G[-1]:continue
			if A.get(s,B):
				if C[E][D]:G.append(v(A));A[s][T]=C[E][D][T];A[s][Y]=C[E][D][Y];F.append(A)
			elif A.get(t,B):
				if C[E][D]:G.append(v(A));A[t][T]=C[E][D][T];A[t][Y]=C[E][D][Y];F.append(A)
			elif A.get(u,B):
				if C[E][D]:G.append(v(A));A[u][T]=C[E][D][T];A[u][Y]=C[E][D][Y];F.append(A)
			elif A.get(A5,B)and F[-1].get(A5,B):continue
			else:
				if A.get('extract_content',B)==B:G.append(v(A))
				F.append(A)
	return J,F
async def BX(keys,page):
	C=keys
	try:await page.keyboard.press(C)
	except H as B:
		if'Unknown key'in V(B):
			for D in C:
				try:await page.keyboard.press(D)
				except H as B:A.debug(f"Error sending key {D}: {V(B)}");raise B
		else:raise B
	E=f"⌨️  Sent keys: {C}";A.info(E);return E
async def Bf(page):B=page;F=re.sub('^https?://(?:www\\.)?|/$',D,B.url);G=re.sub('[^a-zA-Z0-9]+','-',F).strip('-').lower();C=f"{G}.pdf";await B.emulate_media(media='screen');await B.pdf(path=C,format='A4',print_background=W);E=f"Saving page with URL {B.url} as PDF to ./{C}";A.info(E);return E
async def BY(xpath,text,page):
	J=text;F=page;await h(F);E=await r(F,f"xpath={xpath}")
	try:
		if E.startswith(j):
			if Ao in E:K=E.split('[')[0].replace(j,D);N=E.split(Ap)[1].split(a)[0];G=F.get_by_role(K,name=N,exact=C)
			else:K=E.replace(j,D);G=F.get_by_role(K,exact=C)
		elif E.startswith(Aq):O=E.split(k)[1].split(a)[0];G=F.get_by_test_id(O,exact=C)
		elif E.startswith(Ar):P=E.split(k)[1].split(a)[0];G=F.get_by_placeholder(P,exact=C)
		elif E.startswith('text='):L=re.search(As,E);Q=L.group(1)if L else B;G=F.get_by_text(Q,exact=C)
		elif E.startswith(At):R=E.split(k)[1].split(a)[0];G=F.get_by_label(R,exact=C)
		else:G=F.locator(E).first
		M=await G.evaluate('el => el.tagName.toLowerCase()')
		if M!=Aj:I=f"⚠️ Element with selector '{E}' is a {M}, not a select element";A.warning(I);return I
		S=await G.select_option(label=J,timeout=3000);I=f"✅ Selected option '{J}' (value={S}) in dropdown with selector '{E}'";A.info(I);await h(F);return I
	except H as T:I=f"❌ Failed to select option '{J}' in dropdown: {T}";A.error(I);return I
async def Af(page,xpath,action,text=B,css_selector=B):
	P=action;M=css_selector;E=page;await h(E);A=await r(E,xpath)
	try:
		R=await E.locator(A).count()
		if R==0:raise H(f"No elements found with selector: {A}")
	except H as K:
		G(f"  Failed to use selector '{A}': {K}")
		if M:
			G(f"  Trying with CSS selector: {M}")
			try:
				A=await r(E,f"css={M}");R=await E.locator(A).count()
				if R==0:raise H(f"No elements found with CSS selector: {A}")
			except H as b:G(f"  Failed to use CSS selector: {b}");A=M;G(f"  Trying raw CSS selector: {A}")
	N=E.context;Y=N.pages.copy();J=W
	try:
		if A.startswith(j):
			if Ao in A:S=A.split('[')[0].replace(j,D);c=A.split(Ap)[1].split(a)[0];I=E.get_by_role(S,name=c,exact=C)
			else:S=A.replace(j,D);I=E.get_by_role(S,exact=C)
		elif A.startswith(Aq):e=A.split(k)[1].split(a)[0];I=E.get_by_test_id(e,exact=C)
		elif A.startswith(Ar):f=A.split(k)[1].split(a)[0];I=E.get_by_placeholder(f,exact=C)
		elif A.startswith('text='):Z=re.search(As,A);g=Z.group(1)if Z else B;I=E.get_by_text(g,exact=C)
		elif A.startswith(At):i=A.split(k)[1].split(a)[0];I=E.get_by_label(i,exact=C)
		else:I=E.locator(A).first
		if P==AK:
			T=E.url;U=B
			try:
				l=await I.get_attribute('target')
				if l=='_blank':U=N.wait_for_event('page')
			except:pass
			V=B
			try:V=E.wait_for_navigation(timeout=5000)
			except:pass
			await I.click(force=C,timeout=5000);O=W
			if V:
				try:await Q.wait_for(V,timeout=2.);O=C;G(f"  Navigation detected to: {E.url}");await E.wait_for_load_state(d)
				except Q.TimeoutError:pass
				except H as K:
					if E.url!=T:O=C;G(f"  Navigation detected to: {E.url}")
			if not O and U:
				try:F=await Q.wait_for(U,timeout=3.);await F.wait_for_load_state(d);G(f"  New tab/window detected, switching to new page: {F.url}");J=C;return A,F,J
				except Q.TimeoutError:pass
			if not O:
				await Q.sleep(1);X=N.pages;L=[A for A in X if A not in Y]
				if L:F=L[-1];await F.wait_for_load_state(d);G(f"  New tab/window detected, switching to new page: {F.url}");J=C;return A,F,J
			if E.url!=T:G(f"  Page navigated from {T} to {E.url}");await E.wait_for_load_state(d)
		elif P=='fill':await I.fill(text)
		G(f"  Action '{P}' successful with generated selector")
	except H as K:
		G(f"  Error with generated selector: {K}");X=N.pages;L=[A for A in X if A not in Y]
		if L:
			F=L[-1]
			try:await F.wait_for_load_state(d,timeout=5000);G(f"  New tab/window detected after error, switching to new page: {F.url}");J=C;return A,F,J
			except H:pass
		raise K
	return A,E,J
async def BZ(page,action_list):
	A=page;E=[];F=A.context
	for(O,P)in A4(action_list):
		G('------------------------------------');G('index:',O);G('action:',P)
		try:
			for(C,D)in P.items():
				try:await A.evaluate('() => true')
				except H:
					if F.pages:A=F.pages[-1];await A.wait_for_load_state(Ak);G(f"  Switched to most recent page: {A.url}")
					else:G('  No valid pages found in context');break
				await h(A);G(C,D)
				if C==Au:await BO(D[X],A);E.append({M:C,X:D[X]})
				elif C==t:
					I=D.get(Y,B);J,K,Q=await Af(A,f"xpath={D[T]}",AK,css_selector=I)
					if K!=A:A=K
					E.append({M:C,l:J})
					if Q:R=F.pages.index(A);E.append({M:AN,m:R})
				elif C==A5:await BQ(D[A6]);E.append({M:C,A6:D[A6]})
				elif C==s:
					I=D.get(Y,B);J,K,Q=await Af(A,f"xpath={D[T]}",'fill',D[N],css_selector=I)
					if K!=A:A=K
					E.append({M:C,l:J,N:D[N]})
				elif C==Av:await BP(D[N],A);E.append({M:C,N:D[N]})
				elif C==Aw:await BR(A);E.append({M:C})
				elif C==Ax:await BS(A);E.append({M:C})
				elif C==Ay:await BT(A);E.append({M:C})
				elif C==Az:A=await BU(D[X],A);E.append({M:C,X:D[X]})
				elif C==AN:A=await BV(D[m],A);E.append({M:C,m:D[m]})
				elif C==A_:await BX(D[A7],A);E.append({M:C,A7:D[A7]})
				elif C==u:
					I=D.get(Y,B)
					try:J=await r(A,f"xpath={D[T]}")
					except H as L:
						if I:G(f"  Failed to get selector with xpath, trying CSS: {I}");J=await r(A,f"css={I}")
						else:raise L
					await BY(D[T],D[N],A);E.append({M:C,l:J,N:D[N]})
		except H as L:
			G(f"Error executing action {O}: {V(L)}");G('Skipping to next action...');F=A.context if A3(A,'context')else B
			if F and F.pages:A=F.pages[-1];G(f"  Recovered with page: {A.url}")
			continue
	return E
class Ba:
	def __init__(A,action_list,sensitive_data_keys=B,browser_config=B,context_config=B):A.action_list=action_list;A.sensitive_data_keys=sensitive_data_keys or[];A.browser_config=browser_config;A.context_config=context_config;A._imports_helpers_added=W;A._action_handlers={Au:A._map_go_to_url,A5:A._map_wait,s:A._map_input_text,t:A._map_click_element,'click_element':A._map_click_element,Ax:A._map_scroll_down,Ay:A._map_scroll_up,Av:A._map_scroll_to_text,A_:A._map_send_keys,Aw:A._map_go_back,Az:A._map_open_tab,'close_tab':A._map_close_tab,AN:A._map_switch_tab,u:A._map_select_dropdown_option,'done':A._map_done}
	def _generate_browser_launch_args(A):
		if not A.browser_config:return'headless=False'
		C={'headless':A.browser_config.headless}
		if A.browser_config.proxy:C['proxy']=A.browser_config.proxy.model_dump()
		C={C:A for(C,A)in C.items()if A is not B};return', '.join(f"{A}={repr(B)}"for(A,B)in C.items())
	def _generate_context_options(A):
		if not A.context_config:return D
		E={}
		if A.context_config.user_agent:E['user_agent']=A.context_config.user_agent
		if A.context_config.locale:E['locale']=A.context_config.locale
		if A.context_config.permissions:E['permissions']=A.context_config.permissions
		if A.context_config.geolocation:E['geolocation']=A.context_config.geolocation
		if A.context_config.timezone_id:E['timezone_id']=A.context_config.timezone_id
		if A.context_config.http_credentials:E['http_credentials']=A.context_config.http_credentials
		if A.context_config.is_mobile is not B:E['is_mobile']=A.context_config.is_mobile
		if A.context_config.has_touch is not B:E['has_touch']=A.context_config.has_touch
		if A.context_config.save_recording_path:E['record_video_dir']=A.context_config.save_recording_path
		if A.context_config.save_har_path:E['record_har_path']=A.context_config.save_har_path
		if A.context_config.no_viewport:E['no_viewport']=C
		elif A3(A.context_config,'window_width')and A3(A.context_config,'window_height'):E['viewport']={AL:A.context_config.window_width,AM:A.context_config.window_height}
		E={C:A for(C,A)in E.items()if A is not B};return', '.join(f"{A}={repr(B)}"for(A,B)in E.items())
	def _get_imports_and_helpers(F):E='                ';C='    except Exception:';B='    try:';A='    ';return['import asyncio','import json','import os','import sys','import re','from playwright.async_api import async_playwright, Page, BrowserContext',D,'def get_locator_from_selector(page: Page, selector: str):','    """Gets a Playwright locator based on a selector string."""','    if selector.startswith("role="):','        if "[name=" in selector:','            role_part = selector.split("[")[0].replace("role=", "")','            name_part = selector.split(\'[name="\')[1].split(\'"]\')[0]','            return page.get_by_role(role_part, name=name_part, exact=True).first','        else:','            role_part = selector.replace("role=", "")','            return page.get_by_role(role_part, exact=True).first','    elif selector.startswith("[data-testid="):','        test_id = selector.split(\'="\')[1].split(\'"]\')[0]','        return page.get_by_test_id(test_id).first','    elif selector.startswith("placeholder="):','        placeholder = selector.split(\'="\')[1].split(\'"]\')[0]','        return page.get_by_placeholder(placeholder, exact=True).first','    elif selector.startswith("text="):','        match = re.search(r\'text="([^"]*)"\', selector)','        text_content = match.group(1) if match else None','        return page.get_by_text(text_content, exact=True).first','    elif selector.startswith("label="):','        label = selector.split(\'="\')[1].split(\'"]\')[0]','        return page.get_by_label(label, exact=True).first','    else:','        return page.locator(selector).first',D,'async def wait_for_page_stable(page: Page, timeout: int = 3000):','    """Wait for the page to be stable and ready for interaction."""',B,'        # Wait for the DOM to be loaded','        await page.wait_for_load_state("domcontentloaded", timeout=timeout)','        await asyncio.sleep(1)',C,'        pass',D,'async def click_and_handle_navigation(page: Page, context: BrowserContext, locator):','    """Click an element and handle potential navigation or new tab/window."""','    current_url = page.url','    current_page_count = len(context.pages)',A,'    # Perform the click','    await locator.click()',A,'    # Check if a new page/tab was opened','    if len(context.pages) > current_page_count:','        # New tab/window opened, switch to it','        new_page = context.pages[-1]',"        await new_page.wait_for_load_state('domcontentloaded')",'        print(f"  New tab/window opened, switched to: {new_page.url}")','        return new_page','    elif page.url != current_url:','        # Same tab navigation occurred',"        await page.wait_for_load_state('domcontentloaded')",'        print(f"  Navigated to: {page.url}")',A,'    return page',D,'async def scroll_to_text(page: Page, text: str):','    """Scroll to an element containing the specified text."""',B,'        # Try to find element with exact text match','        element = page.get_by_text(text, exact=False).first','        await element.scroll_into_view_if_needed(timeout=1000)','        print(f"  Successfully scrolled to text: {text}")',C,'        # If exact text not found, try with XPath',B0,'            # Escape quotes in text for XPath','            escaped_text = text.replace("\'", "\\\\\'").replace(\'"\', \'\\\\"\')','            element = page.locator(f"//*[contains(text(), \'{escaped_text}\')]").first','            await element.scroll_into_view_if_needed(timeout=1000)','            print(f"  Successfully scrolled to text (XPath match): {text}")','        except Exception:','            # As fallback, scroll through the page looking for the text','            print(f"  Could not find element with text, scrolling through page...")','            for i in range(10):  # Max 10 scroll attempts','                # Check if text is visible on current viewport',"                is_visible = await page.evaluate('''(text) => {","                    const elements = Array.from(document.querySelectorAll('*'));",'                    return elements.some(el => {','                        const rect = el.getBoundingClientRect();','                        return el.textContent && el.textContent.includes(text) && ','                               rect.top >= 0 && rect.bottom <= window.innerHeight;','                    });',"                }''', text)",E,'                if is_visible:','                    print(f"  Text found in viewport after {i} scrolls")','                    break',E,'                # Scroll down by one viewport height',"                await page.evaluate('window.scrollBy(0, window.innerHeight)')",'                await asyncio.sleep(0.5)',D]
	def _get_sensitive_data_definitions(B):
		if not B.sensitive_data_keys:return['SENSITIVE_DATA = {}',D]
		A=['# Sensitive data placeholders mapped to environment variables'];A.append('SENSITIVE_DATA = {')
		for C in B.sensitive_data_keys:E=C.upper();F=f"YOUR_{E}";A.append(f'    "{C}": os.getenv("{E}", {I.dumps(F)}),')
		A.append('}');A.append(D);return A
	def _get_goto_timeout(A):
		B=90000
		if A.context_config and A.context_config.maximum_wait_page_load_time:return int(A.context_config.maximum_wait_page_load_time*1000)
		return B
	def _map_go_to_url(C,action,step_info_str):
		B=step_info_str;A=action.get(X);D=C._get_goto_timeout()
		if A:E=I.dumps(A);return[f'            print(f"Navigating to: {A} ({B})")',f"            await page.goto({E}, timeout={D})",f"            await wait_for_page_stable(page)"]
		return[f"            # Skipping go_to_url ({B}): missing url"]
	def _map_wait(B,action,step_info_str):A=action.get(A6,3);return[f'            print(f"Waiting for {A} seconds... ({step_info_str})")',f"            await asyncio.sleep({A})"]
	def _map_input_text(G,action,step_info_str):
		C=step_info_str;B=action;A=B.get(l);E=B.get(N,D)
		if A:F=f"{I.dumps(V(E))}";return[f'            print(f"Inputting text into element: {A.replace(c,n).replace(A8,D)} ({C.replace(c,n).replace(A8,D)})")',f"            locator = get_locator_from_selector(page, {I.dumps(A)})",f"            await locator.fill({F})",f"            await wait_for_page_stable(page)"]
		return[f"            # Skipping input_text ({C}): missing selector"]
	def _map_click_element(C,action,step_info_str):
		B=step_info_str;A=action.get(l)
		if A:return[f'            print(f"Clicking element: {A.replace(c,n).replace(A8," ")} ({B.replace(c,n)})")',f"            locator = get_locator_from_selector(page, {I.dumps(A)})",'            page = await click_and_handle_navigation(page, context, locator)',f"            await wait_for_page_stable(page)"]
		return[f"            # Skipping click_element ({B}): missing selector"]
	def _map_scroll_down(A,action,step_info_str):return[f'            print(f"Scrolling down ({step_info_str})")',"            await page.evaluate('window.scrollBy(0, window.innerHeight)')",f"            await wait_for_page_stable(page)"]
	def _map_scroll_up(A,action,step_info_str):return[f'            print(f"Scrolling up ({step_info_str})")',"            await page.evaluate('window.scrollBy(0, -window.innerHeight)')",f"            await wait_for_page_stable(page)"]
	def _map_scroll_to_text(E,action,step_info_str):
		B=step_info_str;A=action.get(N,D)
		if A:C=I.dumps(A);return[f'            print(f"Scrolling to text: {A} ({B})")',f"            await scroll_to_text(page, {C})",f"            await wait_for_page_stable(page)"]
		return[f"            # Skipping scroll_to_text ({B}): missing text"]
	def _map_send_keys(D,action,step_info_str):
		B=step_info_str;A=action.get(A7)
		if A:
			C=['Enter','Tab','Escape','ArrowDown','ArrowUp','ArrowLeft','ArrowRight','Backspace','Delete','Home','End','PageUp','PageDown','Control','Alt','Shift','Meta']
			if A in C:return[f'            print(f"Sending key: {A} ({B})")',f"            await page.keyboard.press({I.dumps(A)})",f"            await wait_for_page_stable(page)"]
			else:return[f'            print(f"Typing text: {A} ({B})")',f"            await page.keyboard.type({I.dumps(A)})",f"            await wait_for_page_stable(page)"]
		return[f"            # Skipping send_keys ({B}): missing keys"]
	def _map_select_dropdown_option(G,action,step_info_str):
		F='\\n';E=step_info_str;C=action;A=C.get(l);B=C.get(N,D)
		if A and B:return[f"            print(f\"Selecting option '{B}' in dropdown: {A.replace(c,n).replace(F,D)} ({E.replace(c,n).replace(F,D)})\")",f"            locator = get_locator_from_selector(page, {I.dumps(A)})",f"            await locator.select_option(label={I.dumps(B)})",f"            await wait_for_page_stable(page)"]
		return[f"            # Skipping select_dropdown_option ({E}): missing selector or text"]
	def _map_go_back(A,action,step_info_str):B=A._get_goto_timeout();return[f'            print(f"Navigating back ({step_info_str})")',f"            await page.go_back(timeout={B})",f"            await wait_for_page_stable(page)"]
	def _map_open_tab(C,action,step_info_str):
		B=step_info_str;A=action.get(X);D=C._get_goto_timeout()
		if A:return[f'            print(f"Opening new tab: {A} ({B})")',B1,f"            await page.goto({I.dumps(A)}, timeout={D})",f"            await wait_for_page_stable(page)"]
		return[f"            # Skipping open_tab ({B}): missing url"]
	def _map_close_tab(B,action,step_info_str):A=action.get(m);return[f'            print(f"Closing tab (Note: page_id {A} is indicative, closing current page) ({step_info_str})")','            await page.close()','            if context.pages: page = context.pages[-1]']
	def _map_switch_tab(D,action,step_info_str):
		C=step_info_str;A=action.get(m)
		if A is not B:return[f'            print(f"Switching to tab index {A} ({C})")',f"            if {A} < len(context.pages):",f"                page = context.pages[{A}]",'                await page.bring_to_front()',f"                await wait_for_page_stable(page)",'            else:',f'                print(f"  Warning: Tab index {A} not found.")']
		return[f"            # Skipping switch_tab ({C}): missing page_id"]
	def _map_done(F,action,step_info_str):A=action;B=A.get(N,D);C=A.get('success',W);E=f"{I.dumps(V(B))}";return[f'            print("\\n--- Task Done ({step_info_str}) ---")',f'            print(f"Success: {C}")',f'            print(f"Final Message: {{ {E} }}")']
	def generate_script_content(A):
		B=[]
		if not A._imports_helpers_added:B.extend(A._get_imports_and_helpers());A._imports_helpers_added=C
		B.extend(A._get_sensitive_data_definitions());J=A._generate_browser_launch_args();K=A._generate_context_options();F='chromium'
		if A.browser_config and A.browser_config.browser_class in['firefox','webkit']:F=A.browser_config.browser_class
		B.extend(['async def run_processed_script():','    global SENSITIVE_DATA','    async with async_playwright() as p:','        browser = None','        context = None','        page = None',B0,f"            print('Launching {F} browser...')",f"            browser = await p.{F}.launch({J})",f"            context = await browser.new_context({K})","            print('Browser context created.')",B1,D,"            print('--- Starting Processed Script Execution ---')"])
		for(G,H)in A4(A.action_list):
			B.append(f"\n            # --- Step {G+1} ---");E=H.get(M);I=A._action_handlers.get(E)
			if I:
				L=f"Step {G+1}, Action: {E}";N=I(H,L);B.extend(N)
				if E=='done':break
			else:B.append(f"            # Unsupported action: {E}")
		B.append(f"\n            print('End of script execution')\n");B.append(f"            await asyncio.sleep(3)");B.extend(['        except Exception as e:',"            print(f'\\n--- An error occurred: {e} ---', file=sys.stderr)",'            import traceback','            traceback.print_exc()','        finally:',"            print('\\n--- Script Execution Finished ---')",'            if browser:','                await browser.close()',"            print('Browser closed.')",D,"if __name__ == '__main__':",'    asyncio.run(run_processed_script())']);return A8.join(B)
def Bb(refined_action_list_path,script_path):
	B=script_path
	try:
		with i(refined_action_list_path,'r')as D:E=I.load(D)
		F=Ba(E);G=F.generate_script_content();os.makedirs(os.path.dirname(os.path.abspath(B)),exist_ok=C)
		with i(B,'w',encoding='utf-8')as D:D.write(G)
		A.info(f"Script generated successfully: {B}");return C
	except H as J:A.error(f"Error generating script: {V(J)}");return W
async def Ag(agent_history_path,output_path):
	C=output_path;B=agent_history_path;F,D=BW(B)
	with i(C,'w')as E:I.dump(D,E,indent=4)
	A.info(f"Parsed agent history from {B} to {C}");return D
async def Ah(parsed_action_list_path,output_path):
	D=output_path;C=parsed_action_list_path
	with i(C,'r')as B:G=I.load(B)
	async with B2()as H:E=await H.chromium.launch(headless=W,args=['--disable-blink-features=AutomationControlled','--disable-features=IsolateOrigins,site-per-process','--disable-site-isolation-trials','--disable-web-security','--disable-features=BlockInsecurePrivateNetworkRequests']);J=await E.new_context(viewport={AL:1280,AM:720});K=await J.new_page();F=await BZ(K,G);await Q.sleep(2);await E.close()
	with i(D,'w')as B:I.dump(F,B,indent=4)
	A.info(f"Refined action list from {C} to {D}");return F
def Ai(refined_action_list_path,output_path):
	C=output_path;B=refined_action_list_path;D=Bb(B,C)
	if D:A.info(f"Generated script from {B} to {C}")
	else:A.error(f"Failed to generate script from {B}")
async def Bc():
	W='pipeline';V='Output path for generated script';U='script.py';T='generate';S='Output path for refined action list';R='refined_action_list.json';Q='refine';P='Output path for parsed action list';O='parsed_action_list.json';N='Path to agent history JSON file';M='parse';I='-o';H='--output';G='-i';F='--input';import argparse as X;E=X.ArgumentParser(description='Browser Automation Script Generator');B=E.add_subparsers(dest='command',help='Command to run');J=B.add_parser(M,help='Parse agent history to action list');J.add_argument(F,G,required=C,help=N);J.add_argument(H,I,default=O,help=P);K=B.add_parser(Q,help='Refine parsed action list');K.add_argument(F,G,required=C,help='Path to parsed action list JSON file');K.add_argument(H,I,default=R,help=S);L=B.add_parser(T,help='Generate script from refined action list');L.add_argument(F,G,required=C,help='Path to refined action list JSON file');L.add_argument(H,I,default=U,help=V);D=B.add_parser(W,help='Run the full pipeline');D.add_argument('--history',required=C,help=N);D.add_argument('--parsed',default=O,help=P);D.add_argument('--refined',default=R,help=S);D.add_argument('--script',default=U,help=V);A=E.parse_args()
	if A.command==M:await Ag(A.input,A.output)
	elif A.command==Q:await Ah(A.input,A.output)
	elif A.command==T:Ai(A.input,A.output)
	elif A.command==W:Y=await Ag(A.history,A.parsed);Z=await Ah(A.parsed,A.refined);Ai(A.refined,A.script)
	else:E.print_help()
if __name__=='__main__':Q.run(Bc())