# Graph: 197 nodes / 456 rels

## count_nodes
```cypher
MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC;
```
```
label=Clause | n=99
label=Person | n=34
label=Article | n=18
label=Case | n=14
label=Crime | n=13
label=Substance | n=12
label=Location | n=7
```

## count_rels
```cypher
MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS n ORDER BY n DESC;
```
```
rel=THRESHOLD | n=243
rel=HAS_CLAUSE | n=99
rel=INVOLVED_IN | n=42
rel=CHARGED_WITH | n=20
rel=INVOLVES | n=18
rel=LOCATED_IN | n=14
rel=DEFINES | n=13
rel=MENTIONS | n=7
```

## E1_case_without_crime
```cypher
MATCH (k:Case) WHERE NOT (k)-[:CHARGED_WITH]->() RETURN k.name AS case, k.doc_id AS doc_id ORDER BY doc_id;
```
```
case=Vụ tông cảnh sát giao thông ở An Giang | doc_id=news-100260926112415229
```

## E1_cases_per_doc
```cypher
MATCH (k:Case) RETURN k.doc_id AS doc_id, collect(k.name) AS cases ORDER BY doc_id;
```
```
doc_id=news-100260917203001265 | cases=['Vụ vận chuyển ma túy từ Đức về Việt Nam']
doc_id=news-100260918080821054 | cases=['Vụ góp tiền mua ma túy tại Hà Nội']
doc_id=news-100260920221957595 | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy"]
doc_id=news-100260922111804786 | cases=["Vụ bắt giữ TikToker Phannhibeauty và giang hồ 'Hoàng Nato'"]
doc_id=news-100260924095400982 | cases=['Vụ sử dụng ma túy etomidate của Hoàng Nato và Phan Kim Nhi']
doc_id=news-100260924101703641 | cases=["Vụ bắt giữ giang hồ mạng 'Đức Cộng'"]
doc_id=news-100260924105118645 | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương']
doc_id=news-100260924145818945 | cases=['Vụ vận chuyển 840kg ma túy đá tại Campuchia']
doc_id=news-100260925144412498 | cases=['Vụ triệt phá 8 đường dây ma túy tại TP.HCM']
doc_id=news-100260926112415229 | cases=['Vụ tông cảnh sát giao thông ở An Giang']
doc_id=news-100260927182621527 | cases=['Vụ phát hiện 20kg ma túy tại Phú Quốc']
doc_id=news-100260928173914514 | cases=['Vụ mua bán hơn 36kg ma túy tại TP.HCM']
doc_id=news-100260930085028036 | cases=['Vụ tổ chức sử dụng ma túy tại Sầm Sơn']
doc_id=news-100261002184934505 | cases=['Chuyên án A3-626P']
```

## E2_hoang_nato
```cypher
MATCH (p:Person)-[r:INVOLVED_IN]->(k:Case) WHERE p.name CONTAINS 'Tuấn' OR any(a IN p.aliases WHERE a CONTAINS 'Nato') OPTIONAL MATCH (k)-[:INVOLVES]->(s:Substance) OPTIONAL MATCH (k)-[:CHARGED_WITH]->(c:Crime) RETURN p.name AS person, p.aliases AS aliases, r.charge AS charge, k.name AS case, collect(DISTINCT s.name) AS substances, collect(DISTINCT c.name) AS crimes;
```
```
person=Kim Xuân Tuấn | aliases=[] | charge=mua bán trái phép chất ma túy | case=Vụ góp tiền mua ma túy tại Hà Nội | substances=['Ketamine', 'MDMA'] | crimes=['mua bán trái phép chất ma túy']
person=Dương Minh Tuấn | aliases=['Hoàng Nato'] | charge=tổ chức sử dụng trái phép chất ma túy | case=Vụ triệt phá 8 đường dây ma túy tại TP.HCM | substances=['etomidate'] | crimes=['mua bán trái phép chất ma túy', 'tàng trữ trái phép chất ma túy', 'tổ chức sử dụng trái phép chất ma túy']
person=Dương Minh Tuấn | aliases=['Hoàng Nato'] | charge=tổ chức sử dụng trái phép chất ma túy | case=Vụ sử dụng ma túy etomidate của Hoàng Nato và Phan Kim Nhi | substances=['etomidate'] | crimes=['tổ chức sử dụng trái phép chất ma túy']
person=Dương Minh Tuấn | aliases=['Hoàng Nato'] | charge=tổ chức sử dụng trái phép chất ma túy | case=Vụ bắt giữ TikToker Phannhibeauty và giang hồ 'Hoàng Nato' | substances=['etomidate'] | crimes=['tổ chức sử dụng trái phép chất ma túy']
person=Dương Minh Tuấn | aliases=['Hoàng Nato'] | charge=tổ chức sử dụng trái phép chất ma túy | case=Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy | substances=['Ketamine', 'MDMA', 'etomidate'] | crimes=['tàng trữ trái phép chất ma túy', 'mua bán trái phép chất ma túy', 'tổ chức sử dụng trái phép chất ma túy']
person=Trần Thanh Tuấn | aliases=[] | charge=mua bán trái phép chất ma túy | case=Vụ mua bán hơn 36kg ma túy tại TP.HCM | substances=[] | crimes=['mua bán trái phép chất ma túy', 'tổ chức sử dụng trái phép chất ma túy']
person=Đinh Đức Tuấn | aliases=[] | charge=tổ chức sử dụng trái phép chất ma túy | case=Vụ mua bán hơn 36kg ma túy tại TP.HCM | substances=[] | crimes=['mua bán trái phép chất ma túy', 'tổ chức sử dụng trái phép chất ma túy']
```

