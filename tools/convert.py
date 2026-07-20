"""
 TUNER Beta. Should be enough redundancies throughout to stop it from exploding I hope
 Scripting is simple enough to not really warrant comments IMO. Though it is all sorta a mess still anyway
 If you're wondering why it constantly prints a lot of conversion data, it's because I don't want the user to be scared that it froze
 Also I kinda needed it for debugging
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import shutil
import subprocess
import glob
import re
import json
 
ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS   = os.path.join(ROOT, "tools")
FILES   = os.path.join(ROOT, "FILES_GO_HERE")
OUT     = os.path.join(ROOT, "OUTPUT", "OCCULTICNINE")
WINDATA = os.path.join(OUT, "windata")
 
KEY_LEN = 13
KEEP_EXTS = (".bin", ".psb.m")
 
OC9_SOURCES = [
    ("vita", "eboot.bin.elf", 0x190BF8),
    ("ps4",  "eboot.bin",     0x236658),
    ("xone", "advengine.exe", 0x6DA6E0),
]
 
KONO_SOURCE = ("KONOSUBA.exe", 0x00299AF0)
 
GROUPS = [
    "config",
    "font",
    "image",
    "motion",
    "scenario",
    "script",
    "sound",
    "voice",
]
 
 
def run(cmd, cwd=None):
    subprocess.check_call(cmd, cwd=cwd)
 
def lowercase_keys(obj):
    if isinstance(obj, dict):
        return {k.lower(): lowercase_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [lowercase_keys(v) for v in obj]
    return obj
 
def in_dir(path, folder):
    return os.sep + folder + os.sep in path
 
def in_any_dir(path, folders):
    return any(in_dir(path, f) for f in folders)
 
 
def read_key(fname, offset):
    path = os.path.join(FILES, fname)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        f.seek(offset)
        data = f.read(KEY_LEN)
    try:
        return data.decode("ascii") if len(data) == KEY_LEN else None
    except Exception:
        return None
 
def extract_keys():
    oc9 = None
    for _, fname, off in OC9_SOURCES:
        oc9 = read_key(fname, off)
        if oc9:
            break
    if not oc9:
        raise RuntimeError("OC9 key not found")
    kono = read_key(*KONO_SOURCE)
    if not kono:
        raise RuntimeError("KONOSUBA key not found")
    return oc9, kono
 
 
def unpack_psb(oc9):
    exe = os.path.join(TOOLS, "PsbDecompile.exe")
    for g in GROUPS:
        files_dir = os.path.join(FILES, g)
        out_dir   = os.path.join(WINDATA, g)
        info_psb  = os.path.join(FILES, f"{g}_info.psb.m")
        if (
            (os.path.isdir(files_dir) and os.listdir(files_dir)) or
            (os.path.isdir(out_dir)   and os.listdir(out_dir))
        ):
            continue
        if not os.path.exists(info_psb):
            continue
        print(f"  Unpacking {g}...")
        run([exe, "info-psb", "-k", oc9, info_psb, "-a"], cwd=FILES)
 
 
def collect_output():
    os.makedirs(WINDATA, exist_ok=True)
    for g in GROUPS:
        src = os.path.join(FILES, g)
        if not os.path.isdir(src):
            continue
        dst = os.path.join(WINDATA, g)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.move(src, dst)
 
    for pat in ("*_info.psb.m.json", "*_info.psb.m.resx.json"):
        for f in glob.glob(os.path.join(FILES, pat)):
            shutil.move(f, WINDATA)
 
 
def patch_sound_entry(entry, res_index):
    cl = entry.get("channelList", [])
    if not cl:
        return res_index
 
    file    = entry.get("file")
    loop    = entry.get("loop", 0)
    loopstr = entry.get("loopstr", "none")
 
    if loop > 0 and loopstr.startswith("range:"):
        a, b    = map(int, loopstr.split(":")[1].split(","))
        new_len = b - a
        cl[0]["archData"] = {
            "fmt":  f"#resource#{res_index}",
            "data": f"#resource#{res_index + 1}",
            "loop": [a, new_len],
            "wav":  file,
        }
        entry["loopstr"] = f"range:{a},{new_len}"
        res_index += 2
    else:
        cl[0]["archData"] = {
            "fmt":  f"#resource#{res_index}",
            "dpds": f"#resource#{res_index + 1}",
            "data": f"#resource#{res_index + 2}",
            "wav":  file,
        }
        res_index += 3
 
    entry["quality"] = 2
    return res_index
 
def rebuild_sound_archive_json(obj, resx_order):
    voice = obj.get("voice", {})
    res_index = 0
    for name in resx_order:
        entry = voice.get(name)
        if not entry:
            continue
        try:
            res_index = patch_sound_entry(entry, res_index)
        except Exception as e:
            print(f"  WARNING: failed patching entry '{name}': {e}")
 
def load_resx_order(json_path):
    resx_path = json_path.replace(".json", ".resx.json")
    if not os.path.exists(resx_path):
        return None
    with open(resx_path, "r", encoding="utf-8") as f:
        resx = json.load(f)
    resources = resx.get("Resources") or resx.get("resources") or {}
    return list(resources.keys())
 
 
def edit_one_json(args):
    path, oc9, kono = args
 
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    orig = txt
 
    txt = txt.replace(oc9, kono)
    txt = re.sub(
        r'"(platform|spec)"\s*:\s*"(vita|ps4|xone|win)"',
        r'"\1": "win"',
        txt,
        flags=re.IGNORECASE,
    )
 
    if path.endswith(".m.json") and in_any_dir(path, ("image", "font", "motion")):
        txt = txt.replace("_SW", "")
 
    if path.endswith(".resx.json"):
        if in_any_dir(path, ("sound", "voice")):
            txt = re.sub(r'\.at9\.wav', '.xwma.xwma', txt, flags=re.IGNORECASE)
            obj = lowercase_keys(json.loads(txt))
            txt = json.dumps(obj, indent=2, ensure_ascii=False)
    elif in_any_dir(path, ("sound", "voice")):
        resx_order = load_resx_order(path)
        obj = json.loads(txt)
        if resx_order is None:
            resx_order = list(obj.get("voice", {}).keys())
        rebuild_sound_archive_json(obj, resx_order)
        txt = json.dumps(obj, indent=2, ensure_ascii=False)
 
    if txt == orig:
        return 0
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    return 1
 
def edit_all_jsons(oc9, kono):
    paths = glob.glob(os.path.join(WINDATA, "**", "*.json"), recursive=True)
    resx_paths  = [p for p in paths if p.endswith(".resx.json")]
    other_paths = [p for p in paths if not p.endswith(".resx.json")]
    print(f"Editing {len(paths)} JSON files...")
 
    changed = 0
    processed = 0
    for batch in (resx_paths, other_paths):
        if not batch:
            continue
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as ex:
            futures = [ex.submit(edit_one_json, (p, oc9, kono)) for p in batch]
            for f in as_completed(futures):
                changed += f.result()
                processed += 1
                if processed % 500 == 0:
                    print(f"  {processed}/{len(paths)}...")
    print(f"JSON editing complete ({changed} files changed).")
 
 
def reencode_one_movie(args):
    src, dst, ffmpeg = args
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    subprocess.check_call([
        ffmpeg, "-y", "-loglevel", "error",
        "-i", src,
        "-map", "0:v:0", "-map", "0:a:0",
        "-c:v", "copy",
        "-c:a", "pcm_s16le",
        dst,
    ])
 
def reencode_movies():
    movie_src_root = os.path.join(FILES, "movie")
    if not os.path.isdir(movie_src_root):
        return
    movie_dst_root = os.path.join(WINDATA, "movie")
    ffmpeg = os.path.join(TOOLS, "ffmpeg.exe")
    jobs = []
    for root, _, names in os.walk(movie_src_root):
        for n in names:
            if n.lower().endswith(".mp4"):
                src = os.path.join(root, n)
                rel = os.path.relpath(src, movie_src_root)
                dst = os.path.join(movie_dst_root, rel)
                jobs.append((src, dst, ffmpeg))
    if not jobs:
        return
    print(f"Reencoding {len(jobs)} movies...")
    with ThreadPoolExecutor(max_workers=min(4, os.cpu_count())) as ex:
        list(ex.map(reencode_one_movie, jobs))
    print("Movies done.")
 
 
def is_looping_bgm(name):
    n = name.lower()
    return n.startswith("bgm") and "nl" not in n and "dummy" not in n
 
def reencode_one_audio(args):
    path, enc = args
    name = os.path.basename(path)
 
    if not in_any_dir(path, ("sound", "voice")):
        return 0
 
    if in_dir(path, "sound") and is_looping_bgm(name):
        dst = re.sub(r'\.at9\.wav$|\.wav$', '.wav.wav', path, flags=re.IGNORECASE)
        if dst != path:
            os.replace(path, dst)
        return 1
 
    dst = re.sub(r'\.at9\.wav$|\.wav$', '.xwma.xwma', path, flags=re.IGNORECASE)
    run([enc, path, dst])
    return 1
 
def reencode_audio():
    enc = os.path.join(TOOLS, "xWMAEncode.exe")
    paths = [
        os.path.join(r, n)
        for r, _, fs in os.walk(WINDATA)
        for n in fs
        if n.lower().endswith(".wav")
    ]
    if not paths:
        return
    print(f"Reencoding {len(paths)} audio files...")
    with ThreadPoolExecutor(max_workers=min(4, os.cpu_count())) as ex:
        list(ex.map(reencode_one_audio, [(p, enc) for p in paths]))
    print("Audio done.")
 
 
def rebuild_sound_resx():
    pattern = os.path.join(WINDATA, "**", "*.resx.json")
    for path in glob.glob(pattern, recursive=True):
        if not in_any_dir(path, ("sound", "voice")):
            continue
 
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
 
        resources = obj.get("resources") or obj.get("Resources") or {}
        if not resources:
            continue
 
        base_dir = os.path.dirname(path)
        new_res  = {}
 
        for key, declared in resources.items():
            folder = os.path.join(base_dir, key)
            if not os.path.isdir(folder):
                new_res[key] = declared
                continue
 
            files = os.listdir(folder)
            declared_file = os.path.basename(declared)
            if declared_file in files:
                new_res[key] = declared
                continue
 
            chosen = next(
                (c for c in (f"{key}.xwma.xwma", f"{key}.wav.wav") if c in files),
                files[0] if files else None,
            )
            new_res[key] = f"{key}/{chosen}" if chosen else declared
 
        obj["resources"] = new_res
        obj.pop("Resources", None)
        obj = lowercase_keys(obj)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
 
 
def rebuild_psb(kono):
    exe = os.path.join(TOOLS, "PsBuild.exe")
    for g in GROUPS:
        src = os.path.join(WINDATA, f"{g}_info.psb.m.json")
        if not os.path.exists(src):
            continue
        print(f"  Rebuilding {g}...")
        run([exe, "info-psb", "-k", kono, os.path.basename(src)], cwd=WINDATA)
 
 
def patch_exe_strings(dst):
    with open(dst, "rb") as f:
        data = f.read()
 
    old, new = b"KONOSUBA", b"OCCULTIC"
    count = data.count(old)
    if not count:
        return
 
    data = data.replace(old, new)
    with open(dst, "wb") as f:
        f.write(data)
        
 
def finalize():
    src = os.path.join(FILES, "KONOSUBA.exe")
    dst = os.path.join(OUT, "OCCULTIC;NINE.exe")
    shutil.copy2(src, dst)
    print(f"Copied executable -> {dst}")
 
    patch_exe_strings(dst)
 
    rcedit = os.path.join(TOOLS, "rcedit.exe")
    icon   = os.path.join(FILES, "icon.ico")
    if os.path.exists(rcedit) and os.path.exists(icon):
        print(f"Setting icon from {icon}")
        run([rcedit, dst, "--set-icon", icon]) 
 
def cleanup_windata():
    if not os.path.isdir(WINDATA):
        return
    print("Cleaning up windata...")
    for entry in os.listdir(WINDATA):
        if entry.lower() == "movie":
            continue
        path = os.path.join(WINDATA, entry)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif not entry.lower().endswith(KEEP_EXTS):
            os.remove(path)
    print("Cleanup done.")
 
 
def main():
    print("=== TUNING APPRICATION ===")
    oc9, kono = extract_keys()
    print(f"Keys: OC9={oc9!r}  KONO={kono!r}")
 
    print("Unpacking PSBs...")
    unpack_psb(oc9)
 
    print("Collecting output...")
    collect_output()
 
    print("Editing JSONs...")
    edit_all_jsons(oc9, kono)
 
    print("Reencoding movies...")
    reencode_movies()
 
    print("Reencoding audio...")
    reencode_audio()
 
    print("Rebuilding sound resx...")
    rebuild_sound_resx()
 
    print("Rebuilding PSBs...")
    rebuild_psb(kono)
 
    print("Finalizing...")
    finalize()
 
    cleanup_windata()
 
    print("=== TUNER DONE ===")
 
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        input("Press Enter to exit...")