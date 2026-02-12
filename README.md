# Recruiter Scorecard MVP Demo - v2.0
## Role-Centric Dashboard with Partnership Visibility

A working prototype that shows hiring performance at the **role level**, making it easy to see which recruiter + hiring manager partnerships are working well.

## 🎯 What's Different in V2

### Key Innovation: **Role-Level Visibility**
Instead of just showing individual recruiter or HM scores, this version shows:
- Each open role as a single row
- Both the recruiter AND hiring manager assigned
- Individual scores for each person
- **Combined partnership score** showing how well they're working together
- Action items specific to that role

This makes it immediately clear:
- Which roles are stuck and why
- Which partnerships are high-performing
- Where to focus coaching efforts

## 🚀 Quick Start Options

### Option 1: HTML Demo (FASTEST - 30 seconds)
1. Download `dashboard_v2.html`
2. Double-click to open in your browser
3. That's it!

**Perfect for:** Quick demos, sales presentations

### Option 2: Full Streamlit App (Customizable)
1. Install Python (3.9+)
2. Run these commands:
```bash
cd path/to/demo/folder
pip install -r requirements.txt
python generate_sample_data.py
streamlit run app.py
```

**Perfect for:** Custom data, client pilots, detailed exploration

## 📊 What You're Looking At

### Main Dashboard View
The role-centric table shows:

| Column | What It Shows | Why It Matters |
|--------|--------------|----------------|
| **Role** | Job title | What position is open |
| **Department** | Team/function | Where bottlenecks are by team |
| **Recruiter** | Name | Who's sourcing/screening |
| **Rec. Score** | 0-100 score | How well recruiter is performing |
| **Hiring Manager** | Name | Who's making hiring decisions |
| **Mgr. Score** | 0-100 score | How responsive/engaged HM is |
| **Combined Score** | Weighted average | Overall health of this hire |
| **Open Since** | Days | Urgency indicator |
| **Action Items** | Specific issues | What's blocking progress |

### Top Metrics Bar
- **Team Score:** Overall average across all roles
- **Open Roles:** Total count
- **Avg Recruiter/Manager Scores:** Team-wide performance
- **Avg Time to Feedback:** How long feedback takes
- **Avg Stage Time:** How long candidates sit in stages

### Color Coding
- 🟢 **Green (70-100):** Performing well
- 🟡 **Orange (50-69):** Needs attention
- 🔴 **Red (0-49):** Critical issues

## 🎤 Demo Script (5 Minutes)

### Opening (30 sec)
"Most companies track time-to-hire and offer acceptance rates, but they don't know *why* hiring is slow until it's too late. This dashboard shows you exactly where each role is stuck and who's responsible."

### Show the Table (2 min)
1. **Point to a high-scoring role:**
   - "Look at this Software Engineer role - combined score of 89. Charlie the recruiter scored 90, Dana the hiring manager scored 88. They're moving fast together."

2. **Point to a struggling role:**
   - "But here's Sales Associate - score of 68. The recruiter Emily is at 65, manager Frank at 70. Neither is terrible individually, but together they're mediocre. Look at the action items: '2 feedback overdue, 3 stages stalled'. They need coaching."

3. **Point to a critical role:**
   - "And this Ops Analyst role? It's been open 30 days with a score of 67. Karen the hiring manager is at 60 - that's the bottleneck. She has feedback overdue. This role needs intervention."

### Show Filters (1 min)
- Filter by department: "You can drill into just Engineering or just Sales"
- Sort by critical issues: "Or sort to see your most urgent problems first"
- Show insights: "The dashboard automatically flags your top 5 critical roles"

### Top Metrics Context (1 min)
- "Your team average is 76 - that's decent but not great"
- "Average feedback time is 52 hours - you're violating your 48-hour SLA"
- "This tells you exactly where to focus: Get hiring managers to submit feedback faster"

### Close (30 sec)
"This updates automatically every two weeks as you close roles and open new ones. You can export reports, set up alerts, and track improvement over time. The goal is to make every hire as efficient as your best partnerships."

## 💡 Why This Works for Sales

### It Solves Real Problems
1. **Transparency:** Everyone can see their scores
2. **Accountability:** Both recruiters AND hiring managers are measured
3. **Actionable:** Specific violations, not vague metrics
4. **Fair:** Based on SLAs they already agreed to

### It Addresses Common Objections

**"How is this different from our ATS reports?"**
→ "Your ATS shows you time-to-fill. This shows you *why* it's slow and *who's* causing delays."

