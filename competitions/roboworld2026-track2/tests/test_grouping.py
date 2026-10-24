import unittest

from havln_tools import group_by_path


class GroupingTests(unittest.TestCase):
    def test_groups_three_instructions_per_path(self):
        eps = []
        for traj in ("10", "11"):
            for k in range(3):
                eps.append({"episode_id": f"{traj}{k}", "trajectory_id": traj, "scene_id": "mp3d/x/x.glb"})
        g = group_by_path(eps)
        self.assertEqual(sorted(len(v) for v in g.values()), [3, 3])

    def test_falls_back_to_start_pose(self):
        eps = [{"episode_id": "1", "scene_id": "s", "start_position": [1.0001, 0.2, -3.0], "start_rotation": [0, 0.7071, 0, 0.7071]},
               {"episode_id": "2", "scene_id": "s", "start_position": [1.0004, 0.2, -3.0], "start_rotation": [0, 0.7071, 0, 0.7071]},
               {"episode_id": "3", "scene_id": "s", "start_position": [4.0, 0.2, -3.0], "start_rotation": [0, 0.7071, 0, 0.7071]}]
        g = group_by_path(eps)
        self.assertEqual(sorted(len(v) for v in g.values()), [1, 2])


if __name__ == "__main__":
    unittest.main()
