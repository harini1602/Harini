import pandas as pd
from io import BytesIO
ALIASES = {
 'student_id':['student_id','roll_no','admission_no','student_code'], 'student_name':['student_name','name','learner_name'],
 'class_name':['class','grade','class_name'], 'section':['section'], 'date':['date','attendance_date','exam_date','assessment_date'],
 'status':['status','present','attendance','is_present'], 'subject':['subject','course','paper'], 'marks':['marks','score','marks_obtained'],
 'max_marks':['max_marks','total_marks','out_of'], 'term':['term','exam','assessment','test_name']}

def read_spreadsheet(file):
    name = getattr(file, 'name', 'upload.csv').lower(); data = file.read() if hasattr(file,'read') else file
    if name.endswith('.csv'): return pd.read_csv(BytesIO(data) if isinstance(data, bytes) else file)
    return pd.read_excel(BytesIO(data) if isinstance(data, bytes) else file)

def standardize_columns(df):
    df = df.copy(); lower = {c: str(c).strip().lower() for c in df.columns}; rename={}
    used=set()
    for canon, aliases in ALIASES.items():
        for orig, low in lower.items():
            if low in aliases and orig not in used:
                rename[orig]=canon; used.add(orig); break
    return df.rename(columns=rename), rename

def normalize_attendance(df):
    df,_=standardize_columns(df); df['date']=pd.to_datetime(df['date'], errors='coerce')
    if 'section' not in df: df['section']='A'
    def present(v):
        s=str(v).strip().lower(); return 1 if s in ['1','true','yes','y','present','p'] else 0
    df['is_present']=df.get('is_present', df.get('status')).apply(present)
    return df

def normalize_marks(df):
    df,_=standardize_columns(df); df['date']=pd.to_datetime(df['date'], errors='coerce')
    if 'section' not in df: df['section']='A'
    if 'term' not in df: df['term']=df['date'].dt.strftime('%Y-%m')
    return df
