# Báo cáo Day 19 — Flat RAG vs GraphRAG

**Họ tên:** Lê Chí Hùng  **MSSV:** 2A202602863  **Ngày:** 05/10/2026

> Kỳ vọng và thang điểm: `SUBMISSION.md`. Mọi số liệu phải khớp với `ket_qua_benchmark_kg.txt`. Bản thiết kế ontology nộp riêng ở `report/ONTOLOGY.md`.

Cấu hình: `openai:gpt-4o-mini` (chat), `openai:text-embedding-3-small` (embedding), `top_k=3`, `chunk_size=800`, 176 chunk. KG dùng **ontology tự thiết kế** (197 node / 456 cạnh). Kết quả của ontology gợi ý để đối chiếu nằm trong `ket_qua_benchmark_kg.hint.txt`.

## 1. Chi phí (10 điểm)

```
== Indexing (one-off)
pipeline  calls    in_tok  out_tok       USD  seconds
flat        176     56072        0   0.00112     43.4
graph       196     91958     4620   0.00928    109.9

== Querying (mean per question)
pipeline  recall  judge   in_tok  out_tok       USD  seconds
flat        0.43   1.00      694       47   0.00013     1.54
graph       0.94   1.83     4777       78   0.00076     2.37
```

| Chỉ số | Flat | Graph | Graph / Flat |
| --- | --- | --- | --- |
| Indexing USD | 0.00112 | 0.00928 | ×8.3 |
| Indexing giây | 43.4 | 109.9 | ×2.5 |
| Mỗi câu: USD | 0.00013 | 0.00076 | ×5.8 |
| Mỗi câu: giây | 1.54 | 2.37 | ×1.5 |
| Mỗi câu: in_tok | 694 | 4777 | ×6.9 |

**Chi phí tăng thêm đến từ đâu?**

> **Indexing:** GraphRAG vẫn embed đúng 176 chunk như Flat (56 072 token, 0.00112 USD), rồi gọi LLM thêm **20 lần** để trích xuất 20 bài báo (91 958 − 56 072 = 35 886 token vào, 4 620 token ra). Với giá `gpt-4o-mini` trong `src/llm.py` (0.15 / 0.60 USD cho 1 triệu token), phần trích xuất tốn khoảng 0.0054 + 0.0028 = **0.0082 USD, chiếm 88 %** chi phí dựng graph và khoảng 66 giây. Phần luật trích bằng regex nên không tốn token.
>
> **Mỗi câu hỏi:** chênh lệch đến gần như hoàn toàn từ **prompt dài hơn**: thêm 4 083 token đầu vào cho dữ kiện graph (khoảng 0.00061 USD), trong khi token đầu ra chỉ tăng 31 (khoảng 0.00002 USD). Có thêm khoảng 0.8 giây cho các truy vấn Cypher và cho LLM đọc prompt dài hơn.
>
> **Điểm hòa vốn:** GraphRAG tốn thêm 0.0082 USD một lần cộng 0.00063 USD mỗi câu. Với 1 000 câu hỏi, tổng là 0.77 USD so với 0.14 USD của Flat. Tính trên câu trả lời *đúng đủ* (judge = 2) của benchmark: Flat đúng 2/6 câu, mỗi câu đúng tốn khoảng 0.00039 USD; Graph đúng 5/6 câu, mỗi câu đúng tốn khoảng 0.00091 USD (chưa tính indexing). Riêng với 3 câu cross-kb (Q3–Q5), Flat không có câu nào đúng đủ, nên không có mức chi phí nào của Flat mua được câu trả lời đúng. Ở đây chi phí không phải yếu tố quyết định, khả năng trả lời mới là.
>
> So với ontology gợi ý (`.hint.txt`): indexing gần bằng nhau (0.00935 so với 0.00928 USD, vì cùng số lần gọi LLM), mỗi câu 0.00072 so với 0.00076 USD. Dòng "khung cao nhất" làm tăng một chút token, và phần cắt bớt text khoản bù lại gần hết.

## 2. Từng câu hỏi (10 điểm)

