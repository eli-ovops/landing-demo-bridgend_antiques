from pathlib import Path
import json
job=Path('evidence/demo-workflow-20260905/bridgend-antiques-v1/contract.json')
c=json.loads(job.read_text()); ledger=json.loads(Path('client_bridgend_antiques/docs/ASSET_LEDGER.json').read_text())
urls={'S1':'https://www.yell.com/biz/bridgend-antiques-ballyclare-6999917/','S2':'https://www.antiques-atlas.com/bridgendantiques/','S3':'https://www.antiques-atlas.com/bridgendantiques/contact.php','S4':'https://www.antiques-atlas.com/sites/bridgendantiques/images/bridgendantiques.jpg','S6':'https://www.youtube.com/shorts/iet95Lq8_NQ','S9':'local-original://imagegen/bridgend-antiques-20260908'}
c['sources']=[dict(id=k,url=u,grade='C' if k=='S9' else 'B',retrievedDate='2026-09-08',platform='Built-in image generation' if k=='S9' else 'Public merchant listing / public visitor review',attribution='Original category artwork generated for this local concept' if k=='S9' else 'Merchant-specific listing; review claims attributed to reviewer; image dealer-managed hosted shop') for k,u in urls.items()]
c['assets']=[]
for idx,a in enumerate(ledger):
 c['assets'].append(dict(id='AS'+str(idx+1),path=a['path'],originalPath=a['path'],sha256=a['sha256'],originalSha256=a['sha256'],sourceId='S4' if a['authenticity']=='REAL' else 'S9',role=a['role'],focus='Whole subject visible; contain or original aspect ratio; no factual edit',authenticity=a['authenticity'],rights='Local independent concept; final transfer not established',permissionEvidence='User local concept authorisation; tool original generated art' if a['authenticity']=='CONCEPT' else 'User B dealer-attributable concept allowance; source is dealer-managed Atlas shop'))
items=[]
def item(id,base,source,selector,section,**kw):
 i=dict(id=id,baselineId='BASE'+str(base),sourceId=source,selector=selector,section=section,applicability='YES',disposition='FACT/PARAPHRASE USE',factState='SOURCE CLAIM',mappingStatus='OWNER_CONFIRMED',viewports=['desktop','mobile']);i.update(kw);items.append(i)
item('identity',1,'S2','.brand','header',text='Bridgend Antiques')
item('selling',2,'S1','#hero-intro','hero',text='antiques, gold and silver')
item('silver',2,'S1','#selling-title','selling',text='Gold, silver & antiques')
item('mobile',3,'S3','#hero-call','hero',href='tel:+447966751699',promise='Call Hector by mobile')
item('mobile-bottom',3,'S3','#mobile','visit',href='tel:+447966751699',promise='Call public business mobile')
item('landline',4,'S3','#landline','visit',href='tel:+442893341979',promise='Call shop public landline')
item('email',5,'S3','#email','visit',href='mailto:[REDACTED_EMAIL]',promise='Open email application to public business address')
item('address',6,'S3','#address','visit',text='50 Church Road')
item('directions',6,'S3','#directions','visit',href='https://www.google.com/maps/search/?api=1&query=Bridgend+Antiques+50+Church+Road+Ballynure+BT39+9UF',promise='Search the verified business address on Google Maps')
item('review',7,'S1','#review-quote','proof',text='Paid us on the spot without any quibble.')
item('review-source',7,'S1','#review-source','proof',href=urls['S1'],promise='Read publicly attributed silver seller review on Yell')
item('catalogue',8,'S2','#catalogue-link','catalogue',href=urls['S2'],promise='Browse current catalogue on Antiques Atlas')
item('contact-form',8,'S3','#atlas-contact','visit',href=urls['S3'],promise='Open existing external Atlas contact page')
item('showroom',9,'S4','#showroom-photo','visit',assetId='AS4',disposition='DIRECT USE',factState='OBSERVED FACT')
for n,(selector,section) in enumerate([('#hero-art','hero'),('#silver-art','selling'),('#objects-art','catalogue')]):
 item('concept-'+str(n+1),10,'S9',selector,section,assetId='AS'+str(n+1),disposition='CONCEPT VISUAL REPLACEMENT',factState='OBSERVED FACT')
item('hours',11,'S3','#visit-note','visit',text='Please telephone before travelling',disposition='TIME-SENSITIVE VERIFY/REPHRASE')
for base,s,reason in [(12,'S6','Private video unavailable to anonymous visitors; no playable source or usable thumbnail.'),(13,'S2','No verified usable official logo, portrait, social account or credentials; no invented replacements.')]:
 item('excluded-'+str(base),base,s,'','excluded',applicability='NO',disposition='EXCLUDE',reason=reason)
c['items']=items
for b in c['baseline']:
 bi=[i for i in items if i['baselineId']==b['id']];b.update(disposition='MAPPED',itemIds=[i['id'] for i in bi],sourceIds=list(dict.fromkeys(i['sourceId'] for i in bi)),reason='Source fact consolidated into related visible actions or specifically excluded unavailable material.')
c['coverageReview']='OWNER_RECONCILED';c['hero']={'selector':'#hero','ctaSelector':'#hero-call'};c['sections']=['#hero','#selling','#proof','#catalogue','#visit']
job.write_text(json.dumps(c,indent=2))
print('Planned contract populated; confirm against implemented DOM before run')
