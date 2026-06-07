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
6. 收集 ModelSim 控制台输出，避免直接污染 Python 仿真输出；
7. 提供可重写函数，便于后续工程化扩展。

推荐工作区目录格式:
project/
├─ rtl/              # RTL 源文件目录
├─ tb/               # Testbench 目录
├─ sim/              # 仿真工作目录
│  ├─ files.f        # 源文件列表 (供 vlog -f 使用)
│  ├─ modelsim.ini   # 本地 modelsim.ini (由 vmap -c 创建)
│  └─ work/          # 物理库目录 (由 vlib 创建)
└─ scripts/
   └─ run_modelsim.py # 本脚本
"""

from __future__ import annotations


import subprocess
import shutil
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# =======================================
# 全局配置 (根据具体工程需求修改)
# =======================================

# 工程根目录 (本脚本位于 <PROJECT_ROOT>/scripts/run_modelsim.py, 根据实际情况调整)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# 仿真工作空间目录
SIM_DIR: Path = PROJECT_ROOT / "sim"
RTL_DIR: Path = PROJECT_ROOT / "rtl"
TB_DIR: Path = PROJECT_ROOT / "tb"
LOGS_DIR: Path = SIM_DIR / "logs"
FILES_F: Path = SIM_DIR / "files.f"  # 存放待编译文件列表的文件
MODELSIM_INI_NAME: str = "modelsim.ini"
FILES_F_NAME: str = "files.f"

# 命令日志
COMMAND_LOG: Path = LOGS_DIR / "commands.log"

# ModelSim/QuestaSim 后端工具路径
# 可以直接修改位绝对路径
VMAP: str = "vmap"  
VLIB: str = "vlib"
VLOG: str = "vlog"
VSIM: str = "vsim"
VDEL: str = "vdel"

# 详细日志控制开关
VERBOSE: bool = False

# TOP 模块名字
TOP_MODULE: str = "tb_top"

# =======================================
# 通用类/工具函数
# =======================================

def args_parser() -> None:
    """命令行参数解析器，允许用户覆盖全局 VERBOSE 配置。"""
    parser = argparse.ArgumentParser(description="ModelSim/QuestaSim Simulation Driver")
    parser.add_argument(
        "--verbose", '-v', action="store_true", default=None, dest="verbose",
        help="Enable verbose logging (default).",
    )
    parser.add_argument(
        "--top_module", '-tm', action="store", dest="top_module",
        help="Specify the top module name.",
    )

    args = parser.parse_args()
    # 更新全局配置: verbose
    if args.verbose is not None:
        global VERBOSE
        VERBOSE = args.verbose

    # 更新全局配置: top_module
    if args.top_module is not None:
        global TOP_MODULE
        TOP_MODULE = args.top_module

def check_dir(path: Path) -> None:
    """确保目录存在，不存在则创建。"""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def check_tool(tools: List[str], stage_name: str) -> None:
    """
    检查工具是否在系统 PATH 中可用。
    例如：vmap, vlib, vlog, vsim
    """
    for tool in tools:
        # 如果提供的工具路径是绝对路径，直接检查二进制文件是否存在
        if Path(tool).is_absolute():
            if not Path(tool).exists():
                raise FileNotFoundError(f"Tool not found: {tool}")
            continue  
            # 绝对路径存在，继续检查下一个工具

        # 否则，检查工具是否在 PATH 中
        if shutil.which(tool) is None:
            raise FileNotFoundError(
                f"Cannot find '{tool}' in PATH. "
                f"Please add ModelSim/Questa 'bin' directory to PATH, "
                f"or set {tool.upper()} to an absolute path."
            )
    print_detail_info(
        f"All required tools are available: {', '.join(tools)}",
        verbose=VERBOSE,
        stage_name=stage_name
    )

def write_log(log_content: str, log_file: Path) -> None:
    """将日志内容写入指定文件。"""
    with log_file.open("w", encoding="utf-8") as f:
        f.write(log_content)    

def append_command_log(cmd: list, log_file: Path) -> None:
    """将执行的命令追加写入命令日志文件。"""
    with log_file.open("a", encoding="utf-8") as f:
        f.write(" ".join(cmd) + "\n")

def flush_log(log_file: Path) -> None:
    """清空指定日志文件内容。"""
    with log_file.open("w", encoding="utf-8") as f:
        f.write("")

def print_detail_info(
    detail_info: str,
    verbose: bool = False,
    stage_name: Optional[str] = None,
    log_file: Path = None
) -> None:
    """
    1. 根据 verbose 开关和 stage_name 打印标准输出信息。
    2. 将标准输出日志写入文件
    """
    # 当 verbose 为 True 且 stdout 有内容时，逐行打印并加上前缀
    if verbose and detail_info:
        prefix = f"[{stage_name}_info]"
        # 使用 splitlines() 可以自动处理各种平台的换行符 (\n 或 \r\n)
        # 并且能避免因字符串末尾有换行符而打印出多余的空行
        for line in detail_info.splitlines():
            print(f"{prefix} {line}")
    if log_file:
        write_log(detail_info, log_file)
    else:
        write_log(detail_info, LOGS_DIR / f"{stage_name}_stdout.log")

def print_error_info(
    error_info: str,
    verbose: bool = True,
    stage_name: Optional[str] = None,
    log_file: Path = None
) -> None:
    """
    1. 根据 verbose 开关和 stage_name 打印标准错误信息。
    2. 将标准错误日志写入文件
    """
    # 当 verbose 为 True 且 stderr 有内容时，逐行打印并加上前缀
    if verbose and error_info:
        prefix = f"[{stage_name}_error]"
        for line in error_info.splitlines():
            print(f"{prefix} {line}")
    if log_file:
        write_log(error_info, log_file)
    else:
        write_log(error_info, LOGS_DIR / f"{stage_name}_stderr.log")

def run_cmd(
    cmd: list,
    *,
    cwd: Optional[Path] = None,
    timeout: Optional[float] = None,
    verbose: bool = False,
    stage_name: Optional[str] = None
) -> str:
    """
    运行命令并捕获输出。
    
    Parameters:
    --------------
    cmd: 要执行的命令列表（强制要求列表）
    cwd: 运行时目录
    timeout: 超时限制（秒）
    verbose: 是否详细打印命令输出
    stage_name: 可选的阶段名称，用于日志输出
    """

    # 运行具体命令并且捕获输出，输出不会直接打印到控制台
    result = subprocess.run(
        args = cmd,
        cwd = str(cwd) if cwd else None,  # subprocess.run 要求 cwd 参数为 str 或 None，Path 对象需要转换
        capture_output = True,  # 捕获 stdout 和 stderr
        text=True,
        encoding='utf-8',
        errors = 'replace',  # 遇到无法解码的字节时用替代字符替换，避免抛出异常
        check = False,  # 不抛出异常，手动检查 returncode
        timeout = timeout
    )


    # 错误信息强制打印，不管 returncode 是否非零
    # 但是依旧用 verbose 参数控制是否详细输出
    print_error_info(result.stderr, verbose=verbose, stage_name=stage_name)
    
    # 将执行的命令追加写入命令日志
    append_command_log(cmd, COMMAND_LOG)

    # 根据 verbose 参数决定是否打印标准输出信息
    print_detail_info(result.stdout, verbose=verbose, stage_name=stage_name)

    # 手动检查 returncode，打印错误信息
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=result.returncode,
            cmd=result.args,
            output=result.stdout,
            stderr=result.stderr
        )
    
    # 返回标准错误和标准输出内容，供后续处理
    # 主要是针对仿真阶段的输出，后续可以根据需要进行解析和处理
    return result.stdout



# =======================================
# 任务流程
# =======================================

# 环境初始化
def env_setup(verbose: bool = False) -> None:
    """
    1. 检测 sim/, sim/files.f 是否存在，没有则抛出异常提示用户创建
    2. 检测 sim/logs/ 是否存在，不存在则创建
    3. 调用 vmap -c 将 modelsim.ini 拷贝到 sim/ 目录（如果日志已存在，则跳过 vmap -c）
    4. 写入日志到 LOGS/setup_stdout.log 和 LOGS/setup_stderr.log
    """

    # 检测 SIM_DIR 是否存在，如果不存在则抛出异常提示用户创建
    if not SIM_DIR.exists() :
        raise FileNotFoundError(f"Simulation directory not found: {SIM_DIR}. Please create it with files.f before running the script.")
    
    # 确保日志目录存在
    check_dir(LOGS_DIR)  
    
    # 清空 commands.log
    flush_log(COMMAND_LOG)

    # 检测 FILES_F 是否存在，如果不存在则抛出异常提示用户创建
    if not FILES_F.exists():
        raise FileNotFoundError(f"Source file list not found: {FILES_F}. Please create it with the list of source files before running the script.")
    else:
        print_detail_info(
            f"Source file list found at {FILES_F}. Proceeding with setup.",
            verbose=verbose,
            stage_name="setup"
        )

    # 检测后端工具是否可用
    check_tool([VMAP, VLIB, VLOG, VSIM, VDEL], stage_name="setup")

    # 检测 modelsim.ini 是否已经存在，如果存在则跳过 vmap -c，否则执行 vmap -c 创建 modelsim.ini
    modelsim_ini_path = SIM_DIR / MODELSIM_INI_NAME
    if modelsim_ini_path.exists():
        print_detail_info(
            f"modelsim.ini already exists at {modelsim_ini_path}. Skipping vmap -c.\n"
            f"For simulation safety, recommend to check {modelsim_ini_path} content or delete it before next run.\n"
            f"Following flow will use existing modelsim.ini.\n"
            f"Similarly, the simulation log files remain unchanged; you can refer to {LOGS_DIR/'setup_stdout.log'} and {LOGS_DIR/'setup_stderr.log'} for more detailed information.\n",
            verbose=verbose,
            stage_name="setup"
        )
    else:
        run_cmd(cmd=[VMAP, "-c"], cwd=SIM_DIR, verbose=verbose, stage_name="setup")

def logic_lib_setup(verbose: bool = False) -> None:
    """
    1. 如果当前存在物理库，调用 vdel -lib work -all 删除物理库
    2. 调用 vlib work 创建物理库
    3. 调用 vmap -modelsimini modelsim.ini work work 映射逻辑库到物理库
    4. 写入日志到 LOGS/lib_stdout.log 和 LOGS/lib_stderr.log
    """
    # 检查并删除现有的物理库
    if (SIM_DIR / "work").exists():
        run_cmd(cmd=[VDEL, "-lib", "work", "-all"], cwd=SIM_DIR, verbose=verbose, stage_name="lib")

    # 创建新的物理库并完成映射
    run_cmd(cmd=[VLIB, "work"], cwd=SIM_DIR, verbose=verbose, stage_name="lib")
    run_cmd(cmd=[VMAP, "-modelsimini", MODELSIM_INI_NAME, "work", "work"], cwd=SIM_DIR, verbose=verbose, stage_name="lib")

def compile_sources(verbose: bool = False) -> None:
    """
    1. 调用 vlog -sv -work work -f files.f -modelsimini modelsim.ini 编译源文件
    2. 写入日志到 LOGS/compile_stdout.log 和 LOGS/compile_stderr.log
    """
    run_cmd(cmd=[VLOG, "-sv", "-work", "work", "-f", FILES_F_NAME, "-modelsimini", MODELSIM_INI_NAME], cwd=SIM_DIR, verbose=verbose, stage_name="compile")

def simulation_run(verbose: bool = False) -> str:
    """
    1. 调用 vsim -c -modelsimini modelsim.ini work.<TOP_MODULE> -do "run -all; quit" 运行仿真
    2. 写入日志到 LOGS/sim_stdout.log 和 LOGS/sim_stderr.log
    """
    result = run_cmd(cmd=[VSIM, "-c", "-voptargs=+acc", "-modelsimini", MODELSIM_INI_NAME, f"work.{TOP_MODULE}", "-do", "run -all; quit -f"], cwd=SIM_DIR, verbose=verbose, stage_name="sim")
    return result

def process(sim_result: str, verbose: bool = False) -> None:
    """
    可配置模块，应根据不同工程需求进行定制化
    例如正则表达式提取仿真结果中的关键信息，或者将仿真输出转换成特定格式的报告等。
    """
    print_detail_info(sim_result, verbose=verbose, stage_name="process")


def run_flow(verbose: bool = False) -> None:
    # Step 1. 环境初始化
    env_setup(verbose=verbose)
    # Step 2. 创建逻辑库并建立逻辑库-物理库映射
    logic_lib_setup(verbose=verbose)
    # Step 3. 编译源文件
    compile_sources(verbose=verbose)
    # Step 4. 运行仿真
    result = simulation_run(verbose=verbose)
    # Step 5. 处理仿真输出信息
    process(sim_result=result, verbose=verbose)

# =======================================
# 主接口函数
# =======================================

def main() -> None:
    # Step 1. 解析命令行参数并设置全局配置
    args_parser()
    # Step 2. 运行仿真流程
    run_flow(verbose = VERBOSE)

# 主接口
if __name__ == "__main__":
    main()
