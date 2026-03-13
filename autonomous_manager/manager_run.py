from autonomous_engine import autonomous_decision

print("\nAutonomous Platform Manager\n")

actions = autonomous_decision()

for a in actions:
    print("AI Action:", a)