| Câu | Loại | Flat recall / judge | Graph recall / judge | Thắng | Vì sao (1 câu) |
| --- | --- | --- | --- | --- | --- |
| Q1 | single-hop-law | 1.00 / 2 | 1.00 / 2 | Hòa | Định nghĩa "tiền chất" nằm gọn trong một chunk của Điều 2 Luật PCMT; graph không thêm gì mà chậm hơn (2.94 giây so với 1.27 giây). |
| Q2 | single-hop-news | 1.00 / 2 | 1.00 / 2 | Hòa | Tên hai bị cáo lãnh án tử hình nằm trong cùng một bài báo, nên vector search lấy được ngay. |
| Q3 | cross-kb | 0.00 / 0 | 1.00 / 2 | **Graph** | Flat trả lời "Không đủ thông tin" vì không chunk nào chứa cả mức án lẫn Điều 251; graph đi `Person → Case → Crime → Article → Clause 1` và lấy được "02 năm đến 07 năm". |
| Q4 | cross-kb | 0.00 / 0 | 1.00 / 2 | **Graph** | Flat lại "Không đủ thông tin"; graph tìm ra Hoàng Nato qua `aliases`, đi tới Điều 255 và lấy được khoản 4 nhờ `severity` ("20 năm hoặc tù chung thân"). |
| Q5 | cross-kb-multi-hop | 0.60 / 1 | 1.00 / 2 | **Graph** | Flat nhầm điểm với khoản ("khoản b") và không nêu Điều; graph so 9 600 gam với `THRESHOLD` và chọn đúng Điều 250 khoản 4. |
| Q6 | aggregation | 0.00 / 1 | 0.67 / 1 | Graph (sát nút) | Flat chỉ ghi tên gọi tắt ("Thành", "Đông") nên recall bằng 0; graph liệt kê đúng 3 vụ nhưng LLM bỏ mất tên "Lê Minh Thành" dù dữ kiện graph có (lỗi E5). |

**Quy luật:** loại câu hỏi quyết định bên thắng.
- **Single-hop** (Q1, Q2): đáp án nằm trong 1 đoạn, hai bên hòa. Graph chỉ thêm khoảng 6 lần token và 1.5 lần thời gian.
- **Cross-kb** (Q3–Q5): đáp án nằm ở cả hai KB, Flat đạt recall trung bình 0.20 so với **1.00** của Graph. Đây là nơi node cầu nối tạo ra giá trị.
- **Aggregation** (Q6): đáp án rải ở nhiều bài, cả hai đều chỉ đúng một phần (judge 1). Graph *có* đủ dữ kiện, nhưng bước LLM viết câu trả lời làm rơi bớt.

## 3. Phân tích lỗi (20 điểm)

### Lỗi E2: Thiếu ngữ cảnh luật, sai khung hình phạt tối đa (phát hiện trên ontology gợi ý, đã sửa bằng ontology mới)

- **Hiện tượng:** với ontology gợi ý, Q4 của GraphRAG trả lời sai mức phạt tối đa, dù graph có đủ Điều 255.

  > `ket_qua_benchmark_kg.hint.txt`, Q4, graph (recall 0.67, judge 1): *"Giang hồ 'Hoàng Nato' bị bắt về hành vi tổ chức sử dụng trái phép chất ma túy. Hành vi này có thể bị phạt tù tối đa **07 năm** theo Điều 255 Bộ luật Hình sự."*

  Đáp án chuẩn là khung cao nhất: tù 20 năm hoặc chung thân.
- **Bằng chứng:** trên graph của ontology gợi ý (`report/evidence/hint_graph.md`):

```cypher
MATCH (:Article {id:'Điều 255 BLHS'})-[:HAS_CLAUSE]->(cl:Clause)
OPTIONAL MATCH (cl)-[:MENTIONS]->(s:Substance)
RETURN cl.number AS clause, cl.penalty AS penalty, collect(s.name) AS substances ORDER BY clause;
```

