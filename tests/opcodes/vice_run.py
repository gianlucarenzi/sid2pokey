# Regenerates vice_ref.txt: runs opc.prg in VICE x64sc (3.10) on a virtual X
# display (Xvfb :77) and reads the result records through the remote monitor.
#
#   cd <directory with opc.prg>; python3 vice_run.py <number of cases> > vice_ref.txt
#
# Needs x64sc and Xvfb.  Only needed to refresh the reference: run.sh does not.
import socket, subprocess, sys, time, re, os
ncases = int(sys.argv[1])
env = dict(os.environ, DISPLAY=":77")
xv = subprocess.Popen(["Xvfb", ":77", "-screen", "0", "1024x768x24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
vice = subprocess.Popen(["x64sc", "-default", "-warp", "+sound", "-autostartprgmode", "1", "-autostart", "opc.prg",
                         "-remotemonitor", "-remotemonitoraddress", "ip4://127.0.0.1:6510"],
                        env=env, stdout=open("vice.log", "w"), stderr=subprocess.STDOUT)
try:
    time.sleep(12)
    s = socket.create_connection(("127.0.0.1", 6510), timeout=10)
    def cmd(c, wait=1.0):
        s.sendall((c + "\n").encode()); time.sleep(wait)
        data = b""
        s.settimeout(0.5)
        try:
            while True:
                chunk = s.recv(65536)
                if not chunk: break
                data += chunk
        except socket.timeout:
            pass
        return data.decode("latin1")
    cmd("", 0.5)
    r = cmd("m 9fff 9fff")
    m = re.search(r">C:9fff\s+([0-9a-f]{2})", r)
    print("marker $9fff =", m.group(1) if m else "?", file=sys.stderr)
    out = []
    total = 8 * ncases
    addr = 0x8000
    mem = {}
    while addr < 0x8000 + total:
        end = min(addr + 0x1FF, 0x8000 + total - 1)
        r = cmd("m %04x %04x" % (addr, end), 0.6)
        for line in r.splitlines():
            mm = re.match(r">C:([0-9a-f]{4})\s+(.*)", line)
            if mm:
                a = int(mm.group(1), 16)
                toks = [t for t in mm.group(2).split() if re.fullmatch(r"[0-9a-f]{2}", t)][:16]
                for k, b in enumerate(toks): mem[a + k] = int(b, 16)
        addr = end + 1
    for i in range(ncases):
        print("".join("%02x" % mem.get(0x8000 + 8 * i + k, 0xEE) for k in range(8)))
    cmd("quit", 0.3)
finally:
    vice.kill(); xv.kill()
