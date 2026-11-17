# Validation — Lab 02 BJT DC Bias Web App

เอกสารนี้แสดงการตรวจสอบผลลัพธ์อย่างเป็นอิสระ (ไม่ได้ใช้โค้ดของเว็บ),
การเทียบกับผลจาก engine/tests, สถานะ warning และหลักฐาน acceptance A1–A7

- **วันที่ตรวจ:** 2026-11-10
- **Environment:** Windows, Python 3.15.2, Flask 3.1.3
- **ชุดทดสอบ:** `python -m unittest discover -s tests -v`

---

## 1. Independent Calculation

### อินพุตอ้างอิง (ค่าตัวอย่างในเอกสาร)

| พารามิเตอร์ | ค่า | หน่วย SI |
|---|---|---|
| `VCC` | 12 | 12 V |
| `R1` | 100 | 100 000 Ω |
| `R2` | 22 | 22 000 Ω |
| `RC` | 2.2 | 2 200 Ω |
| `RE` | 1 | 1 000 Ω |
| `β` | 100 | – |
| `VBE` | 0.70 | 0.70 V |

### สมการที่ใช้

```
VTH = VCC · R2 / (R1 + R2)
RTH = R1 · R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β + 1) · RE)
IC  = β · IB
IE  = (β + 1) · IB
VE  = IE · RE
VB  = VE + VBE
VC  = VCC − IC · RC
VCE = VC − VE
```

### ขั้นคำนวณ

```
VTH = 12 × 22 000 / (100 000 + 22 000)
    = 264 000 / 122 000
    = 2.163934426229508 V

RTH = 100 000 × 22 000 / 122 000
    = 2 200 000 000 / 122 000
    = 18 032.78688524590 Ω
    = 18.03278688524590 kΩ

IB  = (2.163934426229508 − 0.70) / (18 032.78688524590 + 101 × 1 000)
    = 1.463934426229508 / (18 032.78688524590 + 101 000)
    = 1.463934426229508 / 119 032.78688524590
    = 12.29858146260846 × 10⁻⁶ A
    = 12.29858146260846 µA

IC  = 100 × 12.29858146260846 × 10⁻⁶
    = 1.229858146260846 × 10⁻³ A
    = 1.229858146260846 mA

IE  = 101 × 12.29858146260846 × 10⁻⁶
    = 1.242156727723454 × 10⁻³ A
    = 1.242156727723454 mA

VE  = 1.242156727723454 × 1 000
    = 1.242156727723454 V

VB  = 1.242156727723454 + 0.70
    = 1.942156727723454 V

VC  = 12 − 1.229858146260846 × 10⁻³ × 2 200
    = 12 − 2.705687921773861
    = 9.294312078226139 V

VCE = 9.294312078226139 − 1.242156727723454
    = 8.052155350502685 V
```

---

## 2. Cross-check: Independent vs Engine vs UI

| ปริมาณ | คำนวณอิสระ | `dc_bias.py` (test) | แสดงบนเว็บ |
|---|---|---|---|
| `VTH` | 2.163934426 V | 2.163934426 V | 2.16 V |
| `RTH` | 18.032786885 kΩ | 18.032786885 kΩ | 18.03 kΩ |
| `IB` | 12.298581 µmA | 12.298581 µmA | 12.3 µA |
| `IC` | 1.229858146 mA | 1.229858146 mA | 1.23 mA |
| `IE` | 1.242156728 mA | 1.242156728 mA | 1.24 mA |
| `VE` | 1.242156728 V | 1.242156728 V | 1.24 V |
| `VB` | 1.942156728 V | 1.942156728 V | 1.94 V |
| `VC` | 9.294312078 V | 9.294312078 V | 9.29 V |
| `VCE` | 8.052155351 V | 8.052155351 V | 8.05 V |

ผลตรงกันถึงระดับที่ test กำหนด (`places=9` สำหรับแรงดัน, `places=12` สำหรับกระแส)

**หลักฐาน:**

- `tests/test_dc_bias.py::test_reference_operating_point`
- `tests/test_web.py::test_post_valid` (ตรวจข้อความ `8.05`, `1.23`, `Active`)

---

## 3. Warning Scenarios

### 3.1 Cutoff — `R2 = 5 kΩ`

```
VTH = 12 × 5 000 / 105 000 = 0.5714285714 V
VTH ≤ VBE (0.5714 ≤ 0.70)  →  warning "cutoff"

IB = (0.5714285714 − 0.70) / (4 761.9048 + 101 000)
   = −1.2156686177 × 10⁻⁶ A   (ติดลบ → ไม่มีความหมายทางกายภาพ)
IC = 100 × IB = −0.1215668618 mA
```

แบบจำลองยังคำนวณต่อได้ แต่ผลติดลบแสดงว่า Forward-Active approximation
ใช้ไม่ได้ → UI แสดง warning **Cutoff** และไม่รายงานสถานะ Active