```
clause=1 | penalty=phạt tù từ 02 năm đến 07 năm | substances=[]
clause=2 | penalty=phạt tù từ 07 năm đến 15 năm | substances=[]
clause=3 | penalty=phạt tù từ 15 năm đến 20 năm | substances=[]
clause=4 | penalty=phạt tù 20 năm hoặc tù chung thân | substances=[]
clause=5 | penalty=phạt tiền từ 50.000.000 đồng ... | substances=[]
```

  Cùng file đó, `E2_clauses_per_case`, cho thấy chiều ngược lại của cùng quy tắc lọc: vụ "5 viên MDMA" chọn khoản `[2, 4, 3]` và vụ "0,686g MDMA" chọn cả `[3, 4, 2, 1]`, vì khoản nào cũng nhắc MDMA.
- **Nguyên nhân:** nằm ở **thiết kế ontology và Cypher của KG-3**. Quy tắc gợi ý là "khoản 1 + khoản `MENTIONS` một chất mà vụ `INVOLVES`". Điều 255 (tổ chức sử dụng) không có khoản nào nhắc tên chất, nên chỉ còn khoản 1 và LLM lấy "07 năm" làm mức tối đa. Ngược lại, ở các Điều có ngưỡng khối lượng, điều kiện theo *tên* chất không phân biệt được khoản, vì ontology không có khối lượng.
- **Đề xuất sửa (đã làm):** trong `src/graph.py` (`parse_penalty`, `parse_thresholds`, `Neo4jGraph.context`):
  - Lưu `Clause {max_years, life, death, severity}` và luôn thêm khung cao nhất của mỗi Điều.
  - Thêm cạnh `THRESHOLD {min_g, max_g}` và `INVOLVES {grams}` để chọn khoản theo khối lượng.

  Kết quả: Q4 trả lời *"tối đa 20 năm hoặc tù chung thân theo Điều 255 BLHS khoản 4"* (recall 1.00, judge 2). Cypher sau khi sửa:

```cypher
MATCH (:Article {id:'Điều 255 BLHS'})-[:HAS_CLAUSE]->(cl:Clause)
RETURN cl.number AS clause, cl.max_years AS max_years, cl.life AS life, cl.severity AS severity ORDER BY severity DESC;
```

```
clause=4 | max_years=20.0 | life=True | severity=25
clause=3 | max_years=20.0 | life=False | severity=20.0
...
```

  Đánh đổi: thêm khoảng 1 dòng mỗi Điều trong prompt (mỗi câu 0.00072 → 0.00076 USD); không có thêm lần gọi LLM nào.

### Lỗi E5: LLM lệch với graph ở câu tổng hợp

- **Hiện tượng:** ở Q6, graph đưa đủ tên người cho từng vụ có MDMA, nhưng câu trả lời của GraphRAG bỏ mất "Lê Minh Thành" (recall 0.67). Lần chạy với ontology gợi ý thì LLM lại **bịa thêm** một vụ không có MDMA. Chạy hai lần cho ra hai kiểu lỗi khác nhau.
- **Bằng chứng:**

  > `ket_qua_benchmark_kg.txt`, Q6, graph (recall 0.67, judge 1): *"2. **Vụ góp tiền mua ma túy tại Hà Nội**: Có liên quan đến 5 viên MDMA."* Câu này không có tên người nào.

```cypher
MATCH (s:Substance {name:'MDMA'})<-[i:INVOLVES]-(k:Case)
OPTIONAL MATCH (p:Person)-[:INVOLVED_IN]->(k)
RETURN k.name AS case, i.amount AS amount, collect(p.name) AS people ORDER BY case;
```