## E2_article255_clause_substances
```cypher
MATCH (:Article {id:'Điều 255 BLHS'})-[:HAS_CLAUSE]->(cl:Clause) OPTIONAL MATCH (cl)-[:MENTIONS]->(s:Substance) RETURN cl.number AS clause, cl.penalty AS penalty, collect(s.name) AS substances ORDER BY clause;
```
```
clause=1 | penalty=phạt tù từ 02 năm đến 07 năm | substances=[]
clause=2 | penalty=phạt tù từ 07 năm đến 15 năm | substances=[]
clause=3 | penalty=phạt tù từ 15 năm đến 20 năm | substances=[]
clause=4 | penalty=phạt tù 20 năm hoặc tù chung thân | substances=[]
clause=5 | penalty=phạt tiền từ 50.000.000 đồng đến 500.000.000 đồng, phạt quản chế, cấm cư trú từ 01 năm đến 05 năm hoặc tịch thu một phần hoặc toàn bộ tài sản | substances=[]
```

## E2_clauses_per_case_mdma_5_vien
```cypher
MATCH (k:Case)-[i:INVOLVES]->(s:Substance)<-[:MENTIONS]-(cl:Clause)<-[:HAS_CLAUSE]-(a:Article)-[:DEFINES]->(:Crime)<-[:CHARGED_WITH]-(k) RETURN k.name AS case, s.name AS substance, i.amount AS amount, a.id AS article, collect(cl.number) AS clauses_selected ORDER BY case;
```
```
```

## E3_substances
```cypher
MATCH (s:Substance) OPTIONAL MATCH (k:Case)-[:INVOLVES]->(s) RETURN s.name AS substance, count(k) AS cases ORDER BY toLower(substance);
```
```
substance=Amphetamine | cases=0
substance=chất ma túy khác (thể rắn) | cases=0
substance=Cocaine | cases=0
substance=côca | cases=0
substance=cần sa | cases=2
substance=etomidate | cases=4
substance=Heroine | cases=0
substance=Ketamine | cases=4
substance=MDMA | cases=5
substance=Methamphetamine | cases=3
substance=thuốc phiện | cases=0
substance=XLR-11 | cases=0
```

## E3_cases
```cypher
MATCH (k:Case) RETURN k.name AS case, k.doc_id AS doc_id ORDER BY toLower(k.name);
```
```
case=Chuyên án A3-626P | doc_id=news-100261002184934505
case=Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy | doc_id=news-100260920221957595
case=Vụ bắt giữ giang hồ mạng 'Đức Cộng' | doc_id=news-100260924101703641
case=Vụ bắt giữ TikToker Phannhibeauty và giang hồ 'Hoàng Nato' | doc_id=news-100260922111804786
case=Vụ góp tiền mua ma túy tại Hà Nội | doc_id=news-100260918080821054
case=Vụ mua bán hơn 36kg ma túy tại TP.HCM | doc_id=news-100260928173914514
case=Vụ phát hiện 20kg ma túy tại Phú Quốc | doc_id=news-100260927182621527
case=Vụ sử dụng ma túy etomidate của Hoàng Nato và Phan Kim Nhi | doc_id=news-100260924095400982
case=Vụ triệt phá 8 đường dây ma túy tại TP.HCM | doc_id=news-100260925144412498
case=Vụ tông cảnh sát giao thông ở An Giang | doc_id=news-100260926112415229
case=Vụ tổ chức sử dụng ma túy tại Sầm Sơn | doc_id=news-100260930085028036
case=Vụ vận chuyển 840kg ma túy đá tại Campuchia | doc_id=news-100260924145818945
case=Vụ vận chuyển ma túy từ Đức về Việt Nam | doc_id=news-100260917203001265
case=Vụ án tại Viện Pháp y tâm thần Trung ương | doc_id=news-100260924105118645
```

