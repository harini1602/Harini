import numpy as np, pandas as pd
from datetime import date, timedelta

def generate_demo_data(n_students=72, seed=7):
    rng=np.random.default_rng(seed); subjects=['Maths','Science','English','Social Studies','Hindi']; terms=['Term 1','Term 2','Term 3']
    students=[{'student_id':f'S{1000+i}','student_name':f'Learner {i+1}','class_name':str(6+i%3),'section':chr(65+i%3)} for i in range(n_students)]
    days=[date.today()-timedelta(days=i) for i in range(59,-1,-1) if (date.today()-timedelta(days=i)).weekday()<5]
    ar=[]; mr=[]
    for idx,s in enumerate(students):
        pattern=idx%12; base=.94 if pattern not in [0,1,2] else (.62 if pattern==0 else .78)
        for j,d in enumerate(days):
            p=base-(.25*j/len(days) if pattern in [1,3] else 0)
            if pattern==0 and j>len(days)-8: present=False
            else: present=rng.random()<p
            status='Present' if present else ('Unexplained Absence' if rng.random()<.35 else 'Absent')
            ar.append({**s,'date':d.isoformat(),'status':status})
        for ti,t in enumerate(terms):
            for sub in subjects:
                if pattern in [2,4] and ti==2 and sub in ['Maths','Science'] and rng.random()<.5: continue
                mean=76-(25 if pattern in [0,2] else 0)-(18*ti if pattern in [3,4] else 0)-(12 if sub=='Maths' and pattern in [1,2,3] else 0)
                score=float(np.clip(rng.normal(mean,10), 15, 98))
                mr.append({**s,'date':(date.today()-timedelta(days=(3-ti)*24)).isoformat(),'subject':sub,'marks':score,'max_marks':100,'term':t})
    return pd.DataFrame(ar), pd.DataFrame(mr)

def write_demo_files(path='data'):
    import os
    os.makedirs(path, exist_ok=True); a,m=generate_demo_data(); a.to_csv(f'{path}/demo_attendance.csv', index=False); m.to_csv(f'{path}/demo_marks.csv', index=False)
