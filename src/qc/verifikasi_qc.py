import pandas as pd,numpy as np, pathlib,hashlib,json
from scipy.io import wavfile
from scipy.signal import welch
import sys
p=pathlib.Path(sys.argv[1]); l=pd.read_csv(p/'label.csv'); a=pd.read_csv(p/'audio_index.csv'); print(l.groupby(['kipas','pompa','buzzer','lampu']).size().to_string()); print('unique',l.no.nunique(),l.groupby(['kipas','pompa','buzzer','lampu','ulangan']).size().value_counts()); print('hash',hashlib.sha256((p/'label.csv').read_bytes()).hexdigest()); m=json.loads((p/'manifest.json').read_text()); print('manifest mismatch',[k for k,v in m['berkas'].items() if not (p/k).exists() or hashlib.sha256((p/k).read_bytes()).hexdigest()!=v['sha256']]); h=hashlib.sha256(); names=['data/'+n+'.csv' for n in ['label','imu','daya','aktuator','audio_index','lingkungan','digital']];
for n in sorted(names): h.update(n.encode()); h.update((p/pathlib.Path(n).name).read_bytes())
print('hash raw',h.hexdigest()[:32]);h.update(b'split:2026');print('hash split',h.hexdigest()[:32]);
base=a.t_mulai_host.iloc[0]; fs=16000; starts=np.rint((a.t_mulai_host-base)*fs).astype(int); x=np.zeros(int(starts.iloc[-1]+a.jumlah_sampel.iloc[-1]),np.float32); cover=np.zeros(len(x),bool); bad=[]
for i,r in a.iterrows():
 rate,y=wavfile.read(p/'audio'/r.berkas); s=starts.iloc[i];
 if rate!=fs or y.ndim!=1 or len(y)!=r.jumlah_sampel: bad.append(r.berkas)
 x[s:s+len(y)]=y.astype(np.float32)/32768;cover[s:s+len(y)]=True
print('wav',len(a),bad)
rows=[]
for r in l.itertuples():
 s=round((r.t_mulai_host+1-base)*fs); e=round((r.t_selesai_host-base)*fs); y=x[s:e]; c=cover[s:e]; f,pow=welch(y,fs=fs,nperseg=2048); band=(f>=500)&(f<=1500); rows.append([r.no, int((~c).sum()),float(np.sqrt(np.mean(y*y))),10*np.log10(np.sum(pow[band])*(f[1]-f[0])+1e-20),float(np.mean(np.abs(y)>=.999))])
q=pd.DataFrame(rows,columns=['no','missing_samples','rms','band_db','clip_fraction']); d=l.merge(q); pairs=d.pivot(index=['kipas','buzzer','lampu','ulangan'],columns='pompa',values='band_db'); delta=pairs[200]-pairs[0]; print('qc',q.describe().to_string()); print('pairs',len(delta),sum(delta>0),delta.mean(),delta.median()); print('isolated',delta.loc[(0,0)].describe(),sum(delta.loc[(0,0)]>0)); print('isolated IDs',d[(d.kipas==0)&(d.buzzer==0)][['no','pompa','lampu','ulangan','band_db']].to_string(index=False)); print('duration', (l.t_selesai_host-l.t_mulai_host).describe()); print('channels',pd.read_csv(p/'daya.csv',usecols=['kanal']).kanal.value_counts());

out=pathlib.Path(sys.argv[2]) if len(sys.argv)>2 else pathlib.Path("."); out.mkdir(parents=True,exist_ok=True)
d.to_csv(out/"qc_kondisi.csv",index=False)
pair=d.pivot(index=["kipas","buzzer","lampu","ulangan"],columns="pompa",values=["no","band_db"]); pair.columns=[f"{a}_{b}" for a,b in pair.columns]; pair["delta_db"]=pair.band_db_200-pair.band_db_0; pair.reset_index().to_csv(out/"qc_pasangan_pompa.csv",index=False)
l.groupby(["kipas","pompa","buzzer","lampu"]).size().rename("jumlah").reset_index().to_csv(out/"qc_kombinasi.csv",index=False)
