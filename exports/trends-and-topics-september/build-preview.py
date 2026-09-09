from pathlib import Path
import re,html
root=Path('/Users/christopherjames/Code/2n/2n-brain'); out=root/'exports/trends-and-topics-september'
s=(root/'.agents/skills/generate-trends-topics/templates/trends-and-topics-template.html').read_text()
parts=re.split(r'(<!-- ================= .*? ================= -->)',s)
z={parts[i]:parts[i+1] for i in range(1,len(parts),2)}
keys=list(z)
def key(t): return next(k for k in keys if t in k)
def pretty(t):
 a=t.rsplit(' ',1);return '&nbsp;'.join(a) if len(a)==2 else t
sans="font-family:'Inter',Arial,Helvetica,sans-serif;"
serif="font-family:'Instrument Serif',Georgia,'Times New Roman',serif;"
def p(t):return f'<p style="margin:0 0 14px;{sans}font-size:14.5px;line-height:1.65;color:#3A4360;">{pretty(t)}</p>'
def h(t):return f'<div style="{serif}font-size:26px;line-height:1.15;color:#0A1A3A;margin:0 0 14px;">{pretty(t)}</div>'
def cta(t,u):return f'<a href="{u}" style="display:inline-block;{sans}font-size:11px;letter-spacing:2.2px;text-transform:uppercase;color:#0A1A3A;border:1px solid #0A1A3A;padding:10px 18px;font-weight:600;">{t} →</a>'
def table(t):return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'+t+'</table>'
def card(t,body):
 if "<a " not in body: body=re.sub(r'(margin:)0 0 14px;([^>]*>.*?</p>)$', r'\g<1>0;\2', body, flags=re.S)
 return table(f'<tr><td style="border:1px solid #E0D8C5;padding:18px 20px;">'+f'<div style="{serif}font-size:19px;color:#0A1A3A;margin:0 0 10px;">{pretty(t)}</div>'+body+'</td></tr>')+'<div style="height:12px;line-height:12px;">&nbsp;</div>'
def body(t,content):
 k=key(t); old=z[k]; end=old.index('</tr></table>')+len('</tr></table>');z[k]=old[:end]+content+'\n</td></tr></table>\n'
def roster(rows):
 return table(''.join(f'<tr><td style="padding:10px 0;{serif}font-size:16px;color:#0A1A3A;'+('border-bottom:1px dotted #D0C7B0;' if i<len(rows)-1 else '')+f'">{n}</td><td align="right" style="padding:10px 0;{"border-bottom:1px dotted #D0C7B0;" if i<len(rows)-1 else ""}{sans}font-size:11px;letter-spacing:0.5px;color:#B8870A;">{c}</td></tr>' for i,(n,c) in enumerate(rows))) + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td height="18" style="height:18px;font-size:0;line-height:18px;">&nbsp;</td></tr></table>'

# Letter retains its stat table and drop cap styles.
k=key('LETTER'); v=z[k]; ps=list(re.finditer(r'<p\b[^>]*>.*?</p>',v,re.S))
texts=["August was another strong month for the 2^n community. We welcomed eleven family offices, added new Deal Partners, and reached a milestone with the first job posting live in Talent.","None of that happens on its own. It happens because members make introductions, share what they are seeing, and show up for one another. Thank you for that. It is the whole thesis of this community, and you keep proving it out.","On October 5, we are releasing features members have asked for since day one. Signal, Events, Messaging, and Radar all serve the same purpose: the more connected this network becomes, the more each of you gets out of it.","Here’s what moved across the community, and what to have on your radar this September."]
for i,m in reversed(list(enumerate(ps))):
 t=texts[i]; inner=pretty(t)
 if i==0: inner=re.search(r'<span.*?</span>',m[0],re.S)[0].replace('>T<','>A<')+pretty(t[1:])
 v=v[:m.start()]+re.match(r'<p[^>]*>',m[0])[0]+inner+'</p>'+v[m.end():]
