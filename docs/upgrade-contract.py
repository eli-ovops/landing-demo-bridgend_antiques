from pathlib import Path
import json,hashlib,csv
r=Path('client_bridgend_antiques');p=Path('evidence/demo-workflow-20260905/bridgend-antiques-v1/contract.json');c=json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(r/'docs/before-upgrade/contract.json').write_text(json.dumps(c,indent=2))
a=c['assets'][3];a.update(path='assets/showroom-detail.jpg',originalPath='assets/showroom-detail.jpg',sha256=sha(r/'demo/assets/showroom-detail.jpg'),originalSha256=sha(r/'demo/assets/showroom-detail.jpg'),focus='Entire original2016x1512 scene, original4:3 ratio, unmodified',rights='User local B concept permission; attribution by visual identity with dealer-managed Atlas showroom; final transfer UNKNOWN')
c['sources'].append(dict(id='S10',grade='B',url='https://www.pbs.org/video/paul-laidlaw-and-catherine-southon-day-2-0zauil/',retrievedDate='2026-09-08',platform='PBS episode transcript',attribution='Primary programme transcript explicitly names Ballynure, Bridgend and Hector Thompson; historic appearance not endorsement'))
c['sources'].append(dict(id='S11',grade='B',url='https://c.yell.com/a1953832-61ae-4717-9052-35326532adec_image_jpeg.jpg',retrievedDate='2026-09-08',platform='Yell public merchant gallery',attribution='Exact same scene/composition as first Atlas dealer-managed triptych image, independent reviewer verified identity; larger original CDN image, unmodified'))
a['sourceId']='S11';a['permissionEvidence']='Cross-source visual match to dealer-managed Atlas photo; independent reviewer confirmed local B eligibility.'
for i in c['items']:
 if i['id']=='showroom':i['sourceId']='S11'
 if i['id']=='review-source':i['promise']='Read source seller reviews on Yell'
c['baseline'][8]['sourceIds']=['S11']
source=r/'docs/activation-source.csv'
new=[('buyingdetail','Gold chains rings coins and antiques enquiries','S1','selling'),('preparation','Visitor enquiry preparation not a merchant mandatory workflow','S3','selling'),('adviceproof','AshleyC-5845 05 Aug2026 advice then selected purchase','S1','proof'),('history','Established1994 and dealer range from Atlas','S2','visit'),('programme','PBS Series12Episode2 Ballynure Hector Thompson visit','S10','visit')]
with source.open('a') as f:csv.writer(f).writerows(new)
def add(id,base,s,sel,section,**kw):
 i=dict(id=id,baselineId='BASE'+str(base),sourceId=s,selector=sel,section=section,applicability='YES',disposition='FACT/PARAPHRASE USE',factState='SOURCE CLAIM',mappingStatus='OWNER_CONFIRMED',viewports=['desktop','mobile']);i.update(kw);c['items'].append(i)
add('buyingdetail',14,'S1','#buying-list','selling',text='Chains, rings and gold coins.')
add('preparation',15,'S3','#enquiry-guide','selling',text='What should I have ready?',factState='OBSERVED FACT')
add('adviceproof',16,'S1','#advice-proof','proof',text='Ashley describes receiving helpful valuation advice')
add('history',17,'S2','#dealer-history','visit',text='Established in 1994')
add('historylink',17,'S2','#history-source','visit',href='https://www.antiques-atlas.com/bridgendantiques/',promise='Read merchant history on Antiques Atlas')
add('programme',18,'S10','#programme-fact','visit',text='Paul Laidlaw visited Hector')
add('programmelink',18,'S10','#programme-source','visit',href=c['sources'][-2]['url'],promise='Read public historic episode transcript on PBS, video playback not promised')
lines=source.read_text().splitlines()
for n in range(14,19):
 text=lines[n];bi=[i for i in c['items'] if i['baselineId']=='BASE'+str(n)]
 c['baseline'].append(dict(id='BASE'+str(n),file=str(source.resolve()),line=n+1,excerpt=text,excerptSha256=hashlib.sha256(text.encode()).hexdigest(),disposition='MAPPED',itemIds=[i['id'] for i in bi],sourceIds=list(dict.fromkeys(i['sourceId'] for i in bi)),reason='Additional verified source mapped to visible content or actionable visitor guidance without inventing merchant policy.'))
c['sourceFiles'][0]['sha256']=sha(source);c['currentEvidence']='User 9-point refinement request; additional public Yell/PBS/Atlas research2026-09-08; same activev1'
p.write_text(json.dumps(c,indent=2))
l=json.loads((r/'docs/ASSET_LEDGER.json').read_text());l[3].update(path=a['path'],sha256=a['sha256'],source=c['sources'][-1]['url'],treatment='Unmodified public2016x1512 original, replaces low-resolution triptych; CSS original aspect ratio',attribution=c['sources'][-1]['attribution']);(r/'docs/ASSET_LEDGER.json').write_text(json.dumps(l,indent=2))
with (r/'docs/ASSET_INVENTORY.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=l[0].keys());w.writeheader();w.writerows(l)
print('Contract27items/18baseline with updated actual shop source')
