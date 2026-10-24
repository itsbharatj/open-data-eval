import unittest

from havln_tools import group_by_path


class GroupingTests(unittest.TestCase):
    def test_groups_three_instructions_per_path_by_trajectory_id(self):
        eps = []
        for traj in ("10", "11"):
            for k in range(3):
                eps.append({"episode_id": f"{traj}{k}", "trajectory_id": traj, "scene_id": "s", "start_position": [float(traj), 0.0, 0.0]})
        g = group_by_path(eps)
        self.assertEqual(sorted(len(v) for v in g.values()), [3, 3])

    def test_fallback_uses_id_blocks_not_start_pose(self):
        # Two trajectories share the same start pose (happens for 580 test trajectories) -> pose grouping would merge them.
        eps = [{"episode_id": str(i), "scene_id": "s", "start_position": [1.0, 0.0, 0.0]} for i in range(1, 7)]
        g = group_by_path(eps)
        self.assertEqual(sorted(g.values()), [["1", "2", "3"], ["4", "5", "6"]])

    def test_pose_consistency_check(self):
        eps = [{"episode_id": "1", "trajectory_id": "7", "start_position": [0, 0, 0]},
               {"episode_id": "2", "trajectory_id": "7", "start_position": [5, 0, 0]}]
        with self.assertRaises(ValueError):
            group_by_path(eps)


if __name__ == "__main__":
    unittest.main()
