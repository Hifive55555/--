# main.py
import flet as ft
import pandas as pd
import os
from typing import Dict, List, Tuple, Optional

NEWS_COLLECT_SCRIPT = "collect_news.py"
PREDICT_SCRIPT      = "predict.py"

# ----------------------------------------------------------
# GUI
# ----------------------------------------------------------
def main(page: ft.Page):
    page.title = "新闻事件多意向预测器"
    page.window_width  = 900
    page.window_height = 700
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # 【改动】全局状态
    news_df: pd.DataFrame = None
    intent_columns: List[str] = []       # 所有意向列名
    selected_intent: Optional[str] = None # 当前选中的意向

    # 左右两栏 ListView
    lv_left  = ft.ListView(expand=True, spacing=10, padding=10)
    lv_right = ft.ListView(expand=True, spacing=10, padding=10)

    # 进度条、状态文字
    pb_pull    = ft.ProgressBar(width=400, visible=False)
    pb_predict = ft.ProgressBar(width=400, visible=False)
    pb_train   = ft.ProgressBar(width=400, visible=False)  # 训练进度条
    lbl_status = ft.Text("", size=16, italic=True)

    # 【改动】顶部意向选择栏（横向 ListView）
    lv_intents = ft.ListView(
        expand=True,
        spacing=10,
        padding=ft.padding.only(top=8, bottom=8),
    )

    # ----------------------------------------------------------
    # 启动即加载
    # ----------------------------------------------------------
    def load_excel_on_start():
        nonlocal news_df, intent_columns, selected_intent
        try:
            import collect_news
        except ImportError:
            # Silently handle the missing module case
            news_df = None
            intent_columns = []
            selected_intent = None
            lbl_status.value = "请拉取新闻"
            page.update()
            return

        try:
            news_df = collect_news.get_current_news()
            if news_df is not None:
                # 自动识别意向列：除前三列外的所有数值列
                intent_columns = [
                    c for c in news_df.columns[3:]
                    if pd.api.types.is_numeric_dtype(news_df[c])
                ]
                if not intent_columns:
                    lbl_status.value = "未检测到意向列（标题、时间、内容之后需为数值列）"
                else:
                    selected_intent = intent_columns[0]  # 默认第一个
                    lbl_status.value = f"已加载 {len(news_df)} 条历史新闻，共 {len(intent_columns)} 个意向"
                    refresh_intent_bar()
                    show_news()
                collect_news.update_models()  # 更新模型
            else:
                lbl_status.value = "请拉取新闻"
        except Exception as ex:
            news_df = None
            intent_columns = []
            selected_intent = None
            lbl_status.value = "请拉取新闻"
        page.update()

    # ----------------------------------------------------------
    # 拉取新闻
    # ----------------------------------------------------------
    def pull_news(e, force_refresh: bool = False):
        nonlocal news_df, intent_columns, selected_intent
        pb_pull.visible = True
        
        # Handle force refresh
        if force_refresh:
            try:
                import os
                if os.path.exists('news.xlsx'):
                    os.remove('news.xlsx')
                news_df = None
                intent_columns = []
                selected_intent = None
                lbl_status.value = "正在重新拉取新闻..."
            except Exception as ex:
                lbl_status.value = f"清除历史数据失败：{ex}"
                pb_pull.visible = False
                page.update()
                return
        else:
            lbl_status.value = "正在拉取新闻..."
        
        page.update()

        # Keep track of processed titles for UI updates
        seen_titles = set()
        if news_df is not None:
            seen_titles.update(news_df['标题'].tolist())
        total_new = 0

        def update_progress(current: int, total: int):
            pb_pull.value = current / total
            lbl_status.value = f"正在拉取新闻... (新增 {current}/{total})"
            page.update()

        def update_news(row_data: Dict):
            nonlocal news_df, total_new
            title = row_data.get('标题', '')
            
            # Skip if already displayed
            if title in seen_titles:
                return
                
            seen_titles.add(title)
            total_new += 1
            
            # Convert single row to DataFrame
            new_row = pd.DataFrame([row_data])
            
            # Update news_df
            if news_df is None:
                news_df = new_row
            else:
                news_df = pd.concat([news_df, new_row])
            
            # Update intent columns if needed
            nonlocal intent_columns, selected_intent
            if not intent_columns:
                intent_columns = [
                    c for c in news_df.columns[3:]
                    if pd.api.types.is_numeric_dtype(news_df[c])
                ]
                if intent_columns:
                    selected_intent = intent_columns[0]

            # Refresh display
            if selected_intent:
                refresh_intent_bar()
                show_news()

        try:
            import collect_news
            max_articles = int(slider_max_articles.value)
            news_df = collect_news.fetch_news(
                progress_callback=update_progress,
                news_callback=update_news,
                max_articles=max_articles
            )
            
            # Final update
            intent_columns = [
                c for c in news_df.columns[3:]
                if pd.api.types.is_numeric_dtype(news_df[c])
            ]
            if not intent_columns:
                raise ValueError("收集到的新闻没有意向列")
            selected_intent = intent_columns[0]
            lbl_status.value = f"已拉取 {total_new} 条新闻，共 {len(intent_columns)} 个意向"
            refresh_intent_bar()
            show_news()
        except Exception as ex:
            lbl_status.value = f"拉取失败：{ex}"
        finally:
            pb_pull.visible = False
            page.update()

    # ----------------------------------------------------------
    # 【改动】刷新顶部意向栏
    # ----------------------------------------------------------
    def refresh_intent_bar():
        if news_df is None or intent_columns == []:
            lv_intents.controls.clear()
            return
        # 计算每个意向的平均值（预测结果）
        avg_scores = {
            col: float(news_df[col].mean())
            for col in intent_columns
        }
        # 按均值降序排序
        sorted_intents = sorted(
            avg_scores.items(), key=lambda x: x[1], reverse=True)

        lv_intents.controls.clear()
        for col, avg in sorted_intents:
            # 颜色插值
            r = int(60 * avg)
            g = int(200 * avg + 20)
            b = int(200 * (1 - avg) + 20)
            color_hex = f"#{r:02x}{g:02x}{b:02x}"

            bar_width = max(4, int(avg * 200))
            
            is_selected = (col == selected_intent)
            btn = ft.Container(
                content=ft.Column([
                    ft.Text(col, size=14, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Container(
                            width=bar_width,
                            height=10,
                            bgcolor=color_hex,
                            border_radius=5
                        ),
                        ft.Text(f"{avg:.2f}", size=13, color=color_hex)
                    ], spacing=5)
                ], tight=True, alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.all(8),
                border=ft.border.all(2, ft.Colors.PRIMARY if is_selected else ft.Colors.GREY),
                border_radius=8,
                bgcolor=ft.Colors.PRIMARY_CONTAINER if is_selected else ft.Colors.TRANSPARENT,
                ink=True,
                on_click=lambda e, c=col: select_intent(c)
            )
            lv_intents.controls.append(btn)
        page.update()

    # 【改动】点击意向切换
    def select_intent(intent_col: str):
        nonlocal selected_intent
        selected_intent = intent_col
        refresh_intent_bar()   # 刷新选中样式
        show_news()            # 重新展示

    # ----------------------------------------------------------
    # 可视化展示
    # ----------------------------------------------------------
    def show_news():
        lv_left.controls.clear()
        lv_right.controls.clear()

        if news_df is None or news_df.empty or selected_intent is None:
            return

        # 使用当前意向列
        col = selected_intent
        if col not in news_df.columns:
            return

        # 构造临时列用于排序
        news_df["_score"] = news_df[col].apply(
            lambda v: v if v >= 0.5 else 1 - v)

        left_df  = news_df[news_df[col] >= 0.5].sort_values("_score", ascending=False)
        right_df = news_df[news_df[col] < 0.5].sort_values("_score", ascending=False)

        for _, row in left_df.iterrows():
            lv_left.controls.append(_build_card(row, left=True))
        for _, row in right_df.iterrows():
            lv_right.controls.append(_build_card(row, left=False))

        page.update()

    # ----------------------------------------------------------
    # 单条卡片 UI
    # ----------------------------------------------------------
    def _build_card(row: pd.Series, left: bool):
        col = selected_intent
        val = float(row.get(col, 0.0))
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
            ink=True,
            on_click=lambda e: show_news_detail(row),
            tooltip="点击查看详情"
        )

    # ----------------------------------------------------------
    # 预测事件（使用当前意向）
    # ----------------------------------------------------------
    def predict(e):
        if news_df is None or news_df.empty or selected_intent is None:
            lbl_status.value = "请先拉取新闻"
            page.update()
            return

        pb_predict.visible = True
        lbl_status.value = f"正在分类并预测 “{selected_intent}” ..."
        page.update()

        try:
            result = bayes_predict(news_df[selected_intent])
            show_result(result, selected_intent)
        except Exception as ex:
            lbl_status.value = f"预测失败：{ex}"
        finally:
            pb_predict.visible = False
            page.update()

    # 【改动】对话框标题增加意向名
    def show_result(result: float, intent_name: str):
        threshold = 0.70
        if result >= threshold:
            verdict = f"事件 “{intent_name}” 大概率会发生"
            icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=40)
        else:
            verdict = f"事件 “{intent_name}” 大概率不会发生"
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
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ----------------------------------------------------------
    # 新闻详细内容（保持不变）
    # ----------------------------------------------------------
    def show_news_detail(row: pd.Series):
        def close_dlg(e):
            dlg.open = False
            page.update()

        content = ft.Column([
            ft.Text("发布时间：" + str(row.get("时间", "未知")), size=14),
            ft.Divider(height=1),
            ft.Text(str(row.get("内容", "无内容")),
                   size=14,
                   selectable=True,
                   text_align=ft.TextAlign.JUSTIFY),
        ], scroll=ft.ScrollMode.AUTO, expand=True)

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
    # 训练模型
    # ----------------------------------------------------------
    def train_models(e):
        try:
            import train_news
            pb_train.visible = True
            lbl_status.value = "正在训练模型..."
            page.update()
            
            result = train_news.start_training()
            
            # 显示训练结果对话框
            def close_dlg(e):
                dlg.open = False
                page.update()
            
            dlg = ft.AlertDialog(
                title=ft.Text("训练结果"),
                content=ft.Column([
                    ft.Text(result, size=14, selectable=True)
                ], scroll=ft.ScrollMode.AUTO),
                actions=[ft.TextButton("关闭", on_click=close_dlg)],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            page.overlay.append(dlg)
            dlg.open = True
            lbl_status.value = "训练完成"
            
        except ImportError:
            lbl_status.value = "未找到训练模块"
        except Exception as ex:
            lbl_status.value = f"训练失败：{ex}"
        finally:
            pb_train.visible = False
            page.update()

    # ----------------------------------------------------------
    # 按钮
    # ----------------------------------------------------------
    btn_pull   = ft.ElevatedButton("拉取新闻", on_click=pull_news, width=200)
    btn_predict= ft.ElevatedButton("预测",     on_click=predict,   width=200)
    btn_train  = ft.ElevatedButton(
        "训练模型",
        on_click=train_models,
        width=200,
        bgcolor=ft.Colors.AMBER,
        color=ft.Colors.BLACK
    )
    btn_pull_refresh = ft.ElevatedButton(
        "覆盖拉取", 
        on_click=lambda e: pull_news(e, force_refresh=True),
        width=200,
        bgcolor=ft.Colors.RED_400,
        color=ft.Colors.WHITE,
    )

    # ----------------------------------------------------------
    # 滑动条：最大新闻数量
    # ----------------------------------------------------------
    def update_slider_label(e):
        slider_max_articles.label = f"最大新闻数量：{int(e.control.value)}"
        page.update()
    slider_max_articles = ft.Slider(
        min=10,
        max=100,
        divisions=9,
        value=50,
        label="最大新闻数量：{value}",
        width=300,
        on_change=update_slider_label
    )

    # ----------------------------------------------------------
    # 页面布局
    # ----------------------------------------------------------
    page.add(
        ft.Column([
            ft.Row([btn_pull, btn_pull_refresh, btn_predict, btn_train], 
                  alignment=ft.MainAxisAlignment.CENTER),
            pb_pull,
            pb_predict,
            pb_train,
            lbl_status,
            ft.Divider(height=1),
            ft.Row([
                ft.Column([ft.Text("意向选择", size=16, weight=ft.FontWeight.BOLD), lv_intents], expand=1),
                ft.VerticalDivider(width=1),
                ft.Column([ft.Text("支持", size=16, weight=ft.FontWeight.BOLD), lv_left], expand=2),
                ft.VerticalDivider(width=1),
                ft.Column([ft.Text("反对", size=16, weight=ft.FontWeight.BOLD), lv_right], expand=2),
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

# ----------------------------------------------------------
# 预测逻辑（保持不变）
# ----------------------------------------------------------
def bayes_predict(values: pd.Series) -> float:
    if values.empty:
        return 0.5
    return float(values.mean())

# ----------------------------------------------------------
# 入口
# ----------------------------------------------------------
if __name__ == "__main__":
    ft.app(target=main)