## E3_persons
```cypher
MATCH (p:Person)-[r:INVOLVED_IN]->(k:Case) RETURN p.name AS person, p.aliases AS aliases, collect(k.name) AS cases ORDER BY toLower(p.name);
```
```
person=7 công dân Trung Quốc | aliases=[] | cases=['Vụ vận chuyển 840kg ma túy đá tại Campuchia']
person=Bùi Thị Thanh Thủy | aliases=[] | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương']
person=Cao Thị Bích Hằng | aliases=[] | cases=['Vụ tổ chức sử dụng ma túy tại Sầm Sơn']
person=Cái Quang Huy | aliases=[] | cases=['Vụ vận chuyển ma túy từ Đức về Việt Nam']
person=Dương Minh Tuấn | aliases=['Hoàng Nato'] | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy", "Vụ bắt giữ TikToker Phannhibeauty và giang hồ 'Hoàng Nato'", 'Vụ sử dụng ma túy etomidate của Hoàng Nato và Phan Kim Nhi', 'Vụ triệt phá 8 đường dây ma túy tại TP.HCM']
person=Giang Quốc Khánh | aliases=[] | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy"]
person=Kim Xuân Tuấn | aliases=[] | cases=['Vụ góp tiền mua ma túy tại Hà Nội']
person=Kim Yu Young | aliases=[] | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy"]
person=Lê Minh Thành | aliases=[] | cases=['Vụ góp tiền mua ma túy tại Hà Nội']
person=Lê Văn Đông | aliases=[] | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương', 'Vụ tổ chức sử dụng ma túy tại Sầm Sơn']
person=Lê Đăng Khoa | aliases=[] | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy"]
person=Nguyễn Minh Nhân | aliases=[] | cases=['Vụ tông cảnh sát giao thông ở An Giang']
person=Nguyễn Minh Đức | aliases=['Đức Cộng'] | cases=["Vụ bắt giữ giang hồ mạng 'Đức Cộng'"]
person=Nguyễn Quang Hưng | aliases=[] | cases=['Vụ góp tiền mua ma túy tại Hà Nội']
person=Nguyễn Thành Quốc | aliases=[] | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy"]
person=Nguyễn Thị Mai Anh | aliases=['bà trùm'] | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương', 'Vụ tổ chức sử dụng ma túy tại Sầm Sơn']
person=Nguyễn Tiến Đạt | aliases=[] | cases=['Vụ vận chuyển ma túy từ Đức về Việt Nam']
person=Nguyễn Văn Quang | aliases=[] | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương']
person=Ngô Việt Dũng | aliases=[] | cases=['Vụ tổ chức sử dụng ma túy tại Sầm Sơn']
person=Ngô Văn Vinh | aliases=['cựu viện trưởng'] | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương']
person=Phan Kim Nhi | aliases=['TikToker Phannhibeauty'] | cases=["Vụ bắt giữ TikToker Phannhibeauty và giang hồ 'Hoàng Nato'", 'Vụ sử dụng ma túy etomidate của Hoàng Nato và Phan Kim Nhi', 'Vụ triệt phá 8 đường dây ma túy tại TP.HCM']
person=Phạm Minh Sang | aliases=[] | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy"]
person=Phạm Phương Anh | aliases=[] | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy"]
person=Phạm Tài Vình | aliases=[] | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy"]
person=Trần Minh Tâm | aliases=[] | cases=['Vụ mua bán hơn 36kg ma túy tại TP.HCM']
person=Trần Ngọc Nam | aliases=[] | cases=['Vụ tông cảnh sát giao thông ở An Giang']
person=Trần Ngọc Thảo | aliases=[] | cases=['Vụ mua bán hơn 36kg ma túy tại TP.HCM']
person=Trần Quốc An | aliases=[] | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương', 'Vụ tổ chức sử dụng ma túy tại Sầm Sơn']
person=Trần Thanh Tuấn | aliases=[] | cases=['Vụ mua bán hơn 36kg ma túy tại TP.HCM']
person=Trần Văn Trường | aliases=['cựu viện trưởng'] | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương']
person=Trịnh Vũ Kiên | aliases=[] | cases=['Vụ góp tiền mua ma túy tại Hà Nội']
person=Võ Nữ Minh Thư | aliases=[] | cases=['Vụ mua bán hơn 36kg ma túy tại TP.HCM']
person=Đinh Đức Tuấn | aliases=[] | cases=['Vụ mua bán hơn 36kg ma túy tại TP.HCM']
person=Đỗ Thị Ngọc Yến | aliases=[] | cases=['Vụ mua bán hơn 36kg ma túy tại TP.HCM']
```