**หลักฐาน:** `test_cutoff_warning`, `test_post_cutoff_warning`

### 3.2 Near Saturation — `RC = 10 kΩ`

```
IC  = 1.229858146 mA  (ค่าเดิม เพราะ RC ไม่มีผลกับ IB)
VC  = 12 − 1.229858146 × 10⁻³ × 10 000
    = −0.2985814626 V
VCE = −0.2985814626 − 1.2421567277
    = −1.5407381903 V
VCE < 0.2 V  →  warning "near_saturation"
```

`VCE` ติดลบแปลว่า transistor ไม่สามารถอยู่ใน forward-active ด้วย `RC` ค่านี้
→ UI แสดง warning **Near Saturation**

**หลักฐาน:** `test_saturation_warning`, `test_post_saturation_warning`

---

## 4. Automated Test Result

```
python -m unittest discover -s tests -v
Ran 17 tests in 0.091s
OK
```

- Engineering tests: 10 (`tests/test_dc_bias.py`)
- Flask client tests: 7 (`tests/test_web.py`)
- Log เต็ม: [`docs/test-log.txt`](test-log.txt)

### 4.1 Independent Cross-check (Decimal, 40 digits)

ตรวจ `calculate_dc_bias()` เทียบกับ implementation อิสระที่ใช้ `decimal.Decimal`
(ความละเอียด 40 หลัก) โดยไม่ใช้โค้ดชุดเดียวกัน:

| การตรวจ | ผล |
|---|---|
| ค่าอ้างอิง 9 ปริมาณ | relative error สูงสุด **1.79 × 10⁻¹⁶** |
| สุ่ม 5,000 ชุดอินพุต × 9 ค่า | คลาดเคลื่อน > 1e-9: **0 รายการ** |
| Warning/region logic 2,000 เคส | ไม่ตรงกัน: **0 รายการ** |

การตรวจนี้ยืนยันว่าสมการใน `dc_bias.py` ตรงกับสมการอ้างอิงในเอกสาร §06
และ warning ถูกตัดสินจากเงื่อนไขเดียวกัน

### 4.2 หมายเหตุเรื่องค่าตัวเลขในภาพตัวอย่าง

ภาพหน้าจอตัวอย่างในเอกสาร Lab 02 ระบุชัดว่าเป็น **“ค่าประกอบภาพ”
ไม่ใช่คำตอบอ้างอิงหรือผลการจำลองที่ตรวจสอบแล้ว** ตัวเลขในภาพ
(เช่น `VB = 2.20 V`, `VCE = 7.20 V`) มาจากการประมาณอย่างหยาบ
โดยถือ `IC ≈ IE ≈ (VTH − VBE)/RE` และปัด `VTH` เป็น 2.20 V
ซึ่ง **ละเลย `RTH` และ base-current loading**

เมื่อใช้สมการครบตามเอกสาร §06 (`IB` มี `RTH + (β+1)RE` ในตัวส่วน)
จะได้ `VCE = 8.05 V` ตามที่แสดงใน §1–§2 ของเอกสารนี้
แอปนี้จึงยึดสมการในเอกสาร ไม่ยึดตัวเลขในภาพ

---

## 5. Acceptance Checklist A1–A7

| # | เกณฑ์ | หลักฐาน | สถานะ |
|---|---|---|---|
| A1 | `GET /` ตอบ HTTP 200 และมีฟอร์ม 7 ช่อง | `test_get_form` + `docs/screenshot.png` | ผ่าน |
| A2 | `POST /calculate` คำนวณจริง ไม่ hardcode | `test_post_valid` + ตรวจ `app.py` เรียก `calculate_dc_bias()` | ผ่าน |
| A3 | `VB, VE, VC, VCE, IC` ตรงคำนวณอิสระ | §2 + `test_reference_operating_point` | ผ่าน |
| A4 | `R ≤ 0`, `β ≤ 0`, non-numeric, non-finite → error ชัดเจน | `test_rejects_*`, `test_post_invalid_resistor`, `test_post_missing_field`, `test_post_nan_rejected` + ตรวจบนเบราว์เซอร์ | ผ่าน |
| A5 | Cutoff / Saturation warning | §3 + `test_*_warning` และ web tests | ผ่าน |
| A6 | ≥ 3 engineering tests + ≥ 1 Flask test | 10 + 7 tests, `docs/test-log.txt` | ผ่าน |
| A7 | Clone/install/run/test ตาม README ได้ | ทดสอบคำสั่งใน README บนเครื่องนี้ (§6) | ผ่าน |

---

## 6. Manual Browser Checks (2026-11-10)

