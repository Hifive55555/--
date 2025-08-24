# main.py
import flet as ft
import pandas as pd
import subprocess
import os
import json
import math
from typing import Dict, List, Tuple

NEWS_COLLECT_SCRIPT = "collect_news.py"
PREDICT_SCRIPT      = "predict.py"

# ----------------------------------------------------------
# GUI
# ----------------------------------------------------------
def main(page: ft.Page):
    page.title = "新闻事件预测器"
    page.window_width  = 900
    page.window_height = 700
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # 全局状态
    news_df: pd.DataFrame = None

    # 左右两栏 ListView
    lv_left  = ft.ListView(expand=True, spacing=10, padding=10)
    lv_right = ft.ListView(expand=True, spacing=10, padding=10)

    # 进度条、状态文字
    pb_pull    = ft.ProgressBar(width=400, visible=False)
    pb_predict = ft.ProgressBar(width=400, visible=False)
    lbl_status = ft.Text("", size=16, italic=True)

    # ----------------------------------------------------------
    # 启动即加载
    # ----------------------------------------------------------
    def load_excel_on_start():
        nonlocal news_df
        if os.path.exists("news.xlsx"):
            try:
                news_df = pd.read_excel("news.xlsx")
                lbl_status.value = f"已加载 {len(news_df)} 条历史新闻"
                show_news()
            except Exception as ex:
                lbl_status.value = f"加载历史数据失败：{ex}"
        else:
            lbl_status.value = "未找到 news.xlsx，请“拉取新闻”"
        page.update()

    # ----------------------------------------------------------
    # 拉取新闻
    # ----------------------------------------------------------
    def pull_news(e):
        nonlocal news_df
        pb_pull.visible = True
        lbl_status.value = "正在拉取新闻..."
        page.update()

        try:
            subprocess.run(["python", NEWS_COLLECT_SCRIPT], check=True)
            news_df = pd.read_excel("news.xlsx")
            lbl_status.value = f"已拉取 {len(news_df)} 条新闻"
            show_news()
        except Exception as ex:
            lbl_status.value = f"拉取失败：{ex}"
        finally:
            pb_pull.visible = False
            page.update()

    # ----------------------------------------------------------
    # 可视化展示
    # ----------------------------------------------------------
    def show_news():
        lv_left.controls.clear()
        lv_right.controls.clear()

        if news_df is None or news_df.empty:
            return

        # 确保有“值”列
        if "值" not in news_df.columns:
            news_df["值"] = 0.0

        # 构造需要排序的字段
        def _score(val):
            return val if val >= 0.5 else 1 - val

        # 添加辅助列
        news_df["_score"] = news_df["值"].apply(_score)

        # 分别筛选
        left_df  = news_df[news_df["值"] >= 0.5].sort_values("_score", ascending=False)
        right_df = news_df[news_df["值"] < 0.5].sort_values("_score", ascending=False)

        for _, row in left_df.iterrows():
            lv_left.controls.append(_build_card(row, left=True))
        for _, row in right_df.iterrows():
            lv_right.controls.append(_build_card(row, left=False))

        page.update()

    # ----------------------------------------------------------
    # 单条卡片 UI
    # ----------------------------------------------------------
    def _build_card(row: pd.Series, left: bool):
        val = float(row.get("值", 0))
        display_val = val if left else 1 - val
        # 颜色插值：红(1,0,0) ←→ 蓝(0,0,1)
        r = int(255 * val)
        b = int(255 * (1 - val))
        color_hex = f"#{r:02x}00{b:02x}"

        bar_width = max(4, int(display_val * 200))

        return ft.Container(
            content=ft.Column([
                ft.Text(str(row.get("标题", "无标题")), size=14, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Container(
                        width=bar_width,
                        height=10,
                        bgcolor=color_hex,
                        border_radius=5
                    ),
                    ft.Text(f"{display_val:.2f}", size=13, color=color_hex)
                ], spacing=5)
            ], tight=True),
            padding=10,
            border=ft.border.all(1, color_hex),
            border_radius=8
        )

    # ----------------------------------------------------------
    # 预测事件（保持不变）
    # ----------------------------------------------------------
    def predict(e):
        if news_df is None or news_df.empty:
            lbl_status.value = "请先拉取新闻"
            page.update()
            return

        pb_predict.visible = True
        lbl_status.value = "正在分类并预测..."
        page.update()

        try:
            result = bayes_predict(news_df["值"])
            print(result)
            show_result(result)
        except Exception as ex:
            lbl_status.value = f"预测失败：{ex}"
        finally:
            pb_predict.visible = False
            page.update()

    def show_result(result: float):
        """
        根据预测概率弹出对话框，给出“发生 / 不发生”的结论。
        """
        threshold = 0.70        # 可随业务需求调整
        if result >= threshold:
            verdict = "事件大概率会发生"
        else:
            verdict = "事件大概率不会发生"

        dlg = ft.AlertDialog(
            title=ft.Text("预测结果"),
            modal=True,
            content=ft.Column([
                ft.Text(f"预测概率：{result:.2%}", size=18),
                ft.Text(verdict, size=16, weight=ft.FontWeight.BOLD)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            actions=[
                ft.TextButton("关闭", on_click=lambda _: setattr(dlg, "open", False))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        page.dialog = dlg
        dlg.open = True
        lbl_status.value = f'{verdict} ({result})'
        page.update()

    # ----------------------------------------------------------
    # 按钮
    # ----------------------------------------------------------
    btn_pull   = ft.ElevatedButton("拉取新闻", on_click=pull_news, width=200)
    btn_predict= ft.ElevatedButton("预测",     on_click=predict,   width=200)

    # ----------------------------------------------------------
    # 页面布局
    # ----------------------------------------------------------
    page.add(
        ft.Column([
            ft.Row([btn_pull, btn_predict], alignment=ft.MainAxisAlignment.CENTER),
            pb_pull,
            pb_predict,
            lbl_status,
            ft.Divider(height=1),
            ft.Row([
                ft.Column([ft.Text("支持（≥ 0.5）", size=16, weight=ft.FontWeight.BOLD), lv_left], expand=True),
                ft.VerticalDivider(width=1),
                ft.Column([ft.Text("反对（< 0.5）", size=16, weight=ft.FontWeight.BOLD), lv_right], expand=True),
            ], expand=True)
        ], expand=True)
    )

    # 启动即加载
    load_excel_on_start()

def bayes_predict(values: pd.Series) -> float:
    if values.empty:
        return 0.5          # 无数据时给一个中性概率
    return float(values.mean())

# ----------------------------------------------------------
# 入口
# ----------------------------------------------------------
if __name__ == "__main__":
    ft.app(target=main)