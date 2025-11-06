

# 🚀 QueueCTL - Backend Developer Internship Assignment (Flam 2025)

### **Tech Stack:** Python · SQLite · Flask · Click

---

## 🎯 Objective

`QueueCTL` is a **CLI-based background job queue system** built from scratch for the **Flam Backend Internship Assignment 2025**.

It manages asynchronous jobs using worker processes, retries failed jobs with an **exponential backoff mechanism**, and maintains a **Dead Letter Queue (DLQ)** for permanently failed jobs.  
It also includes **persistence**, **configuration management**, and an optional **real-time web dashboard** for monitoring.

---

## 🧩 Problem Overview

This project aims to build a **minimal but production-grade** job queue system that can:

- Enqueue and manage background jobs  
- Run multiple worker processes concurrently  
- Retry failed jobs automatically using exponential backoff  
- Move unrecoverable jobs to a Dead Letter Queue (DLQ)  
- Persist data across restarts (SQLite database)  
- Expose all operations via a **command-line interface**

---

## ⚙️ Core Features

| Feature | Description |
|----------|-------------|
| 🧠 **Job Queueing** | Enqueue shell commands for background execution |
| ⚙️ **Multiple Workers** | Parallel job execution with process isolation |
| 🔁 **Retry Mechanism** | Automatic retries using exponential backoff (`2^attempts` seconds) |
| 💀 **Dead Letter Queue** | Stores permanently failed jobs after max retries |
| 💾 **Persistence** | SQLite ensures jobs survive restarts |
| 🧩 **Config Management** | CLI commands to customize retry/backoff behavior |
| 🧹 **Graceful Shutdown** | Workers finish current job before exiting |
| 🧍‍♂️ **Thread-Safe Execution** | Database-level locking prevents duplicates |

**Bonus Features:**
- Job Priority Support  
- Timeout Handling (per job)  
- Scheduled/Delayed Jobs  
- Job Output Logging  
- Metrics & Stats  
- Web Dashboard (Flask-based)

---

## 🔄 Job Lifecycle

| **State** | **Description** |
|------------|----------------|
| `pending` | Waiting to be picked by a worker |
| `processing` | Currently being executed |
| `completed` | Successfully finished |
| `failed` | Failed but retryable |
| `dead` | Permanently failed, moved to DLQ |

---

## 💻 CLI Commands Overview

| Category | Command | Description |
|-----------|----------|-------------|
| **Enqueue** | `queuectl enqueue -c "echo Hello"` | Add a new job to queue |
| **Workers** | `queuectl worker start --count 3` | Start 3 worker processes |
| | `queuectl worker stop` | Gracefully stop workers |
| **Status** | `queuectl status` | View job counts and system stats |
| **List Jobs** | `queuectl list --state pending` | List jobs by state |
| **DLQ** | `queuectl dlq list` / `queuectl dlq retry <id>` | View or retry DLQ jobs |
| **Config** | `queuectl config set max-retries 5` | Manage config parameters |
| **Metrics** | `queuectl metrics` | View performance metrics |
| **Logs** | `queuectl logs <job-id>` | View job execution logs |
| **Dashboard** | `queuectl dashboard` | Launch web dashboard |

---

## 🧠 Architecture Overview

```

┌────────────────────────────┐
│         CLI (Click)        │
│ queuectl enqueue / status  │
└────────────┬───────────────┘
│
┌────────────v───────────────┐
│      Queue Manager         │
│  - Enqueue / Dequeue       │
│  - Retry / DLQ handling    │
│  - Metrics & Stats         │
└────────────┬───────────────┘
│
┌────────────v───────────────┐
│         Worker(s)          │
│  - Executes jobs via shell │
│  - Handles backoff & DLQ   │
└────────────┬───────────────┘
│
┌────────────v───────────────┐
│        SQLite DB           │
│  - Persistent job data     │
│  - Configurations          │
│  - Metrics & logs          │
└────────────────────────────┘

```

**Database:** `data/queuectl.db`  
**Tables:** `jobs`, `config`, `metrics`

Each job record includes:
```

id, command, state, attempts, max_retries, priority,
timeout, created_at, updated_at, next_retry_at, error_message

````

---

## ⚡ Quick Start

### 1️⃣ Clone & Setup

```bash
git clone https://github.com/Yasashwini2005/queuectl.git
cd queuectl
python -m venv venv
venv\Scripts\activate   # (Windows)
pip install -r requirements.txt
pip install -e .
````

### 2️⃣ Run a Simple Job

```bash
queuectl enqueue -c "echo Hello QueueCTL"
queuectl worker start --count 1
queuectl status
```

### 3️⃣ Verify Persistence

Stop and restart your terminal — the job data will still be there:

```bash
queuectl list
```

---

## 📘 Example Usage

