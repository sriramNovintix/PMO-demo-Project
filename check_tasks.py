"""
Quick script to check tasks in database
"""
from agent_service.database import db

print("=" * 60)
print("DATABASE STATUS CHECK")
print("=" * 60)

# Check employees
employees = db.get_all_employees()
print(f"\n👥 EMPLOYEES: {len(employees)}")
for emp in employees:
    print(f"  • {emp['name']} ({emp.get('email', 'no email')})")
    print(f"    Skills: {', '.join(emp.get('skills', [])[:5])}")

# Check all tasks
all_tasks = db.get_all_tasks()
print(f"\n📋 ALL TASKS: {len(all_tasks)}")

# Check unassigned tasks
unassigned = [t for t in all_tasks if not t.get("assigned_to")]
print(f"\n⚠️  UNASSIGNED TASKS: {len(unassigned)}")
for task in unassigned[:10]:  # Show first 10
    print(f"  • {task['title']}")
    print(f"    Hours: {task.get('estimated_hours', 0)}h")
    print(f"    Session: {task.get('session_id', 'N/A')}")
    print(f"    Status: {task.get('status', 'N/A')}")
    print()

# Check assigned tasks
assigned = [t for t in all_tasks if t.get("assigned_to")]
print(f"\n✅ ASSIGNED TASKS: {len(assigned)}")
for task in assigned[:5]:  # Show first 5
    print(f"  • {task['title']} → {task.get('assigned_to')}")

# Check candidates
candidates = db.get_all_candidates()
print(f"\n🎯 CANDIDATES: {len(candidates)}")
for cand in candidates:
    print(f"  • {cand['name']} ({cand.get('email', 'no email')})")

print("\n" + "=" * 60)
