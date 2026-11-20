# LearnSphere user guide

LearnSphere is a high-school management system. The menus shown to each person
depend on their role and school assignment.

## Getting started for everyone

### Sign in

1. Open the LearnSphere sign-in page.
2. Enter the email address registered on your account.
3. Enter your password and select **Sign in**.
4. Use the dashboard and the left-hand menu to open your available features.

Usernames are internal account values; the normal sign-in form uses email.
Email addresses and phone numbers must be unique.

### Account settings

All signed-in users can:

- Open **Profile** to view their account information.
- Open **Account Settings** to update permitted personal details.
- Open **Change Password** to set a new password.
- Use the language selector at the bottom of the menu.
- Select **Logout** when finished, especially on a shared computer.

Success, warning, and error messages appear at the top of the page after an
action. If a page does not show a menu item, that feature is not assigned to
the current role.

### Academic time structure

- A **session** is the school's academic year or school cycle, such as
  `2026/2027`. It groups the school's academic records.
- A **quarter** is a reporting period inside the current session: Q1, Q2, Q3,
  or Q4.
- The administrator selects the current session and current quarter. Marks,
  assessments, attendance, and reports use that context.

## Platform administrator

This is a superuser without a school assignment. The platform administrator
manages the LearnSphere school accounts rather than daily teaching activity.

### Main tasks

1. Open **Registered Schools** from the menu.
2. Review active, trial, suspended, overdue, and revenue summaries.
3. Select **Register New School** or use the Django administration area to add
   a school account.
4. Open a school to update its billing/status information.
5. Suspend, reactivate, or suspend overdue schools as appropriate.

Use the platform dashboard for school-level operations. Do not use the
platform account to enter marks for a school unless it has intentionally been
assigned to that school.

## School administrator or principal

This is a superuser assigned to a school. This role prepares the school for
the academic year and oversees its records.

### Recommended setup order

1. **Sessions**: create the academic session and mark the correct one as
   current.
2. **Current Quarter**: choose Q1, Q2, Q3, or Q4 for reporting.
3. **Classes**: create the school's forms/classes and assign levels.
4. **Subjects**: create subjects and attach them to the appropriate classes.
5. **Teachers**: add teacher accounts with unique email and phone details.
6. **Students**: add student accounts and assign each student to a class.
7. **Parents**: create parent records and link parents to their children.
8. **Course allocations**: allocate subjects to the teachers responsible for
   them.
9. **Timetable**: add or auto-generate timetable entries and review them by
   class.

### Daily and reporting tasks

- Use **Attendance** or **Mark Entry** to review school records.
- Use **Exams** to schedule and manage formal exams.
- Use **School Fees** and **Bulk Fee Add** to create student fee records and
  record payments.
- Use **Finance Dashboard**, **Income**, and **Expenses** to track school
  finances.
- Use **Parents** to review parent links and **Teacher Profiles** to inspect
  teacher records.
- Use **Current Quarter** before producing reports for a new reporting period.

### Grading configuration

The school grading configuration controls the contribution of assignment,
mid-exam, quiz, attendance, and final-exam marks. Quizzes and tests may be
available without contributing to the final grade: set their grading weight to
`0` when they are formative only. Set a positive quiz weight when quiz results
should contribute. The configured weights are used when total marks and grade
reports are calculated.

Before publishing results, confirm that the weights are intentional and that
the current quarter is correct.

## Teacher

Teachers see subjects allocated to them by the school administrator.

### Teaching workflow

1. Open **My Courses** and select a subject.
2. Review the class and enrolled students.
3. Upload course documents or video resources when needed.
4. Create quizzes/tests or physical tests/assignments for the subject.
5. Add questions and configure the assessment.
6. Open **Ready Quizzes & Tests** or **Complete Exams** to review attempts
   and mark them where required.
7. Use **Manage Score** to enter assignment, mid-exam, attendance, or final
   exam marks for the correct quarter.
8. Use **Attendance** to record daily class attendance.
9. Review the saved marks before the administrator publishes or relies on the
   reports.

Teachers can manage only the subjects allocated to them. If a subject or
student is missing, contact the school administrator rather than creating a
second account or duplicate contact details.

## Student

### Student workflow

1. Open **My Courses** to view registered subjects and course resources.
2. Use **Elective Subjects** to add or remove available electives when the
   school has enabled them.
3. Open **Ready Quizzes & Tests** to see assessments available to you.
4. Select an assessment, read its instructions, and submit answers before the
   allowed attempt ends.
5. Use **Quiz Progress** to review quiz activity and previous results.
6. Use **Assessment Results** for assessment outcomes.
7. Use **Grade Results** for quarter and session grade reports.
8. Use **Profile** and **Change Password** to keep the account details safe.

Course registration and dropping are subject to the school's rules and active
session. If a course is not available, contact the school office.

## Parent or guardian

Parents use **Parent Portal** to view children linked to their account.

### Parent workflow

1. Open **Parent Portal** after signing in.
2. Select a child to view class and school information.
3. Open **Grade Reports** to review the child's academic results.
4. Open **Fees** to view fee records and payment status.
5. Open **Announcements** for school news and notices.
6. Return to the dashboard to switch between children.

Parents can see only children linked to their own parent record and school.
Ask the school administrator to correct a missing or incorrect child link.

## Account recovery and common problems

### Forgotten password

Use **Forgot password** on the sign-in page and follow the SMS reset process.
The phone number must match the number stored on the account. If no SMS is
received, ask a school administrator to verify the phone number and reset the
password through the administrator command or account workflow.

### “Invalid email or password”

Confirm that:

- the email is the one registered on the account, not the internal username;
- the account is active;
- the password is entered correctly; and
- the account belongs to the expected school.

### Missing menu item or access denied

Menus are role-based. A teacher cannot manage another teacher's subject, a
student cannot enter marks, and a parent cannot view an unrelated student's
records. Ask the school administrator to correct the account role, school, or
class assignment.

### Marks or report look incorrect

Ask the teacher to confirm the marks and the administrator to confirm the
current quarter and grading weights. A quiz/test with a grading weight of zero
is recorded for learning and assessment history but does not change the final
grade.

## Privacy and safe use

- Never share a password or SMS reset link.
- Sign out on shared devices.
- Do not download or forward student reports unless authorized.
- Report an incorrect student, parent, class, or grade record to the school
  administrator promptly.