```
case=Vụ bắt giang hồ 'Hoàng Nato' và 126 người ... | amount=không rõ  | people=[Nguyễn Thành Quốc, Phạm Minh Sang, Giang Quốc Khánh, Dương Minh Tuấn, ...]
case=Vụ góp tiền mua ma túy tại Hà Nội              | amount=5 viên    | people=[Kim Xuân Tuấn, Nguyễn Quang Hưng, Lê Minh Thành, Trịnh Vũ Kiên]
case=Vụ tổ chức sử dụng ma túy tại Sầm Sơn          | amount=0,686g    | people=[Nguyễn Thị Mai Anh, Trần Quốc An, Cao Thị Bích Hằng, Lê Văn Đông, Ngô Việt Dũng]
case=Vụ vận chuyển ma túy từ Đức về Việt Nam        | amount=9.6kg     | people=[Cái Quang Huy, Nguyễn Tiến Đạt]
case=Vụ án tại Viện Pháp y tâm thần Trung ương      | amount=          | people=[Lê Văn Đông, Nguyễn Văn Quang, Trần Văn Trường, ...]
```

  Dữ kiện tổng hợp mà `context()` đưa vào prompt có câu *"Vụ góp tiền mua ma túy tại Hà Nội (5 viên) - Kim Xuân Tuấn, Nguyễn Quang Hưng, Lê Minh Thành"*. Lần chạy ontology gợi ý (`.hint.txt`, Q6, graph) thì ghi: *"5. **Vụ mua bán hơn 36kg ma túy tại TP.HCM**: Mặc dù không nêu rõ, nhưng có thể liên quan đến MDMA do tổng khối lượng ma túy lớn."* Trong khi đó, graph gợi ý chỉ nối vụ này với node `ma túy` chung chung, không có MDMA (`hint_graph.md`, `E2_hoang_nato`: `substances=['ma túy']`).
- **Nguyên nhân:** nằm ở **prompt trả lời** (`GRAPH_PROMPT`) và ở bản chất sinh văn bản của LLM.
  - Prompt chỉ yêu cầu "trả lời dựa trên ngữ cảnh", không bắt liệt kê đủ và không cấm suy đoán.
  - Với danh sách dài (5 vụ, hơn 20 tên), `gpt-4o-mini` tóm tắt theo ý nó: bỏ người, hoặc thêm "có thể liên quan".
  - Có thêm một nguyên nhân từ thiết kế: để tránh kéo mọi vụ vào phần căn cứ pháp lý, node `Substance` không được dùng để mở rộng vụ án. Vì vậy tóm tắt vụ Hà Nội (câu có tên Thành) không còn trong prompt, chỉ còn một dòng tổng hợp ngắn.
- **Đề xuất sửa:**
  1. Với câu hỏi tổng hợp, trả lời thẳng bằng kết quả Cypher (template hóa: "Có N vụ: …") thay vì để LLM diễn đạt lại. Cách này rẻ hơn và tất định, nhưng cần nhận diện được loại câu hỏi.
  2. Thêm vào `GRAPH_PROMPT` yêu cầu "liệt kê đủ mọi mục trong dữ kiện graph, không thêm mục không có trong dữ kiện". Gần như không tốn thêm token.
  3. Chạy benchmark nhiều lần và báo cáo trung bình, vì lỗi thay đổi giữa các lần chạy.

### Lỗi E3: Trùng thực thể, một sự kiện thành nhiều node `Case`

- **Hiện tượng:** vụ bắt "Hoàng Nato" được 4 bài báo đưa tin, và graph tạo ra 4 node `Case` khác tên. Trùng tên chất (ở ontology gợi ý) đã được sửa; trùng vụ án thì vẫn còn.
- **Bằng chứng:**

```cypher
MATCH (p:Person)-[:INVOLVED_IN]->(k:Case) WHERE 'Hoàng Nato' IN p.aliases
RETURN p.name AS person, k.name AS case, k.doc_id AS doc_id ORDER BY doc_id;
```

```
person=Dương Minh Tuấn | case=Vụ bắt giang hồ 'Hoàng Nato' và 126 người liên quan 8 đường dây ma túy | doc_id=news-100260920221957595
person=Dương Minh Tuấn | case=Vụ bắt giữ TikToker Phannhibeauty và giang hồ 'Hoàng Nato'           | doc_id=news-100260922111804786
person=Dương Minh Tuấn | case=Vụ sử dụng ma túy etomidate của Hoàng Nato và Phan Kim Nhi           | doc_id=news-100260924095400982
person=Dương Minh Tuấn | case=Vụ triệt phá 8 đường dây ma túy tại TP.HCM                          | doc_id=news-100260925144412498
```

  Tương tự, Lê Văn Đông, Nguyễn Thị Mai Anh và Trần Quốc An cùng thuộc 2 vụ "Sầm Sơn" và "Viện Pháp y tâm thần" (`own_graph.md`, `E3_persons`). Về chất, ontology gợi ý có 17 node, trong đó có `Ketamine`/`ketamine` và `Methamphetamine`/`methamphetamine`; ontology mới còn 12 node, không trùng (`E3_substances` trong hai file bằng chứng).
