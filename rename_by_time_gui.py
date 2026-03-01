import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

def list_files(folder: Path):
    return [p for p in folder.iterdir() if p.is_file()]

def sort_files(files, mode: str):
    # mode: "mtime"(수정시간) or "ctime"(생성시간)
    if mode == "mtime":
        return sorted(files, key=lambda p: p.stat().st_mtime)
    return sorted(files, key=lambda p: p.stat().st_ctime)

def rename_sequential(folder: Path, mode: str, pad: int, dry_run: bool):
    files = sort_files(list_files(folder), mode)

    # 충돌 방지: 임시 이름으로 한번 바꾼 뒤 최종 이름 적용
    tmp_pairs = []
    for idx, p in enumerate(files, start=1):
        tmp = p.with_name(f"__tmp__{idx}__{p.name}")
        tmp_pairs.append((p, tmp))

    log_lines = []
    # 1) 임시 이름
    for src, tmp in tmp_pairs:
        log_lines.append(f"TMP: {src.name} -> {tmp.name}")
        if not dry_run:
            src.rename(tmp)

    # 2) 최종 이름 (1,2,3 + 확장자 유지)
    for idx, (_, tmp) in enumerate(tmp_pairs, start=1):
        num = str(idx).zfill(pad) if pad > 0 else str(idx)
        final = tmp.with_name(f"{num}{tmp.suffix}")
        log_lines.append(f"FINAL: {tmp.name} -> {final.name}")
        if not dry_run:
            tmp.rename(final)

    return log_lines, len(files)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Time Sort Rename (1,2,3...)")
        self.geometry("760x520")

        self.folder_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="mtime")
        self.pad_var = tk.StringVar(value="0")
        self.dry_var = tk.BooleanVar(value=True)

        # Row 0: Folder
        frm_top = tk.Frame(self)
        frm_top.pack(fill="x", padx=10, pady=10)

        tk.Label(frm_top, text="폴더 경로:").pack(side="left")
        tk.Entry(frm_top, textvariable=self.folder_var, width=70).pack(side="left", padx=8)
        tk.Button(frm_top, text="찾아보기", command=self.browse).pack(side="left")

        # Row 1: Options
        frm_opt = tk.Frame(self)
        frm_opt.pack(fill="x", padx=10, pady=6)

        tk.Label(frm_opt, text="정렬 기준:").pack(side="left")
        tk.Radiobutton(frm_opt, text="수정시간(mtime)", variable=self.mode_var, value="mtime").pack(side="left", padx=6)
        tk.Radiobutton(frm_opt, text="생성시간(ctime)", variable=self.mode_var, value="ctime").pack(side="left", padx=6)

        tk.Label(frm_opt, text="0채움(자리수):").pack(side="left", padx=(20, 4))
        tk.Entry(frm_opt, textvariable=self.pad_var, width=5).pack(side="left")
        tk.Label(frm_opt, text="  (예: 3 → 001,002)").pack(side="left", padx=6)

        tk.Checkbutton(frm_opt, text="미리보기(실제 변경 X)", variable=self.dry_var).pack(side="left", padx=20)

        # Row 2: Run buttons
        frm_btn = tk.Frame(self)
        frm_btn.pack(fill="x", padx=10, pady=6)

        tk.Button(frm_btn, text="실행", command=self.run).pack(side="left")
        tk.Button(frm_btn, text="로그 지우기", command=self.clear_log).pack(side="left", padx=10)

        # Log box
        self.log = tk.Text(self, wrap="none")
        self.log.pack(fill="both", expand=True, padx=10, pady=10)

        self.note()

    def note(self):
        self.log.insert("end", "사용법:\n")
        self.log.insert("end", "1) 폴더 경로 입력 or 찾아보기\n")
        self.log.insert("end", "2) 기본은 '미리보기' 체크 상태 → 어떤 이름으로 바뀔지 로그 확인\n")
        self.log.insert("end", "3) 문제 없으면 '미리보기' 체크 해제 → 실행\n\n")
        self.log.insert("end", "주의: 같은 폴더에서 되돌리기는 어렵습니다. 먼저 복사본으로 테스트 권장.\n\n")

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_var.set(path)

    def clear_log(self):
        self.log.delete("1.0", "end")
        self.note()

    def run(self):
        folder_str = self.folder_var.get().strip().strip('"')
        if not folder_str:
            messagebox.showerror("오류", "폴더 경로를 입력하세요.")
            return

        folder = Path(folder_str)
        if not folder.exists() or not folder.is_dir():
            messagebox.showerror("오류", "유효한 폴더 경로가 아닙니다.")
            return

        try:
            pad = int(self.pad_var.get().strip() or "0")
            if pad < 0 or pad > 10:
                raise ValueError
        except ValueError:
            messagebox.showerror("오류", "0채움(자리수)은 0~10 사이 숫자로 입력하세요.")
            return

        mode = self.mode_var.get()
        dry = self.dry_var.get()

        try:
            log_lines, count = rename_sequential(folder, mode, pad, dry)
            self.log.insert("end", f"\n대상 파일 수: {count}\n")
            self.log.insert("end", f"실행 모드: {'미리보기' if dry else '실제 변경'} / 정렬: {mode} / pad={pad}\n\n")
            for line in log_lines:
                self.log.insert("end", line + "\n")
            self.log.insert("end", "\n완료.\n")
        except Exception as e:
            messagebox.showerror("오류", f"실행 중 오류:\n{e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()