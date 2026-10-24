"""Reference aggregator mirroring the RoboWorld 2026 Track 2 (HA-VLN) Score.

Per-episode inputs (from a Habitat 0.1.7 replay in the organizer image):
  count    = info['collisions']['count']   (# steps with previous_step_collided)
  success  = info['success']               (STOP called and distance_to_goal < 3.0)
  distance = info['distance_to_goal']      (final distance; HA-VLN override = 3-D Euclidean)
Sources: HASimulator/metric.py L12-17; initial toolkit README (track2 commit 2daf3dd) L336-350;
CMA reference numbers reproduced exactly with these denominators (see A4 findings).
"""
import json, math

H_NOT_INFLUENCED = {'train': 1615, 'val_seen': 96, 'val_unseen': 246, 'test': 549}   # metric.py L12
N_EPISODES = {'train': 10819, 'val_seen': 778, 'val_unseen': 1839, 'test': 3408}

def per_episode(count, success, distance, collision_num):
    e = max(0, int(count) - int(collision_num))          # adjusted collisions (TCR_ep)
    return dict(TCR=e, CR=min(e, 1), SR=float(success) * (1 if e == 0 else 0), NE=float(distance))

def aggregate(split, rows, collision_num):
    """rows: {episode_id(str): {'count':int,'success':0/1,'distance':float}} covering ALL episodes."""
    L = N_EPISODES[split]
    assert len(rows) == L and set(rows) == set(collision_num), 'coverage must be exact'
    beta_L = L - H_NOT_INFLUENCED[split]                  # = beta * L, beta = 1 - H/L
    per = {ep: per_episode(r['count'], r['success'], r['distance'], collision_num[ep]) for ep, r in rows.items()}
    SR  = sum(p['SR'] for p in per.values()) / L
    NE  = sum(p['NE'] for p in per.values()) / L
    TCR = sum(p['TCR'] for p in per.values()) / L
    CR  = sum(p['CR'] for p in per.values()) / beta_L    # NOTE: numerator over ALL episodes; CR can exceed 1
    nav = 0.80 * SR + 0.20 * 3.0 / (3.0 + NE)
    soc = 0.75 * (1.0 - CR) + 0.25 / (1.0 + TCR)
    score = 100.0 * nav * (0.70 + 0.30 * soc)
    return dict(SR=SR, NE=NE, CR=CR, TCR=TCR, Navigation=nav, Social=soc, Score=score, per_episode=per)

def rank_key(m):
    """Higher Score first; ties: higher SR, lower NE, lower CR, lower TCR (then earlier submission)."""
    return (-m['Score'], -m['SR'], m['NE'], m['CR'], m['TCR'])

if __name__ == '__main__':
    # Self-test: synthetic rows with the exact integer totals recovered for the CMA val_seen reference
    # (SR 140/778, CR 425/682, TCR 10679/778, NE 6.2232250) must give Score 16.509450.
    L = 778
    cn = {str(i): 0 for i in range(1, L + 1)}
    rows = {}
    tcr_left = 10679
    for i in range(1, L + 1):
        ep = str(i)
        if i <= 140:   rows[ep] = dict(count=0, success=1, distance=0.0)
        elif i <= 565: # 425 colliding episodes
            c = tcr_left // (566 - i); tcr_left -= c
            rows[ep] = dict(count=c, success=0, distance=0.0)
        else:          rows[ep] = dict(count=0, success=0, distance=0.0)
    tot = 6.2232250 * L
    for ep in rows: rows[ep]['distance'] = tot / L
    m = aggregate('val_seen', rows, cn)
    print({k: round(v, 7) for k, v in m.items() if k != 'per_episode'})
    assert abs(m['Score'] - 16.509450) < 1e-6, m['Score']
    print('self-test OK')