- **Nguyên nhân:** nằm ở **thiết kế ontology và prompt trích xuất**. `Case` được `MERGE` theo `name` do LLM đặt, và LLM đọc từng bài một mà không biết các vụ đã có. Mỗi bài đặt một tên khác nhau nên `MERGE` không gộp được. `Person` thì gộp được vì họ tên là khóa ổn định, nên chính `Person` là cầu nối 4 vụ với nhau. Hệ quả: ở Q4, `context()` lấy cả 4 vụ, kéo theo khung của Điều 249 và 251, làm prompt dài hơn hẳn: khi chỉ dùng node khởi đầu tìm theo tên trong câu hỏi, `context()` trả về 20 dữ kiện cho Q4 so với 5 cho Q3.
- **Đề xuất sửa:**
  - Tách `Report` (bài báo, khóa `doc_id`) khỏi `Case` (sự kiện), nối bằng `(:Report)-[:REPORTS {stage: bắt | khởi tố | xét xử}]->(:Case)`.
  - Trong prompt trích xuất, đưa danh sách vụ đã có (tên, người chính) để LLM chọn dùng lại hoặc tạo mới, rồi xác nhận lại bằng `link_entity` trên tên vụ.
  - Đánh đổi: prompt mỗi bài dài thêm (danh sách vụ tăng dần theo số bài), và thứ tự nạp bài ảnh hưởng kết quả. Nếu gộp nhầm hai vụ khác nhau thì còn tệ hơn để tách.

### Lỗi E4: Phép đo sai, recall và judge mâu thuẫn

- **Hiện tượng:** `recall` (khớp từ khóa) và `judge` (LLM chấm) cho điểm ngược nhau ở Q6.
- **Bằng chứng:** `must_include` của Q6 là `["Cái Quang Huy", "Lê Minh Thành", "Pháp y tâm thần"]`.
  - `ket_qua_benchmark_kg.txt`, Q6, **flat** (recall **0.00**, judge 1): *"1. Vụ việc của **Đức** … 2. Vụ việc của **Thành** liên quan đến 5 viên nén màu trắng được xác định là ma túy MDMA. 3. Vụ việc của **Đông** …"*. Câu trả lời đúng về nội dung với 2 vụ, nhưng chỉ dùng tên gọi tắt nên recall bằng 0.
  - `ket_qua_benchmark_kg.hint.txt`, Q6, **graph** (recall **1.00**, judge 1): có đủ 3 từ khóa nhưng **bịa thêm** vụ 36kg (lỗi E5). Recall chấm tối đa cho một câu trả lời có thông tin sai.
- **Nguyên nhân:** nằm ở **phép đo**. `keyword_recall` chỉ kiểm tra chuỗi con chính xác: không nhận tên gọi tắt, và không phạt nội dung thừa hoặc sai. Judge thì linh hoạt hơn, nhưng thang 0–2 quá thô để phân biệt "thiếu 1 tên" với "thêm 1 vụ sai", và nó cũng là một LLM nên có thể dao động.
- **Đề xuất sửa:** đo thêm *precision*: tách các vụ hoặc người trong câu trả lời rồi so với tập đúng. Cho phép khớp theo alias của người (graph đã có `Person.aliases`). Yêu cầu judge chấm riêng phần "thiếu" và phần "sai". Chạy mỗi câu nhiều lần. Đánh đổi: chi phí đo tăng theo số lần chạy.

## 4. Kết luận (5 điểm)