## E3_location
```cypher
MATCH (l:Location) OPTIONAL MATCH (k)-[:LOCATED_IN]->(l) RETURN l.name AS location, count(k) AS cases ORDER BY toLower(l.name);
```
```
location=An Giang | cases=1
location=Hà Nội | cases=3
location=Ninh Bình | cases=1
location=Phú Quốc, An Giang | cases=1
location=Preah Sihanouk | cases=1
location=Thanh Hóa | cases=1
location=TP.HCM | cases=6
```

## E5_mdma_cases
```cypher
MATCH (k:Case)-[r:INVOLVES]->(s:Substance {name:'MDMA'}) RETURN k.name AS case, r.amount AS amount, k.doc_id AS doc_id ORDER BY doc_id;
```
```
case=Vụ vận chuyển ma túy từ Đức về Việt Nam | amount=9.6kg | doc_id=news-100260917203001265
case=Vụ góp tiền mua ma túy tại Hà Nội | amount=5 viên | doc_id=news-100260918080821054
case=Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy | amount=không rõ | doc_id=news-100260920221957595
case=Vụ án tại Viện Pháp y tâm thần Trung ương | amount= | doc_id=news-100260924105118645
case=Vụ tổ chức sử dụng ma túy tại Sầm Sơn | amount=0,686g | doc_id=news-100260930085028036
```

## OWN_thresholds_250_mdma
```cypher
MATCH (a:Article {id:'Điều 250 BLHS'})-[:HAS_CLAUSE]->(cl:Clause)-[t:THRESHOLD]->(s:Substance {name:'MDMA'}) RETURN cl.number AS clause, t.point AS point, t.min_g AS min_g, t.max_g AS max_g, cl.penalty AS penalty ORDER BY clause;
```
```
clause=1 | point=c | min_g=0.1 | max_g=5.0 | penalty=phạt tù từ 02 năm đến 07 năm
clause=2 | point=h | min_g=5.0 | max_g=30.0 | penalty=phạt tù từ 07 năm đến 15 năm
clause=3 | point=b | min_g=30.0 | max_g=100.0 | penalty=phạt tù từ 15 năm đến 20 năm
clause=4 | point=b | min_g=100.0 | max_g=None | penalty=phạt tù 20 năm, tù chung thân hoặc tử hình
```

## OWN_clause_by_amount
```cypher
MATCH (k:Case)-[i:INVOLVES]->(s:Substance) WHERE i.grams IS NOT NULL MATCH (k)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(a:Article)-[:HAS_CLAUSE]->(cl:Clause)-[t:THRESHOLD]->(g:Substance) WHERE g.name = CASE WHEN EXISTS { (a)-[:HAS_CLAUSE]->()-[:THRESHOLD]->(s) } THEN s.name ELSE 'chất ma túy khác (thể rắn)' END AND t.min_g <= i.grams AND (t.max_g IS NULL OR i.grams < t.max_g) RETURN k.name AS case, s.name AS substance, i.amount AS amount, i.grams AS grams, a.id AS article, cl.number AS clause, t.point AS point ORDER BY case, article;
```
```
case=Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy | substance=Ketamine | amount=khoảng 100g | grams=100.0 | article=Điều 249 BLHS | clause=3 | point=e
case=Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy | substance=Ketamine | amount=khoảng 100g | grams=100.0 | article=Điều 251 BLHS | clause=3 | point=e
case=Vụ tổ chức sử dụng ma túy tại Sầm Sơn | substance=MDMA | amount=0,686g | grams=0.686 | article=Điều 249 BLHS | clause=1 | point=c
case=Vụ vận chuyển 840kg ma túy đá tại Campuchia | substance=Methamphetamine | amount=840kg | grams=840000.0 | article=Điều 250 BLHS | clause=4 | point=b
case=Vụ vận chuyển ma túy từ Đức về Việt Nam | substance=Ketamine | amount=406g | grams=406.0 | article=Điều 250 BLHS | clause=4 | point=e
case=Vụ vận chuyển ma túy từ Đức về Việt Nam | substance=MDMA | amount=9.6kg | grams=9600.0 | article=Điều 250 BLHS | clause=4 | point=b
```

