import os
import time
import base64
import threading
import subprocess
from Crypto.Cipher import AES

class BlacklistDecryptor:
    def __init__(self):
        key_str = os.getenv("CRYPTO_KEY", "")
        self.key = key_str.ljust(32, '0')[:32].encode('utf-8')
        self.blacklist_set = set()
        self.severe_blacklist_set = set()
        self.whitelist_set = set()
        self.blocked_me_set = set()
        self.lock = threading.Lock()

    def _decrypt_line(self, encrypted_str):
        try:
            data = base64.b64decode(encrypted_str.strip())
            cipher = AES.new(self.key, AES.MODE_GCM, nonce=data[:12])
            return cipher.decrypt_and_verify(data[28:], data[12:28]).decode('utf-8')
        except:
            return None

    def _load_file(self, path):
        uids = set()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    decrypted_uid = self._decrypt_line(line)
                    if decrypted_uid:
                        uids.add(decrypted_uid)
        return uids

    def _sync_worker(self):
        repo_dir = "bc" if os.path.exists("bc") else "."
        while True:
            try:
                subprocess.run(["git", "pull"], cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                b_set = self._load_file(os.path.join(repo_dir, "blacklist.txt"))
                sb_set = self._load_file(os.path.join(repo_dir, "severe_blacklist.txt"))
                w_set = self._load_file(os.path.join(repo_dir, "whitelist.txt"))
                bm_set = self._load_file(os.path.join(repo_dir, "blocked_me.txt"))
                with self.lock:
                    self.blacklist_set, self.severe_blacklist_set, self.whitelist_set, self.blocked_me_set = b_set, sb_set, w_set, bm_set
            except:
                pass
            time.sleep(30)

    def start_sync(self):
        threading.Thread(target=self._sync_worker, daemon=True).start()

    def is_blacklisted(self, uid):
        with self.lock: return str(uid) in self.blacklist_set

    def is_severe_blacklisted(self, uid):
        with self.lock: return str(uid) in self.severe_blacklist_set

    def is_whitelisted(self, uid):
        with self.lock: return str(uid) in self.whitelist_set

    def is_blocked_me(self, uid):
        with self.lock: return str(uid) in self.blocked_me_set

    def report_blocked_me(self, uid):
        repo_dir = "bc"
        uid_str = str(uid)
        with self.lock:
            if uid_str in self.blocked_me_set: return
            self.blocked_me_set.add(uid_str)
        try:
            cipher = AES.new(self.key, AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(uid_str.encode('utf-8'))
            encrypted_line = base64.b64encode(cipher.nonce + tag + ciphertext).decode('utf-8') + "\n"
            with open(os.path.join(repo_dir, "blocked_me.txt"), "a", encoding="utf-8") as f:
                f.write(encrypted_line)
            subprocess.run(["git", "add", "blocked_me.txt"], cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", f"被 {uid} 拉黑"], cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "push"], cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