**"Our team won't like being scored"**
→ "This isn't about blame - it's about visibility. Your best performers will shine, and struggling people get clear coaching targets."

**"Can we customize the SLAs?"**
→ "100%. Every threshold is configurable. If you want 24 hours instead of 48 for feedback, we adjust it."

**"What if someone games the system?"**
→ "Scores are based on actual timestamps from your ATS. We flag anomalies. Plus, the combined score means they can't succeed alone - partnerships matter."

## 🔧 Customization Examples

### Change the Team Score Display
The HTML file shows a big orange "76" circle. To customize:

1. Open `dashboard_v2.html` in a text editor
2. Find line ~70: `<div class="team-score-circle">76</div>`
3. Change the number
4. To change the color, find `.team-score-circle` in the CSS (line ~40) and change `background: #f97316;`

### Add Your Company Logo
1. Open `dashboard_v2.html`
2. Find line ~60 (the header section)
3. Add: `<img src="your-logo.png" style="height: 30px;">`
4. Save your logo in the same folder

### Add More Roles
1. Open `dashboard_v2.html`
2. Scroll to line ~145: `const rolesData = [`
3. Copy an existing role object and modify the values
4. Save and refresh

## 📈 What Comes After the Demo

If the prospect is interested, here's the conversation flow:

### Discovery Questions
1. **"Which ATS do you use?"** (Workday, Greenhouse, Lever, etc.)
2. **"How many roles do you typically have open?"**
3. **"What are your current SLA expectations?"** (or "What *should* they be?")
4. **"Who would be the main users?"** (Head of TA, VPs, recruiters?)

### Pilot Proposal
- 2-week pilot with their real data
- 3-5 recruiters + their hiring managers
- One department to start (usually Engineering or Sales)
- Weekly check-ins to adjust thresholds

### Pricing Discovery
- Per-recruiter pricing ($X/recruiter/month)
- Or per-role pricing ($Y/open role/month)
- Enterprise tier for 50+ recruiters
- Implementation + training included

## 📦 Files Included

### Core Demo Files
- `dashboard_v2.html` - **START HERE** - Complete standalone demo
- `QUICK_START.md` - Non-technical setup guide
- `README.md` - This file

### Python/Streamlit Version (Optional)
- `app.py` - Full Streamlit dashboard with role view
- `scoring_engine.py` - Scoring calculation logic
- `generate_sample_data.py` - Creates realistic fake data
- `sample_ats_export.csv` - Pre-generated sample data
- `requirements.txt` - Python dependencies

### Legacy Files (V1)
- `demo.html` - Original individual-focused dashboard
- Still works, just different approach

## 🆘 Troubleshooting

**HTML dashboard won't open:**
- Right-click → Open With → Chrome/Firefox/Safari
- Make sure you're not viewing the code in a text editor

**Python version: "Module not found" error:**
```bash
pip install --upgrade -r requirements.txt
```

**Scores don't match between HTML and Python:**
- HTML uses static sample data for speed
- Python calculates dynamically from the CSV
- They use the same logic, just different datasets

## 🎯 Key Talking Points

### For Talent Acquisition Leaders
- "Finally see which hiring managers are actually the bottleneck"
- "Data-driven coaching instead of gut feel"
- "Prove ROI when you speed up hiring"

### For HR Leaders
- "Align with business on clear SLAs"
- "Objective performance data for reviews"
- "Proactive rather than reactive"

### For Executives
- "Hiring velocity directly impacts revenue"
- "This shows you exactly where to invest in training"
- "Benchmark against industry standards"

## 📊 Sample Numbers to Know

From the demo data:
- **Best Partnership:** Software Engineer (Charlie + Dana = 89)
- **Needs Help:** Sales Associate (Emily + Frank = 68)
- **Critical:** Ops Analyst (David + Karen = 67, 30 days open)
- **Team Average:** 76/100
- **Most Common Issue:** Feedback delays (52 hour average vs 48 hour SLA)

## 🚀 Next Steps

1. **Try the demo:** Open `dashboard_v2.html`
2. **Practice the pitch:** Use the 5-minute script above
3. **Customize:** Add your branding, adjust the data
4. **Book demos:** Show this to 3-5 prospects
5. **Iterate:** Based on their feedback, we adjust

Ready to start demoing? Just open the HTML file! 🎉

---

**Questions?** This is designed to be self-service, but if you get stuck:
- Check `QUICK_START.md` for basics
- Email [your contact]
- The HTML demo requires zero setup - that's your safest bet