v=v.replace('>134<','>11<').replace('>Family Offices<','>New Family Offices<').replace('>9<','>1<').replace('>New in May<','>New Country<').replace('>Wk to Summit<','>First Job Posted<')
v=v.replace('</td></tr>\n              </table>',p('This edition follows Labor Day. Future briefs return to the first Wednesday of each month.')+'</td></tr>\n              </table>');z[k]=v
rows=[('Brodie Generational Capital Partners','Wayne, PA'),('Three Step Legacy, Inc.','Virginia Beach, VA'),('Simon Group Holdings','Birmingham, MI'),('VentureOn Management','Chicago, IL'),('Agave Holdings','Miami, FL'),('Terramar','Brazil'),('TopRidge Investment','Boston, MA'),('Robin Companies','Chicago, IL'),('Jefferson River Capital','New York, NY'),('Ashby Management Company','Austin, TX'),('Berggruen Holdings','Los Angeles, CA')]
body('I · MEMBER',h('Eleven family offices to welcome.')+p('Our latest member introductions span the United States and Brazil. Welcome to the community.')+roster(rows)+cta('View Member Profiles','https://www.2pwrn.com/dashboard/directory'))
body('II · DEAL',h('Welcome our newest Deal Partners.')+roster([('Sentinel Global','San Francisco, CA'),('Ridge Real Estate Partners','New York, NY'),('Amalgam Rx','Wilmington, DE')])+cta('Meet the Deal Partners','https://www.2pwrn.com/dashboard/directory?tab=sponsors'))
k=key('III · DEAL');v=z[k];start=v.index('<table role="presentation" width="100%"',v.index('Recent on the'));end=v.index('</table>',start)+8
row=re.search(r'<tr>\s*<td width="32".*?</tr>',v[start:end],re.S)[0]; rr=[]
for i,(name,id,typ) in enumerate([('Henley Investments · AquaSonic Car Wash',42,'Deal Partner'),('Distressed 2016 MF Acquisition',43,'Deal Partner'),('Project Catalyst · Data Center',45,'Family Office'),('Project Capstone · Data Center',44,'Family Office')]):
 r=row.replace('>01<',f'>{i+1:02d}<').replace('SK Slovan Bratislava',name).replace('Football Club','Real Estate · '+typ).replace('dealId=35',f'dealId={id}')
 if i==3:r=r.replace('border-bottom:1px dotted #D0C7B0;','')
 rr.append(r)
z[k]=v[:start]+table(''.join(rr))+v[end:]
body('IV ·',h('Three conversations worth watching.')+p('Go behind the scenes with Deal Partners to explore the experiences, relationships, and investment philosophies shaping their firms.')+card('Henley Investment Management',p('Ian and Charlie Rickwood discuss Henley’s real estate strategies across Europe and the U.S., their car wash focus, and the long-term family office relationships behind the business.'))+card('Starting Line',p('Ezra Galston, Haley, and Scott discuss their venture fund’s approach to cultural shifts, Midwestern connections, and the Chicago ecosystem.'))+card('Ridge Real Estate Partners',p('Founder Michael Gershenson shares his experience in real estate investing, the firm’s focus on growth markets, and its alignment with family office investors.'))+cta('Watch the Spotlights','https://www.2pwrn.com/dashboard/2n-tv'))
v=h('Where we’ll be.')+card('Sherman Oaks · September 16, 2026',p('Join us at the private residence of a fellow 2^n member for an evening of conversation and new connections in a more personal setting.')+cta('View Sherman Oaks','https://www.2pwrn.com/dashboard/events/12'))+card('Chicago · October 6, 2026',cta('View Chicago','https://www.2pwrn.com/dashboard/events/13'))+card('New York · November 3, 2026',cta('View New York','https://www.2pwrn.com/dashboard/events/14'))
v+=h('Help grow the Talent Vault.').replace('margin:0 0 14px;', 'margin:20px 0 14px;')+p('Our first opportunity is live. Thank you, Emigrant Capital. Posting a role is complimentary while we build out the Talent Vault. Your opening goes only to this community.')+cta('Post or Browse a Role','https://www.2pwrn.com/dashboard/talent')+'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td height="20" style="height:20px;font-size:0;line-height:20px;">&nbsp;</td></tr></table>'+p('Know someone exceptional who wants to be in this world? Send them to the talent application.')+cta('Refer to the Talent Vault','https://www.2pwrn.com/talent')
v+=h('Coming October 5.').replace('margin:0 0 14px;', 'margin:32px 0 14px;')
for t,b in [('Signal: Your Personal Homepage','A daily brief built around you, highlighting strong matches and relevant articles and research. Customize what shows up, post updates, run polls, and reach the 2^n team through the “Ring the Concierge” feature. Add travel cities and dates to discover who to meet.'),('Events','Suggest or host in-person events and see which members are attending. Group chat before you go, rate the event afterward, or host a virtual gathering for up to 24 members.'),('Messaging','Connect through direct messages, group chats for a deal or event, and public channels organized around the topics the community follows.'),('Radar','Your 2^n AI Assistant will help with research and introductions. Ask what the network is discussing or find a member who has already evaluated what you are considering.')]:v+=card(t,p(b))
v+=p('Want a preview before launch? Reach out to Sydney or Matt.');body('V · INSIDE',v)
s=parts[0]+''.join(k+z[k] for k in keys)
s=s.replace('Volume VI','Volume IX').replace('June 2026','September 2026').replace('heading into June','heading into September').replace('What moved in May','What moved in August')
s=re.sub(r'<title>.*?</title>','<title>2^n Family Office Brief: September 2026 (v1)</title>',s)
s=s.replace('—',';')
logo='<img src="https://content.app-us1.com/MZZPE9/2025/11/27/70fbf0f9-a1c1-4c5c-86a2-1a76e1732cf9.png" width="25" height="25" alt="2^n" style="width:25px;height:25px;vertical-align:-7px;">'
s=s.replace('>2^n Intelligence<','>'+logo+' Intelligence<').replace('>Inside 2^n<','>Inside '+logo+'<')
# Center the masthead metadata on two intentional lines at every width.
s=re.sub(r'<td valign="middle" class="vol" style="([^"]*)">.*?</td>', lambda m: '<td valign="middle" align="center" class="vol" style="'+m[1]+'text-align:center;line-height:1.5;">'+'Family Office Brief<br><span style="display:inline-block;margin-top:5px;">Volume IX <span style="color:#B8870A;">&#9670;</span> September 2026</span>'+ '</td>', s, flags=re.S)

