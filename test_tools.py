import json, shutil, sys, tempfile, unittest
from argparse import Namespace as N
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sp, power, econ


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); shutil.copytree(sp.ROOT / "projects/_template", self.tmp / "t")
        sp.PROJ = self.tmp; (self.tmp / "t/state/STATE.md").write_text("## Следующее действие\nx", encoding="utf-8")
    def test_fact_needs_source(self):
        with self.assertRaises(SystemExit): sp.cmd_ev(N(project="t", type="fact", statement="x", source="", locator="", conf="H", note=""))
    def test_check_and_revoke(self):
        sp.cmd_ev(N(project="t", type="assumption", statement="a", source="", locator="", conf="L", note=""))
        sp.cmd_ev(N(project="t", type="synthetic", statement="s", source="", locator="", conf="L", note=""))
        o = self.tmp / "t/outputs/a.md"; o.write_text("Есть спрос [S-01]\n", encoding="utf-8")
        e, _ = sp.run_check(self.tmp / "t"); self.assertTrue(any("синтетический" in x for x in e))
        o.write_text("Допущение [A-01]; ссылка [E-09]\n", encoding="utf-8")
        e, _ = sp.run_check(self.tmp / "t"); self.assertTrue(any("E-09" in x for x in e))
        o.write_text("Допущение [A-01]\n", encoding="utf-8"); self.assertEqual(sp.run_check(self.tmp / "t")[0], [])
        sp.cmd_revoke(N(project="t", id="A-01", reason="r", status="revoked")); self.assertTrue(sp.run_check(self.tmp / "t")[0])
    def test_power(self):
        self.assertAlmostEqual(power.n_per_arm(.12, .09), 1638, delta=3)
        self.assertLess(abs(power.mde(.12, 1638) - .03), .001)
    def test_econ_monotonic(self):
        P = json.load(open(sp.ROOT / "projects/family-connect-demo/model/params.json", encoding="utf-8"))
        r = {k: econ.run(P["common"], v) for k, v in P["scenarios"].items()}
        self.assertLess(r["low"]["gp_delta_mln"], r["base"]["gp_delta_mln"]); self.assertLess(r["base"]["gp_delta_mln"], r["high"]["gp_delta_mln"])


if __name__ == "__main__": unittest.main()
