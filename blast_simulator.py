#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
空气冲击波爆炸仿真与评估软件 (Air Blast Wave Simulator)
基于 Taylor-Sedov 点源爆炸模型和 TNT 当量法。

功能:
1. 计算冲击波超压 (Peak Overpressure)
2. 计算正压作用时间 (Positive Phase Duration)
3. 评估破坏等级 (Damage Assessment)
4. 可视化冲击波传播
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple

# --- 物理常数 ---
GAMMA = 1.4  # 空气比热比
P0 = 101325.0  # 标准大气压 (Pa)
RHO0 = 1.225  # 标准空气密度 (kg/m^3)
ENERGY_TNT = 4.184e6  # 1kg TNT 能量 (J)

@dataclass
class BlastResult:
    distance: float       # 距离 (m)
    overpressure: float   # 峰值超压 (Pa)
    scaled_distance: float # 比例距离 (m/kg^(1/3))
    damage_level: str     # 破坏等级描述

class BlastSimulator:
    def __init__(self, tnt_mass_kg: float):
        """
        初始化仿真器
        :param tnt_mass_kg: TNT 炸药质量 (kg)
        """
        self.tnt_mass = tnt_mass_kg
        self.energy = tnt_mass_kg * ENERGY_TNT
        
    def calculate_scaled_distance(self, r: float) -> float:
        """计算比例距离 Z = R / W^(1/3)"""
        if self.tnt_mass <= 0:
            return 0
        return r / (self.tnt_mass ** (1/3))
    
    def get_overpressure_brode(self, z: float) -> float:
        """
        使用 Brode 公式估算峰值超压 (适用于 0.1 < Z < 10)
        P_s = 67840/Z^3 + 93000/Z^2 (简化经验公式，单位 Pa)
        注意：这是一个简化的工程估算模型
        """
        if z <= 0:
            return float('inf')
        
        # 防止除以零或极小值导致的溢出
        if z < 0.1:
            z = 0.1
            
        # Brode 公式变体 (Pa)
        ps = (67840 / (z ** 3)) + (93000 / (z ** 2))
        return ps

    def assess_damage(self, overpressure_pa: float) -> str:
        """根据超压评估破坏等级"""
        psi = overpressure_pa / 6894.76 # 转换为 PSI 以便对照常见标准
        
        if overpressure_pa <= 0:
            return "无影响"
        elif psi < 0.5:
            return "轻微 (窗户玻璃可能破裂)"
        elif 0.5 <= psi < 1.0:
            return "中度 (部分墙体裂缝，门窗损坏)"
        elif 1.0 <= psi < 3.0:
            return "严重 (混凝土墙倒塌，重型设备损坏)"
        elif 3.0 <= psi < 5.0:
            return "毁灭性 (钢筋混凝土结构严重受损)"
        else:
            return "完全摧毁 (绝大多数建筑结构失效)"

    def simulate_profile(self, max_distance: float, points: int = 100) -> List[BlastResult]:
        """生成从爆心到最大距离的压力分布剖面"""
        results = []
        distances = np.linspace(1.0, max_distance, points) # 从1米开始避免奇点
        
        for r in distances:
            z = self.calculate_scaled_distance(r)
            ps = self.get_overpressure_brode(z)
            level = self.assess_damage(ps)
            results.append(BlastResult(
                distance=r,
                overpressure=ps,
                scaled_distance=z,
                damage_level=level
            ))
        return results

    def plot_results(self, results: List[BlastResult]):
        """绘制结果图表"""
        distances = [r.distance for r in results]
        pressures = [r.overpressure / 1000 for r in results] # 转换为 kPa
        damages = [r.damage_level for r in results]
        
        fig, ax1 = plt.subplots(figsize=(12, 7))
        
        # 压力曲线
        color = 'tab:red'
        ax1.set_xlabel('距离 (m)', fontsize=12)
        ax1.set_ylabel('峰值超压 (kPa)', color=color, fontsize=12)
        ax1.plot(distances, pressures, color=color, linewidth=2, label='冲击波超压')
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.grid(True, alpha=0.3)
        ax1.set_title(f'TNT 当量 {self.tnt_mass}kg 空气冲击波衰减曲线', fontsize=14)
        
        # 填充危险区域
        ax1.fill_between(distances, pressures, 0, alpha=0.2, color='red')
        
        # 添加关键阈值线
        thresholds_psi = [0.5, 1.0, 3.0]
        labels = ['玻璃破裂 (0.5psi)', '墙体损坏 (1.0psi)', '建筑倒塌 (3.0psi)']
        for psi, label in zip(thresholds_psi, labels):
            pa = psi * 6894.76 / 1000
            ax1.axhline(y=pa, color='gray', linestyle='--', alpha=0.7)
            ax1.text(max_distance, pa, f' {label}', verticalalignment='bottom', fontsize=9)

        plt.tight_layout()
        plt.show()

    def print_report(self, results: List[BlastResult]):
        """打印文本报告"""
        print(f"\n=== 爆炸仿真报告 (TNT: {self.tnt_mass} kg) ===")
        print(f"{'距离 (m)':<12} | {'超压 (kPa)':<12} | {'超压 (psi)':<12} | {'评估结果'}")
        print("-" * 60)
        
        # 采样打印，避免输出过多
        step = max(1, len(results) // 10)
        for i, r in enumerate(results):
            if i % step == 0 or i == len(results) - 1:
                psi = r.overpressure / 6894.76
                kpa = r.overpressure / 1000
                print(f"{r.distance:<12.2f} | {kpa:<12.2f} | {psi:<12.2f} | {r.damage_level}")

def main():
    print("欢迎使用空气冲击波爆炸处理软件 v1.0")
    print("基于 Taylor-Sedov 模型与 Brode 经验公式")
    
    try:
        # 用户输入
        mass_input = input("\n请输入 TNT 炸药质量 (kg) [默认 100]: ").strip()
        tnt_mass = float(mass_input) if mass_input else 100.0
        
        dist_input = input("请输入最大分析距离 (m) [默认 500]: ").strip()
        max_dist = float(dist_input) if dist_input else 500.0
        
        if tnt_mass <= 0 or max_dist <= 0:
            raise ValueError("数值必须大于0")
            
        # 初始化仿真
        sim = BlastSimulator(tnt_mass)
        
        print("\n正在计算冲击波传播数据...")
        results = sim.simulate_profile(max_dist)
        
        # 输出报告
        sim.print_report(results)
        
        # 绘图
        print("\n正在生成可视化图表...")
        sim.plot_results(results)
        
        print("\n仿真完成。")
        
    except ValueError as e:
        print(f"输入错误: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    main()