## OWN_max_penalty_255
```cypher
MATCH (:Article {id:'Điều 255 BLHS'})-[:HAS_CLAUSE]->(cl:Clause) RETURN cl.number AS clause, cl.max_years AS max_years, cl.life AS life, cl.death AS death, cl.severity AS severity ORDER BY severity DESC;
```
```
clause=4 | max_years=20.0 | life=True | death=False | severity=25
clause=3 | max_years=20.0 | life=False | death=False | severity=20.0
clause=2 | max_years=15.0 | life=False | death=False | severity=15.0
clause=1 | max_years=7.0 | life=False | death=False | severity=7.0
clause=5 | max_years=None | life=False | death=False | severity=0
```

## OWN_substance_aliases
```cypher
MATCH (s:Substance) WHERE size(coalesce(s.aliases, [])) > 0 RETURN s.name AS substance, s.aliases AS aliases ORDER BY substance;
```
```
substance=Cocaine | aliases=['cocain']
substance=Heroine | aliases=['heroin', 'hêrôin']
substance=Ketamine | aliases=['ketamin', 'ke']
substance=MDMA | aliases=['thuốc lắc', 'ecstasy']
substance=Methamphetamine | aliases=['ma túy đá', 'ma tuý đá', 'hồng phiến']
substance=cần sa | aliases=['marijuana', 'bồ đà']
```

## E6_empty_charge
```cypher
MATCH (p:Person)-[r:INVOLVED_IN]->(k) WHERE r.charge = '' RETURN p.name AS person, r.role AS role, r.sentence AS sentence, k.name AS case ORDER BY case;
```
```
person=Phan Kim Nhi | role=người liên quan | sentence= | case=Vụ triệt phá 8 đường dây ma túy tại TP.HCM
person=Nguyễn Minh Nhân | role=bị can | sentence= | case=Vụ tông cảnh sát giao thông ở An Giang
person=Trần Ngọc Nam | role=người liên quan | sentence= | case=Vụ tông cảnh sát giao thông ở An Giang
person=Trần Quốc An | role=người liên quan | sentence=không rõ | case=Vụ tổ chức sử dụng ma túy tại Sầm Sơn
person=Ngô Việt Dũng | role=người liên quan | sentence=không rõ | case=Vụ tổ chức sử dụng ma túy tại Sầm Sơn
person=Cao Thị Bích Hằng | role=người liên quan | sentence=không rõ | case=Vụ tổ chức sử dụng ma túy tại Sầm Sơn
person=Nguyễn Thị Mai Anh | role=bị can | sentence=chuỗi rỗng | case=Vụ án tại Viện Pháp y tâm thần Trung ương
person=Lê Văn Đông | role=bị can | sentence=chuỗi rỗng | case=Vụ án tại Viện Pháp y tâm thần Trung ương
person=Bùi Thị Thanh Thủy | role=bị can | sentence=chuỗi rỗng | case=Vụ án tại Viện Pháp y tâm thần Trung ương
person=Trần Quốc An | role=cán bộ | sentence=chuỗi rỗng | case=Vụ án tại Viện Pháp y tâm thần Trung ương
person=Nguyễn Văn Quang | role=cán bộ | sentence=chuỗi rỗng | case=Vụ án tại Viện Pháp y tâm thần Trung ương
person=Ngô Văn Vinh | role=người liên quan | sentence=chuỗi rỗng | case=Vụ án tại Viện Pháp y tâm thần Trung ương
person=Trần Văn Trường | role=người liên quan | sentence=chuỗi rỗng | case=Vụ án tại Viện Pháp y tâm thần Trung ương
```

