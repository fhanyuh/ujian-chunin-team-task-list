from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import json
import os

DATA_FILE = Path(os.getenv("DATA_FILE", "/var/lib/backend_data/tasks.json"))

TEAM_MEMBERS = {
    "Rafhan Mazaya Fathurrahman": "101012300238",
    "Zahra Talitha Putri": "101012300192",
    "Clara Novita Fitriani": "101012330008",
    "Rafif Riqullah Siregar": "101012300320",
}

VALID_PRIORITIES = ("High", "Medium", "Low")
VALID_STATUSES = ("Todo", "In Progress", "Done")

DEFAULT_SEED_TASKS = [
    {
        "title": "Menyusun jadwal kerja dan pembagian tugas mingguan",
        "assignee": "Rafhan Mazaya Fathurrahman",
        "nim": "101012300238",
        "priority": "High",
        "status": "Done",
        "category": "Perencanaan",
        "due_date": "2026-11-12",
        "notes": "Membagi target pekerjaan mingguan untuk setiap anggota kelompok.",
        "created_at": "2026-11-08T08:00:00+00:00",
    },
    {
        "title": "Menyiapkan draf materi dan poin bahasan diskusi",
        "assignee": "Zahra Talitha Putri",
        "nim": "101012300192",
        "priority": "High",
        "status": "In Progress",
        "category": "Dokumentasi",
        "due_date": "2026-11-13",
        "notes": "Merangkum referensi utama dan menyusun kerangka materi kelompok.",
        "created_at": "2026-11-08T09:15:00+00:00",
    },
    {
        "title": "Merapikan catatan hasil rapat dan daftar revisi",
        "assignee": "Clara Novita Fitriani",
        "nim": "101012330008",
        "priority": "Medium",
        "status": "In Progress",
        "category": "Evaluasi",
        "due_date": "2026-11-14",
        "notes": "Mencatat masukan dari anggota tim dan memperbarui daftar tindak lanjut.",
        "created_at": "2026-11-08T10:30:00+00:00",
    },
    {
        "title": "Mengecek kelengkapan berkas sebelum dikumpulkan",
        "assignee": "Rafif Riqullah Siregar",
        "nim": "101012300320",
        "priority": "High",
        "status": "Todo",
        "category": "Pemeriksaan",
        "due_date": "2026-11-15",
        "notes": "Memastikan seluruh bagian dokumen dan lampiran akhir sudah sesuai.",
        "created_at": "2026-11-08T11:45:00+00:00",
    },
]


def ensure_seed_data():
    if DATA_FILE.exists():
        return
    write_tasks(DEFAULT_SEED_TASKS)


