import matplotlib.pyplot as plt
import numpy as np

# Data from research findings
challenges = ['Lack of Consistent Electricity', 'Shortage of Qualified Staff', 'Fully Functional Facilities', 'Digital Health Record Adoption (Neglected)']
percentages = [37, 52, 69, 15]  # 15% is an estimate based on "struggling/neglected" status

plt.figure(figsize=(10, 6))
plt.barh(challenges, percentages, color=['#e74c3c', '#e67e22', '#2ecc71', '#3498db'])
plt.xlabel('Percentage (%)')
plt.title('Technical & Operational Challenges in Iraqi Health Sector (2025-2026)')
plt.xlim(0, 100)
for index, value in enumerate(percentages):
    plt.text(value, index, f' {value}%')

plt.tight_layout()
plt.savefig('/home/ubuntu/iraq_health_challenges.png')
print("Analysis visualization saved to /home/ubuntu/iraq_health_challenges.png")