| การทดสอบ | ผล |
|---|---|
| เปิด `http://127.0.0.1:5000/` | HTTP 200, ฟอร์มแสดงค่า default ครบ 7 ช่อง |
| กด Calculate ด้วยค่า default | แสดง `VB 1.94 V`, `VE 1.24 V`, `VC 9.29 V`, `VCE 8.05 V`, `IB 12.3 µA`, `IC 1.23 mA`, `IE 1.24 mA`, สถานะ Active |
| เปลี่ยน `R2 = 5` แล้ว Calculate | แสดง warning Cutoff และสถานะ Cutoff |
| เปลี่ยน `R1 = 0` แล้ว Calculate | แสดง error “R1, R2, RC, RE ต้องมากกว่า 0”, HTTP 200 |
| ลบ `R1` แล้ว submit | แสดง error “กรุณากรอกค่าตัวเลขให้ครบทุกช่อง”, HTTP 200 |
| ส่ง `vcc=nan` ผ่าน HTTP | แสดง error “ค่าอินพุตต้องเป็นจำนวนจำกัด …”, HTTP 200, ไม่มีตารางผลลัพธ์ |
| ย่อหน้าต่าง/จอแคบ | layout stack เป็นคอลัมน์เดียวโดยไม่ล้น |

---

## 7. Reproducibility

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run --debug
python -m unittest discover -s tests -v
```

เวอร์ชันที่ใช้ตรวจ: Python 3.15.2, Flask 3.1.3 (ดู `requirements.txt`)

---

## 8. Notes and Assumptions

- `VCE < 0.2 V` เป็น **heuristic assumption** จากภาพตัวอย่างในเอกสาร
  ไม่ใช่ค่าที่เอกสาร Lab 02 กำหนด และไม่กระทบการคำนวณ
- อินพุตที่ไม่ใช่จำนวนจำกัด (`NaN`, `±Infinity`) และอินพุตที่ล้นจนคำนวณไม่ได้
  ถูกปฏิเสธด้วย `ValueError` เพื่อไม่ให้หน้าเว็บแสดง `nan` เป็นผลลัพธ์
- แบบจำลองไม่ clamp ค่ากระแส/แรงดันเมื่อออกนอก forward-active
  จึงอาจได้ค่าติดลบ ซึ่งเป็นสัญญาณให้ผู้ใช้เห็นว่าแบบจำลองใช้ไม่ได้
- ไม่ได้จำลอง Early effect, อุณหภูมิ, series resistance หรือ load
- ไม่ใช่ SPICE simulator และไม่มี AC/transient analysis

---

## 9. Submission Record

- **Repository:** <https://github.com/b6827311-oss/BJT_DC_Bias_Web_App.git>
- **Branch:** `main` (upstream `origin/main`)
- **Commit SHA (latest code commit):** `b7e5977db02c46794d7ca71ed896512822073d08` (`b7e5977`)
  — `fix: reject non-finite inputs and show region check`
- **Commit history:**

  | SHA | ข้อความ |
  |---|---|
  | `f3c9366` | `feat: add BJT DC bias Flask web app with tests and docs` |
  | `f28156e` | `docs: record final commit SHA and evidence` |
  | `b7e5977` | `fix: reject non-finite inputs and show region check` |

- **สถานะ:** Push ผ่าน GitHub Desktop เมื่อ 2026-11-10
- **Screenshot:** [`docs/screenshot.png`](screenshot.png)
- **Test log:** [`docs/test-log.txt`](test-log.txt)
- **หมายเหตุ:** ไฟล์ `docs/validation.md` นี้ถูกปรับปรุงหลัง `b7e5977`
  ใน commit เอกสาร (`docs: record latest commit SHA and cross-check`)
  โดยไม่มีการเปลี่ยนแปลงโค้ดหรือผลการทดสอบ

---

## 10. Lab 03 (2026-11-17)

Lab 03 เพิ่ม **Fixed Bias** และ **Emitter Bias** ในแอปเดิม
โดยผลของ Divider (A1) ยังตรงกับ §1–§2 ของเอกสารนี้ทุกค่า

> Lab 03 ส่งใน repository ใหม่:
> <https://github.com/b6827311-oss/-ENG29_2121_Lab03_BJT_Bias_Web_App>
> (ลิงก์ใน §9 เป็นหลักฐานของ Lab 02 ใน repository เดิม)

- ตาราง A1–A5, ค่าอ้างอิงอิสระ (Decimal 50 หลัก), วิธีตรวจผ่าน Browser
  และข้อจำกัดของ Playwright MCP: [`lab03-acceptance.md`](lab03-acceptance.md)
- Test log: [`test-log-lab03.txt`](test-log-lab03.txt) — `Ran 17 tests ... OK`
- ภาพหน้าจอ: [`lab03-fixed-bias.jpeg`](lab03-fixed-bias.jpeg),
  [`lab03-emitter-bias.jpeg`](lab03-emitter-bias.jpeg),
  [`lab03-input-error.jpeg`](lab03-input-error.jpeg)