**Enqueue multiple jobs:**

```bash
queuectl enqueue -c "echo Job 1"
queuectl enqueue -c "echo Job 2" -p 10   # High priority
queuectl enqueue -c "echo Job 3" --run-at "2025-11-07T02:00:00"
```

**View job status:**

```bash
queuectl list --state pending
queuectl status
```

**Retry from DLQ:**

```bash
queuectl dlq retry <job-id>
```

**Start dashboard:**

```bash
queuectl dashboard
# Open http://localhost:5000
```

---

## 🧪 Testing Scenarios

| # | Test             | Description                        | Result |
| - | ---------------- | ---------------------------------- | ------ |
| 1 | Basic Job        | Enqueue + complete job             | ✅      |
| 2 | Retry            | Failing job retries (2s, 4s, 8s)   | ✅      |
| 3 | DLQ              | Job moves to DLQ after max retries | ✅      |
| 4 | Multiple Workers | 3 workers process unique jobs      | ✅      |
| 5 | Persistence      | Data survives restart              | ✅      |
| 6 | Timeout          | Long job stops after timeout       | ✅      |
| 7 | Priority         | High-priority executes first       | ✅      |
| 8 | Dashboard        | Real-time monitoring works         | ✅      |

---

## 🧱 Project Structure

```
queuectl/
├── queuectl/
│   ├── cli.py              # CLI commands
│   ├── queue_manager.py    # Core queue logic
│   ├── worker.py           # Worker processes
│   ├── job.py              # Job model
│   ├── database.py         # SQLite integration
│   ├── config.py           # Configuration management
│   ├── dashboard.py        # Flask web dashboard
│   ├── dashboard.jpg        # Flask web dashboard screenshot
│   └── templates/
│       └── dashboard.html  # Web UI
│
├── tests/
│   ├── test_basic.py
│   └── test_windows.py
│
├── data/
│   ├── queuectl.db
│   └── logs/
│
│
├── requirements.txt
├── setup.py
└── README.md
```

---

## 🧭 Design Decisions

* **Python + SQLite:** Easiest setup, zero external dependencies
* **Click CLI:** Clean, intuitive command structure
* **Process-based workers:** True parallelism (avoids GIL)
* **Exponential Backoff:** Simple retry delay formula `delay = base ^ attempts`
* **Flask Dashboard:** Lightweight monitoring UI
* **Pessimistic Locking:** Guarantees no duplicate job execution

---

## ⚠️ Assumptions & Limitations

* Local-only system (not distributed)
* Jobs are shell commands, not Python functions
* Dashboard runs without authentication (local use)
* No job chaining or cancellation yet
* Logs must be manually cleaned up

---

## 🌟 Bonus Features Implemented

✅ Job Priority Queue
✅ Per-job Timeout
✅ Scheduled Jobs
✅ Job Output Logs
✅ Performance Metrics
✅ Web Dashboard

---

## 🧰 Troubleshooting

| Issue                         | Cause                       | Fix                                                         |
| ----------------------------- | --------------------------- | ----------------------------------------------------------- |
| `queuectl: command not found` | venv not activated          | `venv\Scripts\activate`                                     |
| Jobs stuck in `processing`    | Worker crashed              | `UPDATE jobs SET state='pending' WHERE state='processing';` |
| "Database is locked"          | Too many concurrent workers | Reduce worker count                                         |
| Dashboard not loading         | Flask missing or port busy  | `pip install flask` / `--port 8080`                         |

---

## 🧾 Submission Details

**Author:** Yasashwini
**Assignment:** Flam Backend Developer Internship (2025)
Demo Video  
-----------  
🎥 [Watch the full demo on Google Drive](https://drive.google.com/file/d/1QgGbnTibJtUdmhGonQMX1JsmnovpsRSb/view?usp=sharing)

**GitHub:** [github.com/Yasashwini2005/QueueCTL](https://github.com/Yasashwini2005/QueueCTL)

---

## 📞 Contact

📧 **Email:** [yasashwini31@gmail.com](mailto:your.email@example.com)
🔗 **LinkedIn:** [https://www.linkedin.com/in/yasashwini-p-6173b9267/]([https://linkedin.com/in/your-profile](https://www.linkedin.com/in/yasashwini-p-6173b9267/))

---

## ✅ Checklist Before Submission

* [x] Working CLI (`queuectl`)
* [x] Persistent storage (SQLite)
* [x] Retry + Exponential Backoff
* [x] Dead Letter Queue
* [x] Configuration management
* [x] Multiple workers tested
* [x] Bonus features added
* [x] Clean, structured code
* [x] Screenshots + Demo video
* [x] Public GitHub repo ready

---

**Built with ❤️ and a lot of `print("debug")` moments.**

*Last Updated: November 2025*

```


