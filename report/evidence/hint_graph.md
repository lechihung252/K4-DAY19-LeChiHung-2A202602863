# Graph: 205 nodes / 382 rels

## count_nodes
```cypher
MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC;
```
```
label=Clause | n=99
label=Person | n=37
label=Article | n=18
label=Substance | n=17
label=Case | n=14
label=Crime | n=13
label=Location | n=7
```

## count_rels
```cypher
MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS n ORDER BY n DESC;
```
```
rel=MENTIONS | n=169
rel=HAS_CLAUSE | n=99
rel=INVOLVED_IN | n=44
rel=INVOLVES | n=24
rel=CHARGED_WITH | n=19
rel=LOCATED_IN | n=14
rel=DEFINES | n=13
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
doc_id=news-100260922111804786 | cases=['Vụ tổ chức sử dụng trái phép chất ma túy tại TP.HCM']
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
person=Dương Minh Tuấn | aliases=['Hoàng Nato'] | charge=tổ chức sử dụng trái phép chất ma túy | case=Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy | substances=['ma túy tổng hợp', 'etomidate', 'ketamine', 'thuốc lắc'] | crimes=['tổ chức sử dụng trái phép chất ma túy', 'mua bán trái phép chất ma túy', 'tàng trữ trái phép chất ma túy']
person=Dương Minh Tuấn | aliases=['Hoàng Nato'] | charge=tổ chức sử dụng trái phép chất ma túy | case=Vụ tổ chức sử dụng trái phép chất ma túy tại TP.HCM | substances=['ma túy tổng hợp', 'etomidate'] | crimes=['tổ chức sử dụng trái phép chất ma túy']
person=Dương Minh Tuấn | aliases=['Hoàng Nato'] | charge=tổ chức sử dụng trái phép chất ma túy | case=Vụ sử dụng ma túy etomidate của Hoàng Nato và Phan Kim Nhi | substances=['etomidate'] | crimes=['tổ chức sử dụng trái phép chất ma túy']
person=Dương Minh Tuấn | aliases=['Hoàng Nato'] | charge=tổ chức sử dụng trái phép chất ma túy | case=Vụ triệt phá 8 đường dây ma túy tại TP.HCM | substances=['etomidate'] | crimes=['tổ chức sử dụng trái phép chất ma túy', 'tàng trữ trái phép chất ma túy', 'mua bán trái phép chất ma túy']
person=Đinh Đức Tuấn | aliases=[] | charge=tổ chức sử dụng trái phép chất ma túy | case=Vụ mua bán hơn 36kg ma túy tại TP.HCM | substances=['ma túy'] | crimes=['mua bán trái phép chất ma túy', 'tổ chức sử dụng trái phép chất ma túy']
person=Trần Thanh Tuấn | aliases=[] | charge=mua bán trái phép chất ma túy | case=Vụ mua bán hơn 36kg ma túy tại TP.HCM | substances=['ma túy'] | crimes=['mua bán trái phép chất ma túy', 'tổ chức sử dụng trái phép chất ma túy']
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
case=Vụ góp tiền mua ma túy tại Hà Nội | substance=MDMA | amount=5 viên | article=Điều 251 BLHS | clauses_selected=[2, 4, 3]
case=Vụ tổ chức sử dụng ma túy tại Sầm Sơn | substance=cần sa | amount=không rõ | article=Điều 249 BLHS | clauses_selected=[3, 4, 2, 1]
case=Vụ tổ chức sử dụng ma túy tại Sầm Sơn | substance=MDMA | amount=0,686g | article=Điều 249 BLHS | clauses_selected=[3, 4, 2, 1]
case=Vụ vận chuyển 840kg ma túy đá tại Campuchia | substance=Methamphetamine | amount=840kg | article=Điều 250 BLHS | clauses_selected=[1, 2, 3, 4]
case=Vụ vận chuyển ma túy từ Đức về Việt Nam | substance=MDMA | amount=9.6kg | article=Điều 250 BLHS | clauses_selected=[1, 2, 3, 4]
case=Vụ án tại Viện Pháp y tâm thần Trung ương | substance=cần sa | amount= | article=Điều 249 BLHS | clauses_selected=[3, 4, 2, 1]
case=Vụ án tại Viện Pháp y tâm thần Trung ương | substance=MDMA | amount= | article=Điều 249 BLHS | clauses_selected=[3, 4, 2, 1]
case=Vụ án tại Viện Pháp y tâm thần Trung ương | substance=Methamphetamine | amount= | article=Điều 249 BLHS | clauses_selected=[3, 4, 2, 1]
```

