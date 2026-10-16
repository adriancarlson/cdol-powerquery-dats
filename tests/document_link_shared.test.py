import sqlite3,re,xml.etree.ElementTree as ET
from pathlib import Path
c=sqlite3.connect(':memory:')
c.create_function('NVL',2,lambda a,b:b if a is None else a)
c.create_function('TO_CLOB',1,lambda x:'' if x is None else str(x))
c.create_function('TRIM',1,lambda x:None if x is None else str(x).strip() or None)
c.create_function('CHR',1,chr)
c.create_function('TO_CHAR',1,lambda x:None if x is None else str(x))
c.create_function('REGEXP_REPLACE',3,lambda s,p,r:None if s is None else re.sub(r'\s',r,s))
c.create_function('REGEXP_INSTR',2,lambda s,p:0 if s is None or not re.search(r'\s',s) else re.search(r'\s',s).start()+1)
c.executescript("""CREATE TABLE Students(DCID INTEGER,GRADE_LEVEL INTEGER); CREATE TABLE U_STUDENT_ENROLLMENT_LOGIC(StudentsDCID INTEGER,PSEE_SCHOOL_ID INTEGER,PSEE_GRADE_LEVEL INTEGER); CREATE TABLE Schools(DCID INTEGER,School_Number INTEGER); CREATE TABLE U_SCHOOL_ENROLL_DOCUMENTS(ID INTEGER,SchoolsDCID INTEGER,DOCUMENT_TYPE TEXT,DOCUMENT_NAME TEXT,DOCUMENT_URL TEXT,FILTER_FIELD TEXT,FILTER_VALUE TEXT,DOCUMENT_LANGUAGE TEXT); INSERT INTO Students VALUES(1,3); INSERT INTO U_STUDENT_ENROLLMENT_LOGIC VALUES(1,108,4); INSERT INTO Schools VALUES(165,108),(113,107),(253,79438);""")
queries=ET.parse('queries_root/cdolPowerQueryDats.permission_mappings.xml.named_queries.xml').getroot()
sql=next(q for q in queries if q.attrib['name'].endswith('psee.document_link')).find('sql').text
# Execute the actual query with SQLite compatibility functions; this is not Oracle validation.
def doc(owner=165,language='en',grade='4',name='Local English',url=None,field='u_student_enrollment_logic.psee_grade_level',doctype='handbook'):
 return (owner,doctype,name,url or 'https://example.org/'+str(owner)+'/'+str(language)+'?a=1&b=2',field,grade,language)
def run(rows):
 c.execute('DELETE FROM U_SCHOOL_ENROLL_DOCUMENTS')
 for i,row in enumerate(rows,1):c.execute('INSERT INTO U_SCHOOL_ENROLL_DOCUMENTS VALUES(?,?,?,?,?,?,?,?)',(i,)+row)
 return c.execute(sql,{'coretabledcid':1,'document_type':'handbook'}).fetchone()[0]
shared=doc(253,name='Shared English'); local=doc()
es=doc(253,'es',name='Shared Spanish'); vi=doc(253,'vi',name='Shared Vietnamese')
assert 'Shared English</a>' in run([shared])
assert 'Local English</a>' in run([local,shared]) and 'Shared English' not in run([local,shared])
assert 'Shared English' in run([doc(grade='-1'),shared])
assert 'Shared English' in run([doc(grade='14'),shared])
x=run([shared,es,vi]); assert '(<' in x and 'Shared Spanish</a>)' in x and 'Shared Vietnamese</a>)' in x
x=run([local,shared,es,vi]); assert 'Shared Spanish' not in x and 'Shared Vietnamese' not in x and 'Local English' in x
x=run([local,doc(language='vi',name='Local Vietnamese'),shared,es]); assert 'Local Vietnamese</a>)' in x and 'Shared Spanish' not in x
x=run([shared,es,doc(language='es',name='Local Spanish')]); assert 'Shared Spanish' in x and 'Local Spanish' not in x
assert 'Multiple documents' in run([local,local,shared])
assert 'Multiple documents' in run([shared,shared])
assert 'Local English' in run([local,shared,shared])
assert 'Multiple documents' in run([shared,es,es])
assert 'unavailable' in run([local,doc(language='es',url='javascript:alert(1)')])
assert 'unavailable' in run([doc(url='javascript:alert(1)'),shared])
assert 'unavailable' in run([es])
assert 'unavailable' in run([doc(113,name='Other School')])
assert 'Shared English' in run([doc(253,language=None,name='Shared English')])
assert 'Shared English' in run([doc(253,language='  ',name='Shared English',url='https://example.org/blank-language')])
assert 'Shared English' in run([doc(253,grade=None,field=None,name='Shared English')])
assert 'unavailable' in run([doc(253,field='unknown')])
x=run([shared,doc(253,'es',name='Espa&amp; \"<test>')]); assert '&amp;amp;' in x and '&quot;' in x and '&lt;test&gt;' in x
assert 'a=1&amp;b=2' in run([shared])
assert '(' not in run([shared])
assert 'unavailable' in run([doc(253,doctype='apu')])
assert 'COUNT(*)' not in sql and 'SELECT *' not in sql
print('24 shared fallback, override, translation-source, grade, duplicate, invalid URL and escaping cases passed against the actual query using local compatibility functions.')