def read_tasks():
    ensure_seed_data()
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def write_tasks(tasks):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = DATA_FILE.with_suffix(".tmp")
    tmp_file.write_text(
        json.dumps(tasks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp_file.replace(DATA_FILE)


def build_summary(all_tasks):
    todo_count = sum(1 for t in all_tasks if t.get("status") == "Todo")
    in_progress_count = sum(1 for t in all_tasks if t.get("status") == "In Progress")
    done_count = sum(1 for t in all_tasks if t.get("status") == "Done")
    by_priority = {
        p: sum(1 for t in all_tasks if t.get("priority") == p)
        for p in VALID_PRIORITIES
    }
    by_assignee = {}
    for name, nim in TEAM_MEMBERS.items():
        member_tasks = [t for t in all_tasks if t.get("assignee") == name]
        by_assignee[name] = {
            "nim": nim,
            "total": len(member_tasks),
            "done": sum(1 for t in member_tasks if t.get("status") == "Done"),
            "active": sum(1 for t in member_tasks if t.get("status") != "Done"),
        }
    return {
        "todo": todo_count,
        "in_progress": in_progress_count,
        "done": done_count,
        "by_priority": by_priority,
        "by_assignee": by_assignee,
    }


def extract_index_param(parsed, base_paths):
    query = parse_qs(parsed.query)
    raw_index = None
    if "index" in query and query["index"]:
        raw_index = query["index"][0]
    else:
        for prefix in base_paths:
            if parsed.path.startswith(prefix + "/"):
                raw_index = parsed.path[len(prefix) + 1 :]
                break
    return raw_index


class TaskBoardAPIHandler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, PATCH, DELETE, OPTIONS",
        )
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return None, "Body request harus berupa JSON yang valid"
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                return None, "Body request harus berupa objek JSON"
            return payload, None
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None, "Body request harus berupa JSON yang valid"

    def do_OPTIONS(self):
        self.send_json(200, {"status": "ok"})

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            tasks = read_tasks()
            return self.send_json(
                200,
                {
                    "status": "healthy",
                    "service": "team-task-backend",
                    "case_study": "6 - Papan Catatan Tugas Kelompok",
                    "storage_file": str(DATA_FILE),
                    "volume": "team-task-data",
                    "network": "app-net",
                    "stored_tasks": len(tasks),
                },
            )

        if parsed.path in ("/tasks", "/messages"):
            all_tasks = read_tasks()
            query = parse_qs(parsed.query)
            q_filter = (query.get("q", [""])[0] or "").strip().lower()
            assignee_filter = (query.get("assignee", [""])[0] or "").strip()
            priority_filter = (query.get("priority", [""])[0] or "").strip()
            status_filter = (query.get("status", [""])[0] or "").strip()

            indexed_tasks = []
            for idx, item in enumerate(all_tasks):
                enriched = dict(item)
                enriched["index"] = idx
                enriched["message"] = item.get("title", "")
                if q_filter:
                    haystack = " ".join(
                        [
                            str(item.get("title", "")),
                            str(item.get("notes", "")),
                            str(item.get("category", "")),
                            str(item.get("assignee", "")),
                            str(item.get("nim", "")),
                        ]
                    ).lower()
                    if q_filter not in haystack:
                        continue
                if assignee_filter and item.get("assignee") != assignee_filter:
                    continue
                if priority_filter and item.get("priority") != priority_filter:
                    continue
                if status_filter and item.get("status") != status_filter:
                    continue
                indexed_tasks.append(enriched)

            return self.send_json(
                200,
                {
                    "tasks": indexed_tasks,
                    "messages": indexed_tasks,
                    "total": len(indexed_tasks),
                    "total_all": len(all_tasks),
                    "summary": build_summary(all_tasks),
                },
            )

        if parsed.path.startswith("/tasks/") or parsed.path.startswith("/messages/"):
            raw_idx = parsed.path.split("/", 2)[2]
            try:
                idx = int(raw_idx)
            except ValueError:
                return self.send_json(
                    400,
                    {"error": "Parameter 'index' harus berupa bilangan bulat"},
                )
            tasks = read_tasks()
            if idx < 0 or idx >= len(tasks):
                return self.send_json(
                    404,
                    {"error": "Tugas dengan index tersebut tidak ditemukan"},
                )
            item = dict(tasks[idx])
            item["index"] = idx
            item["message"] = item.get("title", "")
            return self.send_json(200, {"index": idx, "task": item, "data": item})

        return self.send_json(404, {"error": "Endpoint tidak ditemukan"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in ("/tasks", "/messages"):
            return self.send_json(404, {"error": "Endpoint tidak ditemukan"})

        payload, err = self.read_json_body()
        if err:
            return self.send_json(400, {"error": err})

        raw_title = (
            payload.get("title")
            or payload.get("task")
            or payload.get("message")
            or ""
        )
        title = str(raw_title).strip()
        if not title:
            return self.send_json(
                400,
                {"error": "Field 'title' (judul tugas) tidak boleh kosong"},
            )

        assignee = str(
            payload.get("assignee") or "Rafhan Mazaya Fathurrahman"
        ).strip()
        nim = str(payload.get("nim") or TEAM_MEMBERS.get(assignee, "101012300238")).strip()

        priority = str(payload.get("priority") or "Medium").strip()
        if priority not in VALID_PRIORITIES:
            priority = "Medium"

        status = str(payload.get("status") or "Todo").strip()
        if status not in VALID_STATUSES:
            status = "Todo"

        category = str(payload.get("category") or "Perencanaan").strip()
        due_date = str(payload.get("due_date") or "2026-11-15").strip()
        notes = str(payload.get("notes") or "").strip()

        new_task = {
            "title": title,
            "assignee": assignee,
            "nim": nim,
            "priority": priority,
            "status": status,
            "category": category,
            "due_date": due_date,
            "notes": notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        tasks = read_tasks()
        tasks.append(new_task)
        write_tasks(tasks)
        idx = len(tasks) - 1
        enriched = dict(new_task)
        enriched["index"] = idx
        enriched["message"] = title

        return self.send_json(
            201,
            {
                "status": "created",
                "index": idx,
                "task": enriched,
                "item": enriched,
            },
        )

    def do_PATCH(self):
        parsed = urlparse(self.path)
        if not (
            parsed.path in ("/tasks", "/messages")
            or parsed.path.startswith("/tasks/")
            or parsed.path.startswith("/messages/")
        ):
            return self.send_json(404, {"error": "Endpoint tidak ditemukan"})

        raw_index = extract_index_param(parsed, ("/tasks", "/messages"))
        if raw_index is None or str(raw_index).strip() == "":
            return self.send_json(
                400,
                {"error": "Parameter query 'index' wajib diisi (contoh: /tasks?index=0)"},
            )
        try:
            idx = int(raw_index)
        except ValueError:
            return self.send_json(
                400,
                {"error": "Parameter 'index' harus berupa bilangan bulat"},
            )

        tasks = read_tasks()
        if idx < 0 or idx >= len(tasks):
            return self.send_json(
                404,
                {"error": "Tugas dengan index tersebut tidak ditemukan"},
            )

        payload, err = self.read_json_body()
        if err:
            return self.send_json(400, {"error": err})

        target = dict(tasks[idx])
        if "title" in payload:
            new_title = str(payload["title"]).strip()
            if not new_title:
                return self.send_json(
                    400,
                    {"error": "Field 'title' (judul tugas) tidak boleh kosong"},
                )
            target["title"] = new_title
        if "status" in payload and payload["status"] in VALID_STATUSES:
            target["status"] = payload["status"]
        if "priority" in payload and payload["priority"] in VALID_PRIORITIES:
            target["priority"] = payload["priority"]
        if "assignee" in payload and str(payload["assignee"]).strip():
            assignee = str(payload["assignee"]).strip()
            target["assignee"] = assignee
            target["nim"] = TEAM_MEMBERS.get(assignee, target.get("nim", ""))
        if "category" in payload:
            target["category"] = str(payload["category"]).strip()
        if "due_date" in payload:
            target["due_date"] = str(payload["due_date"]).strip()
        if "notes" in payload:
            target["notes"] = str(payload["notes"]).strip()

        tasks[idx] = target
        write_tasks(tasks)
        enriched = dict(target)
        enriched["index"] = idx
        enriched["message"] = target.get("title", "")

        return self.send_json(
            200,
            {
                "status": "updated",
                "index": idx,
                "task": enriched,
            },
        )

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if not (
            parsed.path in ("/tasks", "/messages")
            or parsed.path.startswith("/tasks/")
            or parsed.path.startswith("/messages/")
        ):
            return self.send_json(404, {"error": "Endpoint tidak ditemukan"})

        raw_index = extract_index_param(parsed, ("/tasks", "/messages"))
        if raw_index is None or str(raw_index).strip() == "":
            return self.send_json(
                400,
                {"error": "Parameter query 'index' wajib diisi (contoh: /tasks?index=0)"},
            )
        try:
            idx = int(raw_index)
        except ValueError:
            return self.send_json(
                400,
                {"error": "Parameter 'index' harus berupa bilangan bulat"},
            )

        tasks = read_tasks()
        if idx < 0 or idx >= len(tasks):
            return self.send_json(
                404,
                {"error": "Tugas dengan index tersebut tidak ditemukan"},
            )

        removed = tasks.pop(idx)
        write_tasks(tasks)
        return self.send_json(
            200,
            {
                "status": "deleted",
                "index": idx,
                "removed": removed,
                "total": len(tasks),
            },
        )

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}", flush=True)


if __name__ == "__main__":
    ensure_seed_data()
    print(f"Team Task Backend API listening on 0.0.0.0:5000 (DATA_FILE={DATA_FILE})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 5000), TaskBoardAPIHandler).serve_forever()