## E3_substances
```cypher
MATCH (s:Substance) OPTIONAL MATCH (k:Case)-[:INVOLVES]->(s) RETURN s.name AS substance, count(k) AS cases ORDER BY toLower(s.name);
```
```
substance=Amphetamine | cases=0
substance=chất ma túy | cases=1
substance=Cocaine | cases=0
substance=côca | cases=0
substance=cần sa | cases=2
substance=etomidate | cases=4
substance=Heroine | cases=0
substance=Ketamine | cases=3
substance=ketamine | cases=1
substance=ma túy | cases=3
substance=ma túy tổng hợp | cases=2
substance=MDMA | cases=4
substance=Methamphetamine | cases=2
substance=methamphetamine | cases=1
substance=thuốc lắc | cases=1
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
case=Vụ góp tiền mua ma túy tại Hà Nội | doc_id=news-100260918080821054
case=Vụ mua bán hơn 36kg ma túy tại TP.HCM | doc_id=news-100260928173914514
case=Vụ phát hiện 20kg ma túy tại Phú Quốc | doc_id=news-100260927182621527
case=Vụ sử dụng ma túy etomidate của Hoàng Nato và Phan Kim Nhi | doc_id=news-100260924095400982
case=Vụ triệt phá 8 đường dây ma túy tại TP.HCM | doc_id=news-100260925144412498
case=Vụ tông cảnh sát giao thông ở An Giang | doc_id=news-100260926112415229
case=Vụ tổ chức sử dụng ma túy tại Sầm Sơn | doc_id=news-100260930085028036
case=Vụ tổ chức sử dụng trái phép chất ma túy tại TP.HCM | doc_id=news-100260922111804786
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
person=DJ Thái Hoàng | aliases=[] | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương']
person=Dương Minh Tuấn | aliases=['Hoàng Nato'] | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy", 'Vụ tổ chức sử dụng trái phép chất ma túy tại TP.HCM', 'Vụ sử dụng ma túy etomidate của Hoàng Nato và Phan Kim Nhi', 'Vụ triệt phá 8 đường dây ma túy tại TP.HCM']
person=Dương Văn Biết | aliases=['Trưởng khoa giám định'] | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương']
person=Dương Văn Lương | aliases=['Phó viện trưởng'] | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương']
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
person=Nguyễn Thị Thu Hoài | aliases=[] | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương']
person=Nguyễn Tiến Đạt | aliases=[] | cases=['Vụ vận chuyển ma túy từ Đức về Việt Nam']
person=Nguyễn Văn Quang | aliases=[] | cases=['Vụ án tại Viện Pháp y tâm thần Trung ương']
person=Ngô Việt Dũng | aliases=[] | cases=['Vụ tổ chức sử dụng ma túy tại Sầm Sơn']
person=Phan Kim Nhi | aliases=['TikToker Phannhibeauty'] | cases=['Vụ tổ chức sử dụng trái phép chất ma túy tại TP.HCM', 'Vụ sử dụng ma túy etomidate của Hoàng Nato và Phan Kim Nhi', 'Vụ triệt phá 8 đường dây ma túy tại TP.HCM']
person=Phạm Minh Sang | aliases=[] | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy"]
person=Phạm Phương Anh | aliases=[] | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy"]
person=Phạm Tài Vình | aliases=[] | cases=["Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy"]
person=Trần Minh Tâm | aliases=[] | cases=['Vụ mua bán hơn 36kg ma túy tại TP.HCM']
person=Trần Ngọc Nam | aliases=[] | cases=['Vụ tông cảnh sát giao thông ở An Giang']
person=Trần Ngọc Thảo | aliases=[] | cases=['Vụ mua bán hơn 36kg ma túy tại TP.HCM']
person=Trần Quốc An | aliases=[] | cases=['Vụ tổ chức sử dụng ma túy tại Sầm Sơn']
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
case=Vụ án tại Viện Pháp y tâm thần Trung ương | amount= | doc_id=news-100260924105118645
case=Vụ tổ chức sử dụng ma túy tại Sầm Sơn | amount=0,686g | doc_id=news-100260930085028036
```

## E6_empty_charge
```cypher
MATCH (p:Person)-[r:INVOLVED_IN]->(k) WHERE r.charge = '' RETURN p.name AS person, r.role AS role, r.sentence AS sentence, k.name AS case ORDER BY case;
```
```
person=Nguyễn Minh Nhân | role=bị can | sentence= | case=Vụ tông cảnh sát giao thông ở An Giang
person=Trần Ngọc Nam | role=người liên quan | sentence= | case=Vụ tông cảnh sát giao thông ở An Giang
person=Trần Văn Trường | role=người liên quan | sentence= | case=Vụ án tại Viện Pháp y tâm thần Trung ương
person=Dương Văn Lương | role=người liên quan | sentence= | case=Vụ án tại Viện Pháp y tâm thần Trung ương
person=Dương Văn Biết | role=người liên quan | sentence= | case=Vụ án tại Viện Pháp y tâm thần Trung ương
person=Nguyễn Văn Quang | role=cán bộ | sentence= | case=Vụ án tại Viện Pháp y tâm thần Trung ương
person=Nguyễn Thị Thu Hoài | role=cán bộ | sentence= | case=Vụ án tại Viện Pháp y tâm thần Trung ương
```