> **Nên dùng KG khi câu hỏi cần nối dữ kiện từ nhiều nguồn khác nhau.** Ở các câu cross-kb Q3–Q5, Flat RAG đạt recall trung bình 0.20 và không câu nào đúng đủ (judge 0, 0, 1). GraphRAG đạt recall **1.00** và judge **2** ở cả ba câu. Tính trên cả benchmark, recall là 0.43 → 0.94 và judge 1.00 → 1.83, đổi lại chi phí mỗi câu ×5.8 (0.00013 → 0.00076 USD), độ trễ ×1.5 (1.54 → 2.37 giây), và chi phí dựng ×8.3 (thêm khoảng 0.008 USD cho 20 lần trích xuất). Với chi phí tuyệt đối dưới 0.001 USD mỗi câu, mức tăng này đáng tiền nếu hệ thống thường xuyên phải trả lời câu kiểu "người X bị xử theo Điều nào, khung bao nhiêu".
>
> **Flat RAG là đủ** khi đáp án nằm trong một đoạn văn: Q1 (luật) và Q2 (tin) hòa nhau 2/2, còn Graph chỉ tốn thêm khoảng 6 lần token. Nếu phần lớn câu hỏi là tra cứu một nguồn, nên dùng Flat, hoặc chỉ gọi graph khi câu hỏi nhắc tới cả người hoặc vụ lẫn điều luật hoặc mức phạt.
>
> **Điều kiện để KG có lời:**
> 1. Có một **thực thể cầu nối** mà cả hai nguồn cùng gọi tên được (ở đây là tội danh), cộng với cơ chế chuẩn hóa tên (`link_entity`, danh sách tên chuẩn).
> 2. Ít nhất một nguồn có **cấu trúc đều** để trích bằng regex, gần như miễn phí. Ở đây toàn bộ phần luật tốn 0 token LLM.
> 3. Ontology mô hình hóa đúng thứ câu hỏi cần. Cùng một dữ liệu, chỉ thêm ngưỡng khối lượng và khung phạt có cấu trúc đã đưa judge từ 1.67 lên 1.83 và sửa sai ở Q4.
>
> **Khi nào KG chưa đủ:** câu hỏi tổng hợp (Q6). Graph có đủ dữ kiện nhưng LLM vẫn bỏ sót hoặc bịa thêm (E5). Loại câu này nên trả lời thẳng từ kết quả Cypher.

## 5. Tự kiểm (5 điểm)

```
$ pytest tests/ -q
................................................                         [100%]
48 passed in 0.07s

$ python bench_kg.py --check
[OK] Dữ liệu: 18 điều luật, 20 bài báo
[OK] KG-1 link_entity
[OK] Neo4j kết nối được
[provider] chat = openai:gpt-4o-mini | embedding = openai:text-embedding-3-small
[OK] KG-2 build_graph: 147 node / 370 cạnh, đường xuyên 2 KB dài 2 cạnh
[OK] KG-3 context: 12 dữ kiện, có Điều 251
[OK] KG-4 GraphRAGAgent.answer
[OK] Chi phí check: 1 lần gọi LLM, $0.00064. Graph nhỏ (luật + 1 bài) vẫn còn trong Neo4j để bạn xem; chạy --judge để dựng graph đầy đủ.
```

Ảnh Neo4j: `report/img/kg_count.png`, `report/img/kg_cross_kb.png`, `report/img/kg_my_case.png`.
Người đã chọn cho `kg_my_case.png`: **Cái Quang Huy**. Truy vấn Q-D được mở rộng theo ontology riêng để thấy cả khoản luật được chọn theo ngưỡng khối lượng:

```cypher
MATCH p=(:Person {name:'Cái Quang Huy'})-[:INVOLVED_IN]->(k:Case)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(a:Article)
OPTIONAL MATCH q=(k)-[i:INVOLVES]->(:Substance)<-[t:THRESHOLD]-(:Clause)<-[:HAS_CLAUSE]-(a)
WHERE t.min_g <= i.grams AND (t.max_g IS NULL OR i.grams < t.max_g)
OPTIONAL MATCH r=(k)-[:LOCATED_IN]->()
RETURN p, q, r;
```

## Vấn đề gặp phải (không tính điểm)

- `docker run … neo4j:5` lần đầu bị treo khoảng 15 phút khi kéo image (không có tiến triển). Dừng lệnh rồi chạy lại `docker pull neo4j:5` thì tải xong trong khoảng 1 phút, sau đó `docker run` bình thường.
- Số liệu phần tin tức (số `Person`, tên `Case`) thay đổi nhẹ giữa các lần dựng graph vì trích xuất bằng LLM. Mọi số liệu trong báo cáo lấy từ lần chạy `--judge` cuối cùng (197 node / 456 cạnh).
