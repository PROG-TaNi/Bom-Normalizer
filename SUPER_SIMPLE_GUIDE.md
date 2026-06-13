# 🎮 Super Simple Guide - Like You're 5 Years Old!

## 🌐 Step 1: Open the Website

Open your web browser (Chrome, Firefox, etc.) and go to:
```
http://localhost:3001
```

You'll see a dark blue screen with a table full of messy data!

---

## 🎯 What You're Looking At

Imagine you have a messy toy box where toys have different names:
- Some say "LEGO"
- Some say "Lego"
- Some say "L.E.G.O"

But they're all the SAME toy! Your job is to clean up the names so they all say "LEGO".

The website shows you a table with messy electronics parts that need cleaning!

---

## 🚀 Step 2: Choose Your Difficulty

At the top right, you'll see three buttons:

### 🟢 EASY (Start Here!)
- Only 10 rows to clean
- Only fix company names
- Perfect for learning!

### 🟡 MEDIUM
- 50 rows to clean
- Fix company names, values, and packages
- A bit harder!

### 🔴 HARD
- 100 rows to clean
- Fix everything + find duplicates
- Super challenging!

**👉 Click the GREEN "EASY" button to start!**

---

## 🎬 Step 3: Start the Game

Click the big **"Reset Episode"** button (green button on the right).

Now you'll see a table with 10 rows of messy data!

---

## 🤖 THE MAGIC BUTTON: Auto-Normalize with AI

### What Does It Do?

See that big shiny button that says **"⚡ Auto-Normalize with AI"**?

This is like having a super smart robot helper! When you click it:

1. **The AI Reads All the Messy Data** 🤓
   - It looks at names like "TI", "T.I.", "Texas Inst."
   - It knows they all mean "Texas Instruments"

2. **The AI Fixes Everything Automatically** ✨
   - It changes "TI" → "Texas Instruments"
   - It changes "10K" → "10000"
   - It changes "SOT23" → "SOT-23"
   - All by itself!

3. **You Watch It Work** 👀
   - You'll see messages like "Step 1: Normalizing vendor..."
   - The table updates in real-time
   - It's like watching a robot clean your room!

4. **Done!** 🎉
   - All the messy data is now clean
   - You get a score showing how well it did
   - You can download the clean data

### 🎯 When to Use It?

**Use the AI button when:**
- ✅ You want to see how AI cleans data
- ✅ You have lots of rows and don't want to do it manually
- ✅ You want to learn what "correct" looks like
- ✅ You're lazy (it's okay, we all are sometimes! 😄)

**Do it manually when:**
- ✅ You want to learn how normalization works
- ✅ You want to practice
- ✅ You want to compete for a high score
- ✅ You want to understand each step

---

## 🎮 Step 4: Try It Yourself (Manual Way)

If you want to clean data yourself (without AI), here's how:

### Look at the Table

You'll see columns like:
- **Vendor Name** - Company that makes the part (messy!)
- **Part Number** - The part's ID number
- **Value** - What the part does (like "10K" for resistance)
- **Package** - How the part looks (like "SOT-23")
- **Quantity** - How many you need

### On the Left Side - Action Builder

This is your control panel! Here's what each button does:

1. **normalize_vendor** - Fix a company name
   - Example: Change "TI" to "Texas Instruments"

2. **normalize_value** - Fix a value
   - Example: Change "10K" to "10000"

3. **normalize_package** - Fix a package code
   - Example: Change "SOT23" to "SOT-23"

4. **submit** - Finish and get your score!

### How to Fix One Row:

1. **Pick a row** - Look at row 1
2. **See what's wrong** - Maybe it says "TI" instead of "Texas Instruments"
3. **Choose action** - Select "normalize_vendor" from dropdown
4. **Enter row number** - Type "1"
5. **Enter correct value** - Type "Texas Instruments"
6. **Click "Execute Action"** - Watch it change!
7. **See your reward** - You get points for fixing it right!

---

## 📊 Understanding the Scores

### On the Left Panel:

