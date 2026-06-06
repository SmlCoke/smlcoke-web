#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ModelSim/QuestaSim Python Simulation Driver Template

功能：
1. 使用 pathlib 管理工程路径；
2. 使用 subprocess 调度 vmap / vlib / vdel / vlog / vsim；
3. 使用 vmap -c 显式创建工程本地 modelsim.ini；
4. 所有关键命令显式指定 -modelsimini；
5. 使用 files.f 进行编译；
6. 自动生成 run_sim.do；
7. 收集 ModelSim 控制台输出，避免直接污染 Python 仿真输出；
8. 提供可重写函数，便于后续工程化扩展。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ============================================================
# 1. 全局配置区：不同项目主要改这里
# ============================================================
'''推荐工作区目录格式
project/
├─ rtl/
├─ tb/
├─ sim/
│  ├─ files.f
│  ├─ modelsim.ini
│  └─ work/
└─ scripts/
   └─ run_modelsim.py
'''

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RTL_DIR = PROJECT_ROOT / "rtl"
TB_DIR = PROJECT_ROOT / "tb"
SIM_DIR = PROJECT_ROOT / "sim"

# 配置文件: files.f 与 modelsim.ini
FILES_F = SIM_DIR / "files.f"
MODELSIM_INI = SIM_DIR / "modelsim.ini"

# 逻辑库名字与路径
WORK_LIB_NAME = "work"
WORK_LIB_DIR = SIM_DIR / WORK_LIB_NAME

# .do 脚本名字
RUN_DO = SIM_DIR / "run_sim.do"

# 仿真日志
TRANSCRIPT_LOG = SIM_DIR / "transcript.log"
SIM_RESULT_LOG = SIM_DIR / "sim_result.log"

# 顶层 testbench：对应 vsim work.riscv_soc_tb
TOP_MODULE = "riscv_soc_tb"

# ModelSim/Questa 命令名。如果没有加入 PATH，可以改成绝对路径。
VMAP = "vmap"
VLIB = "vlib"
VDEL = "vdel"
VLOG = "vlog"
VSIM = "vsim"

# 编译选项
VLOG_OPTIONS = [
    "-sv",
    # "+acc",          # 如果希望编译阶段保留更多可见性，也可加
    # "+define+SIM",   # 示例：宏定义
    # "+incdir+../rtl/include",
]

# 仿真选项
VSIM_OPTIONS = [
    "-voptargs=+acc",
]

# 仿真运行命令
SIM_RUN_COMMAND = "run -all"


# ============================================================
# 2. 数据结构：保存命令执行结果
# ============================================================

@dataclass
class CmdResult:
    name: str
    cmd: list[str]
    cwd: Path
    returncode: int
    stdout: str
    stderr: str

    @property
    def combined_output(self) -> str:
        if self.stderr:
            return self.stdout + "\n" + self.stderr
        return self.stdout


@dataclass
class SimulationReport:
    passed: bool
    failed: bool
    returncode: int
    transcript_log: Path
    sim_result_log: Path
    summary_lines: list[str] = field(default_factory=list)



# ============================================================
# 3. 工具函数
# ============================================================

def ensure_directory(path: Path) -> None:
    """确保目录存在，没有则创建"""
    path.mkdir(parents=True, exist_ok=True)