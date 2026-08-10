

# Continuity — Prototype Usage Instructions

### 1. Start the application

Open Terminal:

```bash
cd ~/Downloads/continuity
source venv/bin/activate
streamlit run app.py
```

Open the URL shown in the terminal, usually:

```text
http://localhost:8501
```

---

### 2. Create the patient profile

Go to **Patient Profile**.

Enter the basic patient details and save the profile.

You only need to do this once for the demo.

---

### 3. Daily Check-in

Go to **Daily Check-in**.

Describe your current condition naturally in one sentence.

For example:

> My knee is hurting today and the pain is around 7 out of 10.

Click **Send**.

---

### 4. Review and confirm

The application will show you a summary of what you entered.

Check whether the information is correct.

Click **Confirm** to save the health event.

---

### 5. Check Health Timeline

Go to **Health Timeline**.

You should see your recently recorded health event along with previous events.

For a good demo, create a few different entries, for example:

**Day 1**

> My knee hurts today.

**Day 2**

> My knee is hurting again and it is worse after walking.

**Day 3**

> My leg feels sore today.

Then show how these events appear together in the timeline.

---

### 6. Demonstrate the main idea

```text
Patient
   ↓
Daily Check-in
   ↓
Describe symptoms naturally
   ↓
Review information
   ↓
Confirm
   ↓
Health Timeline
   ↓
Previous health history is preserved
```

### 🎤 One-line explanation 

> **"Continuity allows users to record their health experiences naturally and maintains a continuous, organized health history over time."**