**Episode Stats** shows:
- **Step Count** - How many actions you've taken
- **Max Steps** - How many actions you're allowed
- **Fields Remaining** - How many things still need fixing
- **Cumulative Reward** - Your total score

### Rewards:
- ✅ **Green numbers (+0.15)** - You did it right! Good job!
- ❌ **Red numbers (-0.05)** - Oops, that was wrong. Try again!

---

## 🎯 Complete Walkthrough - Easy Task

Let's do the EASY task together, step by step:

### 1. Click "EASY" button (top right)

### 2. Click "Reset Episode" (green button)
   - You now see 10 rows with messy vendor names

### 3. Option A: Use AI (The Easy Way)
   - Click **"⚡ Auto-Normalize with AI"**
   - Watch the magic happen!
   - Wait for "✅ AI normalization complete!"
   - See your score!

### 3. Option B: Do It Yourself (The Learning Way)
   - Look at Row 1 - Maybe it says "TI"
   - In Action Builder (left side):
     - Select "normalize_vendor"
     - Row ID: 1
     - New Value: "Texas Instruments"
     - Click "Execute Action"
   - Repeat for all 10 rows
   - When done, select "submit" and click "Execute Action"
   - See your score!

---

## 🎨 What Each Color Means

### In the Table:
- **Gray rows** - Not touched yet (status: RAW)
- **Green rows** - You fixed them! (status: NORMALIZED)
- **Yellow rows** - Flagged as weird (status: FLAGGED)
- **Red rows** - Duplicates (status: MERGED)

### Buttons:
- **Green buttons** - Start/Reset
- **Blue buttons** - Upload/Download
- **Emerald/Shiny button** - AI Magic!

---

## 🤔 Common Questions

### Q: What if I make a mistake?
**A:** No problem! You can use the "undo_last" action to go back!

### Q: Can I upload my own Excel file?
**A:** Yes! Click "Upload Excel" button and choose your file!

### Q: What's the difference between AI and manual?
**A:** 
- **AI** = Robot does it for you (fast, automatic)
- **Manual** = You do it yourself (slow, but you learn)

### Q: How do I know what the correct value should be?
**A:** 
- Use the "inspect_row" action to get a hint!
- Or click the AI button to see what it does
- Or check the guides in the documentation

### Q: Can I download the cleaned data?
**A:** Yes! After you finish (or AI finishes), click "Download" button!

---

## 🎯 Quick Reference - Common Fixes

### Vendor Names (Company Names):
```
"TI" → "Texas Instruments"
"Murata" → "Murata Manufacturing"
"ST" → "STMicroelectronics"
"Vishay" → "Vishay Intertechnology"
"ON Semi" → "ON Semiconductor"
```

### Values (Component Values):
```
"10K" → "10000"
"100nF" → "100e-9"
"10uF" → "10e-6"
"1M" → "1000000"
```

### Packages (How Parts Look):
```
"SOT23" → "SOT-23"
"0402M" → "0402"
"DIP14" → "DIP-14"
"SOIC8" → "SOIC-8"
```

---

## 🎉 Summary - The Simplest Way

### Want to see AI magic? (Recommended for first time!)

1. Open http://localhost:3001
2. Click "EASY"
3. Click "Reset Episode"
4. Click **"⚡ Auto-Normalize with AI"**
5. Watch it work!
6. See your score!
7. Click "Download" to save the clean data!

### Want to learn by doing?

1. Open http://localhost:3001
2. Click "EASY"
3. Click "Reset Episode"
4. Look at the messy data
5. Use Action Builder to fix each row
6. Click "submit" when done
7. See your score!

---

## 🚀 You're Ready!

The website is like a video game where you clean messy data!

- **Easy Mode** = Practice and learn
- **AI Button** = Let the robot do it
- **Manual Mode** = Do it yourself and learn

**Have fun cleaning data! 🎮✨**

---

*Remember: There's no wrong way to use it! Try the AI button first to see how it works, then try doing it manually to learn!*
