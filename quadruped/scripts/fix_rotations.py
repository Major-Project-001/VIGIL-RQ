"""Fix leg mesh rotations in robot.urdf"""

with open('quadruped/urdf/robot.urdf', 'r') as f:
    lines = f.readlines()

# Left leg visual lines (FL + RL) - currently rpy="0 0 -1.5708"
left_lines = [122,129,136,143,178,185,219,226,257,444,451,458,465,495,502,532,539,569]
# Right leg visual lines (FR + RR) - currently rpy="0 0 1.5708"  
right_lines = [288,295,302,309,339,346,376,383,413,600,607,614,621,651,658,688,695,725]

count = 0
for i in left_lines:
    idx = i - 1
    old = 'rpy="0 0 -1.5708"'
    new = 'rpy="-1.5708 0 -1.5708"'
    if old in lines[idx]:
        lines[idx] = lines[idx].replace(old, new)
        count += 1

for i in right_lines:
    idx = i - 1
    old = 'rpy="0 0 1.5708"'
    new = 'rpy="-1.5708 0 1.5708"'
    if old in lines[idx]:
        lines[idx] = lines[idx].replace(old, new)
        count += 1

with open('quadruped/urdf/robot.urdf', 'w') as f:
    f.writelines(lines)

print(f"Updated {count} leg visual rotation lines")
