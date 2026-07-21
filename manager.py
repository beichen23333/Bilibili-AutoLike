import os
import time
import threading
import subprocess

class BlacklistManager:
    def __init__(self):
        self.blacklist_set = set()
        self.maliciouslist_set = set()
        self.whitelist_set = set()
        self.blocked_set = set()
        self.lock = threading.Lock()

    def _load_file(self, path):
        uids = set()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    uid = line.strip()
                    if uid:
                        uids.add(uid)
        return uids

    def _sync_worker(self):
        repo_dir = "bc"
        while True:
            try:
                subprocess.run(["git", "pull"], cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                b_set = self._load_file(os.path.join(repo_dir, "blacklist.txt"))
                sb_set = self._load_file(os.path.join(repo_dir, "maliciouslist.txt"))
                w_set = self._load_file(os.path.join(repo_dir, "whitelist.txt"))
                bm_set = self._load_file(os.path.join(repo_dir, "blocked.txt"))
                with self.lock:
                    self.blacklist_set, self.maliciouslist_set, self.whitelist_set, self.blocked_set = b_set, sb_set, w_set, bm_set
            except:
                pass
            time.sleep(30)

    def start_sync(self):
        threading.Thread(target=self._sync_worker, daemon=True).start()

    def is_blacklisted(self, uid):
        with self.lock: 
            return str(uid) in self.blacklist_set

    def is_maliciouslisted(self, uid):
        with self.lock: 
            return str(uid) in self.maliciouslist_set

    def is_whitelisted(self, uid):
        with self.lock: 
            return str(uid) in self.whitelist_set

    def is_blocked(self, uid):
        with self.lock: 
            return str(uid) in self.blocked_set

    def report_blocked(self, uid):
        repo_dir = "bc"
        uid_str = str(uid)
        with self.lock:
            if uid_str in self.blocked_set: 
                return
            self.blocked_set.add(uid_str)
        try:
            with open(os.path.join(repo_dir, "blocked.txt"), "a", encoding="utf-8") as f:
                f.write(f"{uid_str}\n")
            
            subprocess.run(["git", "add", "blocked.txt"], cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", f"被 {uid_str} 拉黑"], cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "push"], cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
