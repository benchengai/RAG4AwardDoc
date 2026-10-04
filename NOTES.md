# Notes

Two kinds of entries live here. **Project issues** are things that broke or misled the results, written in English so the good ones can move into the README. **Concept questions** are things I didn't understand while learning, in any language.

Newest first. Two minutes per entry, written when it happens.

---

## Project issues

### 2026-10-04 My pay calculator was off by one cent for some junior rates

**Symptom** Cross-checking `paycalc.py` against every rate in the Fair Work pay guide gave 56 mismatches out of 522, all junior rates, all one or two cents. Example, a 16-year-old Level 2 came out at $14.23 instead of $14.22.

**Cause** I computed the junior hourly rate as adult hourly × junior percentage. Fair Work derives it from the weekly rate instead, weekly × percentage ÷ 38, then rounds. The two methods differ whenever the result lands near half a cent.

**Fix** The calculator now stores weekly rates and derives every hourly rate the same way the pay guide does. All 522 rates match, including casual overtime, which it previously refused.

**Lesson** My 24 unit tests all passed and the bug was still there, because none of them happened to hit a bad combination. Checking a tool against the whole authoritative table, not a handful of examples, is what caught it.

### 2026-10-04 Test set did not say whether the employee was a shiftworker

**Symptom** The pay guide has separate weekend and evening rates for shiftworkers. A casual adult Level 2 on Saturday is $42.68 if not a shiftworker and $49.79 if a shiftworker. My question only gave one of these as correct.

**Cause** I assumed the non-shiftworker case without saying so, the same mistake as the junior one two days earlier.

**Fix** Every question about a day or time rate now says "who is not a shiftworker" (25 questions). Overtime and weekly-rate questions were left alone because shiftwork doesn't change them. Q1 and Q12 now say "full-time", because a casual's minimum hourly rate is different.

**Lesson** An expected answer is only as good as the question is specific. Before trusting a test set, list every dimension the source table varies on (age, employment type, shiftwork, overtime) and check each question pins all of them.

### 2026-10-02 Test set did not say whether the employee was an adult

**Symptom** Q24 asked for a full-time Level 2 overtime rate without giving an age. Junior rates (clause 17.2) also apply to Levels 1–3, so the question had two valid answers.

**Cause** I wrote the expected answers assuming adult rates but never said so in the questions.

**Fix** Added "adult" to the 13 questions at Levels 1–3 that gave no age. Levels 4–8 have no junior rates.

**Lesson** A model that asked "how old is the employee" would have been marked wrong. Underspecified questions need their own category with the expected answer "clarify".

---

## Concept questions

### YYYY-MM-DD (question in one line)

**What confused me**

**What I understand now**

**Still unclear**
