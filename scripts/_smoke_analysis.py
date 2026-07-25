import sys, tempfile, shutil
sys.path.insert(0, r"D:\PythonProject\KP-AI-FENGSHUI")
from pathlib import Path
from core.analysis_storage import AnalysisStorage, AnalysisStorageError

SRC_DB = Path(r"D:\PythonProject\KP-AI-FENGSHUI\database\app.db")
TMP_DB = Path(tempfile.gettempdir()) / "smoke_analysis.db"
if TMP_DB.exists():
    TMP_DB.unlink()
shutil.copy(SRC_DB, TMP_DB)

# Construction touches app.db (empty tables, same as first launch) then redirect to temp
storage = AnalysisStorage()
storage.db_path = TMP_DB
storage._ensure_tables()

inp = {"name": "张三", "gender": "男", "year": 1990, "month": 5, "day": 20,
       "hour": 10, "minute": 30, "city": "上海", "question": "事业如何"}
chart = {"bazi": "xxx"}
ai = {"summary": "稳中有进"}

rid = storage.save_analysis_report("bazi", inp, chart, ai)
print("save_analysis_report ->", rid)
rep = storage.get_report_by_id(rid)
print("get_report_by_id keys:", sorted(rep.keys()))
print("input_data parsed:", isinstance(rep["input_data"], dict), "| birth_date:", rep["birth_date"])
print("ai_analysis parsed:", isinstance(rep["ai_analysis"], dict))

# pending -> update status/result
pid = storage.create_pending_report("meihua", {"name": "李四", "question": "感情"})
print("create_pending_report ->", pid)
print("update_report_status ->", storage.update_report_status(pid, "failed", "timeout"))
print("update_report_result ->", storage.update_report_result(pid, {"gua": "1"}, {"txt": "ok"}, "agnes-2.0", 123))

# logs
lid = storage.add_log(rid, "INFO", "start", {"k": 1})
print("add_log ->", lid)

# list / count / recent
print("get_reports_by_type(bazi) ->", len(storage.get_reports_by_type("bazi")))
print("get_report_count(all) ->", storage.get_report_count())
print("get_report_count(bazi) ->", storage.get_report_count("bazi"))
print("get_recent_reports(5) ->", len(storage.get_recent_reports(5)))
print("test_connection ->", storage.test_connection())

print("ANALYSIS STORAGE SMOKE PASSED")
