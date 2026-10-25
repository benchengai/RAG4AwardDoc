# Notes

Two kinds of entries live here. **Project issues** are things that broke or misled the results, written in English so the good ones can move into the README. **Concept questions** are things I didn't understand while learning, in any language.

Newest first. Two minutes per entry, written when it happens.

---

## Project issues

### 2026-10-25 Test set did not say "ordinary hours", and Q33 asked for ordinary hours that can't exist

**Symptom** Reviewing all 40 questions against the award, 13 Saturday, Sunday and public holiday questions didn't say "ordinary hours". Ordinary hours only run 7am–6pm on a Saturday and 9am–6pm on a Sunday (clause 15.1), and work outside that is overtime. So a casual adult Level 2 working on a Saturday evening gets the 175% overtime rate, not the expected 150%. Q33 asked for 4 hours of ordinary work after 6pm on a weekday, but weekday ordinary hours end at 9pm unless the store trades later. The fourth hour would be overtime, making the answer $154.61 instead of $147.24.

**Cause** The expected answers come from the penalty table (Table 12), whose rows only cover ordinary hours. The questions didn't carry that condition over, and when hours count as ordinary is set in a different clause, the span-of-hours table.

**Fix** Added "working ordinary hours" or "of ordinary work" to the 13 questions, and changed Q33 to 3 hours ($110.43). Re-ran v1 for about US$0.005. Answer accuracy didn't change, citations went from 7/36 to 8/36, and value in context went from 20/28 to 19/28. The 40 questions are frozen from here, so every later version is compared on the same set.

**Lesson** The table an answer comes from isn't the only clause that decides it. A condition set somewhere else, like the span of hours, quietly changes which row applies. Also, small wording changes move dense retrieval: the 26 untouched questions retrieved exactly the same chunks, but 10 of the 14 reworded ones retrieved different chunks after gaining three or four words.

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