# Approved September editorial tightening.
for old,new in {'Eleven family offices to&nbsp;welcome.': 'Meet our newest family&nbsp;offices.', 'Recent on the&nbsp;Marketplace.': 'New in the Deal&nbsp;Marketplace.', 'It is the whole thesis of this community': 'That’s what makes this community work', 'First Job Posted': 'First Talent Posting'}.items(): s=s.replace(old,new)
s=re.sub(r'<p[^>]*>This edition follows Labor Day\..*?</p>', '', s, flags=re.S)
s=re.sub('<p[^>]*>Deals are the catalyst\\..*?</p>\\s*<p[^>]*>It\\x27s also how.*?</p>\\s*<p[^>]*>Use the .*?</p>', lambda m: re.match(r'<p[^>]*>',m[0])[0]+'A shared deal gives members a reason to connect, compare diligence, and build a relationship. Explore these opportunities, ask a question, or share a co-investment with the&nbsp;community.'+'</p>', s, flags=re.S)
s=re.sub('(<div style="[^">]*">)1(</div>\\s*<div style="[^">]*">)First Talent Posting(</div>)', '\\g<1>1st\\2Talent Posting\\3', s)
s=s.replace('>1st</div>', '>1<sup style="font-size:16px;line-height:0;vertical-align:super;">st</sup></div>')
s=re.sub('<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0">\\s*<tr>.*?</table>', lambda m: '<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0">\n<tr><td align="center" class="vol" style="font-family:\'Inter\',Arial,Helvetica,sans-serif;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#6B6657;text-align:center;line-height:1.5;">Family Office Brief</td></tr>\n<tr><td align="center" style="padding:7px 0;"><table role="presentation" width="80" align="center" cellpadding="0" cellspacing="0" border="0"><tr><td style="border-top:1px solid #B8870A;font-size:0;line-height:0;height:0;">&nbsp;</td></tr></table></td></tr>\n<tr><td align="center" class="vol" style="font-family:\'Inter\',Arial,Helvetica,sans-serif;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#6B6657;text-align:center;line-height:1.5;">Volume IX <span style="color:#B8870A;">&#9670;</span> September 2026</td></tr>\n</table>', s, count=1, flags=re.S)
# Gold dates in all three event headings.
for city,date in [('Sherman Oaks','September 16, 2026'),('Chicago','October 6, 2026'),('New York','November 3, 2026')]:
 old=city+' · '+pretty(date)
 assert s.count(old)==1
 s=s.replace(old,city+' · <span style="color:#B8870A;">'+pretty(date)+'</span>')
(out/'trends-and-topics-september-v1.html').write_text(s)
print(len(s.encode()),'bytes')
