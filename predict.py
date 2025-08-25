# main.py
import flet as ft
import pandas as pd
import os
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
                # Convert "值" column to float
                if "值" in news_df.columns:
                    news_df["值"] = pd.to_numeric(news_df["值"], errors='coerce').fillna(0.0)
                lbl_status.value = f"已加载 {len(news_df)} 条历史新闻"
                show_news()
            except Exception as ex:
                lbl_status.value = f"加载历史数据失败：{ex}"
        else:
            lbl_status.value = "未找到 news.xlsx，请拉取新闻"
        page.update()

    # ----------------------------------------------------------
    # 拉取新闻
    # ----------------------------------------------------------
    def pull_news(e):
        nonlocal news_df
        pb_pull.visible = True
        lbl_status.value = "正在拉取新闻..."
        page.update()

        def update_progress(current: int, total: int):
            pb_pull.value = current / total
            lbl_status.value = f"正在拉取新闻... ({current}/{total})"
            page.update()

        try:
            import collect_news
            # 使用滑动条的值作为 max_articles
            max_articles = int(slider_max_articles.value)
            collected_news = collect_news.fetch_news(
                progress_callback=update_progress, 
                max_articles=max_articles
            )
            news_df = pd.DataFrame(collected_news)
            # Convert "值" column to float when creating DataFrame
            if "值" in news_df.columns:
                news_df["值"] = pd.to_numeric(news_df["值"], errors='coerce').fillna(0.0)
            news_df.to_excel("news.xlsx", index=False)
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
        # Ensure value is float
        val = float(row.get("值", 0.0))
        display_val = val if left else 1 - val
        # 颜色插值：红(1,0,0) ←→ 蓝(0,1,1)
        r = int(200 * val)
        g = int(100 * (1 - val) + 20)
        b = int(200 * (1 - val))
        color_hex = f"#{r:02x}{g:02x}{b:02x}"

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
            border_radius=8,
            # 添加以下属性
            ink=True,  # 添加点击效果
            on_click=lambda e: show_news_detail(row),  # 点击时显示详情
            tooltip="点击查看详情"  # 鼠标悬停提示
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
            icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=40)
        else:
            verdict = "事件大概率不会发生"
            icon = ft.Icon(ft.Icons.CANCEL, color=ft.Colors.RED, size=40)

        def close_dlg(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("预测结果"),
            modal=True,
            content=ft.Column([
                icon,
                ft.Text(f"预测概率：{result:.2%}", size=18),
                ft.Text(verdict, size=16, weight=ft.FontWeight.BOLD)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            actions=[
                ft.TextButton("关闭", on_click=close_dlg)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        # page.show_dialog(dlg)
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ----------------------------------------------------------
    # 新闻详细内容
    # ----------------------------------------------------------
    def show_news_detail(row: pd.Series):
        """显示新闻详细内容的对话框"""
        def close_dlg(e):
            dlg.open = False
            page.update()

        content = ft.Column([
            ft.Text("发布时间：" + str(row.get("时间", "未知")), size=14),
            ft.Divider(height=1),
            ft.Text(str(row.get("内容", "无内容")), 
                   size=14,
                   selectable=True,  # 允许选择文本
                   text_align=ft.TextAlign.JUSTIFY),
        ], scroll=ft.ScrollMode.AUTO,  # 添加滚动支持
           expand=True)

        dlg = ft.AlertDialog(
            title=ft.Text(str(row.get("标题", "无标题")), size=16, weight=ft.FontWeight.BOLD),
            content=content,
            actions=[
                ft.TextButton("关闭", on_click=close_dlg)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            content_padding=20,
        )
        
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ----------------------------------------------------------
    # 按钮
    # ----------------------------------------------------------
    btn_pull   = ft.ElevatedButton("拉取新闻", on_click=pull_news, width=200)
    btn_predict= ft.ElevatedButton("预测",     on_click=predict,   width=200)

    # ----------------------------------------------------------
    # 滑动条：最大新闻数量
    # ----------------------------------------------------------
    slider_max_articles = ft.Slider(
        min=10,
        max=100,
        divisions=9,
        value=50,
        label="最大新闻数量：{value}",
        width=300,
        on_change=lambda e: setattr(slider_max_articles, "label", f"最大新闻数量：{int(e.control.value)}")
    )

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
                ft.Column([ft.Text("支持", size=16, weight=ft.FontWeight.BOLD), lv_left], expand=True),
                ft.VerticalDivider(width=1),
                ft.Column([ft.Text("反对", size=16, weight=ft.FontWeight.BOLD), lv_right], expand=True),
            ], expand=True),
            ft.Divider(height=1),
            ft.Row([
                ft.Text("设置", size=18, weight=ft.FontWeight.BOLD),
                slider_max_articles
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
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