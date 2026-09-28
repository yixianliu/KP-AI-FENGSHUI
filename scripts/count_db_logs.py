import os, glob
logs = sorted(glob.glob('logs/app_*.log'))
for f in logs[-5:]:
    print(os.path.basename(f))
    cnt = 0
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        for line in fp:
            if 'DB校验' in line:
                cnt += 1
    print('  DB校验 行数：', cnt)
