import pandas as pd
ATTENDANCE_REQUIRED={'student_id','student_name','class_name','date','status'}
MARKS_REQUIRED={'student_id','student_name','class_name','date','subject','marks','max_marks'}

def validate_attendance(df):
    errors=[]; warnings=[]
    miss=ATTENDANCE_REQUIRED-set(df.columns)
    if miss: errors.append(f"Missing attendance columns after mapping: {', '.join(sorted(miss))}")
    if 'date' in df and pd.to_datetime(df['date'], errors='coerce').isna().any(): errors.append('Attendance contains impossible dates.')
    if {'student_id','date'}.issubset(df.columns) and df.duplicated(['student_id','date']).any(): warnings.append('Duplicate attendance records may distort scoring; latest uploaded batch is retained for review.')
    if len(df) < 30: warnings.append('Sparse attendance history limits confidence.')
    return errors,warnings

def validate_marks(df):
    errors=[]; warnings=[]
    miss=MARKS_REQUIRED-set(df.columns)
    if miss: errors.append(f"Missing marks columns after mapping: {', '.join(sorted(miss))}")
    if 'date' in df and pd.to_datetime(df['date'], errors='coerce').isna().any(): errors.append('Marks contains impossible dates.')
    if {'marks','max_marks'}.issubset(df.columns):
        bad=((df['marks']<0)|(df['max_marks']<=0)|(df['marks']>df['max_marks'])).any()
        if bad: errors.append('Marks must be between 0 and maximum marks; maximum marks must be positive.')
    if {'student_id','date','subject','term'}.issubset(df.columns) and df.duplicated(['student_id','date','subject','term']).any(): warnings.append('Duplicate mark records detected.')
    return errors,warnings

def cross_file_warnings(att, marks):
    a=set(att.get('student_id', [])); m=set(marks.get('student_id', [])); w=[]
    if a-m: w.append(f"{len(a-m)} students appear in attendance but not marks.")
    if m-a: w.append(f"{len(m-a)} students appear in marks but not attendance.")
    return w
