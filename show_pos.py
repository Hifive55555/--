import flet as ft
import flet.canvas as cv
import json
from copy import deepcopy
from disposition2 import calculate

COLOR_MAP = {str(i): c for i, c in enumerate([
    ft.Colors.BLUE, ft.Colors.RED, ft.Colors.GREEN,
    ft.Colors.PURPLE, ft.Colors.ORANGE, ft.Colors.TEAL,
    ft.Colors.PINK, ft.Colors.AMBER], start=1)}

DEFAULT_DATA = {
    'self_ship_list': {'1': 3, '2': 2, '3': 10, '4': 0},
    'self_r': {'1': 2, '2': 3, '3': 4, '4': 1},
    'ship_dic': ['1', '2', '3', '4'],
    'ship_name': {'1': '驱逐舰', '2': '护卫舰', '3': '巡洋舰', '4': '航母'}  # 新增
}

def next_id(existing):
    i = 1
    while str(i) in existing:
        i += 1
    return str(i)

def main(page: ft.Page):
    page.title = "船只布势可视化"
    page.window_width = 900
    page.window_height = 800
    config = deepcopy(DEFAULT_DATA)

    config_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
    grid_container = ft.Column(spacing=0)
    legend_container = ft.Row(spacing=10, wrap=True)

    result = ft.Text()      # 用来显示解析后的结果（调试用）
    def parse_text(e):
        raw: str = e.control.value          # 获取文本框全部内容
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]  # 去掉空行
        data = [ln.split(',') for ln in lines]  # 每行按逗号切分
        # 去掉每个字段两端空白
        data = [[col.strip() for col in row] for row in data]
        result.value = str(data)            # 更新显示
        page.update()
    text_box = ft.TextField(
        multiline=True,
        min_lines=5,
        max_lines=10,
        hint_text="15:00, A, 000\n15:00, B, 001\n16:00, A, 000",
        on_change=parse_text,
    )

    # ---------------- 同步 UI ----------------
    def sync_ui_to_config():
        config_column.controls.clear()
        for tid in config['ship_dic']:
            row = ft.Row(
                [
                    ft.Text(f"{tid}", width=30),  # 仅显示 id，完全不可改
                    ft.TextField(label="名称",
                                 value=config['ship_name'][tid],
                                 width=100,
                                 on_change=lambda e, t=tid: update_name(t, e.control.value)),
                    ft.TextField(label="数量",
                                 value=str(config['self_ship_list'][tid]),
                                 width=60,
                                 on_change=lambda e, t=tid: update_count(t, e.control.value)),
                    ft.TextField(label="半径",
                                 value=str(config['self_r'][tid]),
                                 width=60,
                                 on_change=lambda e, t=tid: update_radius(t, e.control.value)),
                    ft.IconButton(icon=ft.Icons.DELETE,
                                  on_click=lambda _, t=tid: remove_type(t))
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
            config_column.controls.append(row)

        config_column.controls.append(
            ft.ElevatedButton("添加船只类型", icon=ft.Icons.ADD, on_click=add_type)
        )
        page.update()

    # ---------------- 事件 ----------------
    def update_name(tid, val):
        config['ship_name'][tid] = val
        build_legend()

    def update_count(tid, val):
        try:
            config['self_ship_list'][tid] = int(val)
        except ValueError:
            pass

    def update_radius(tid, val):
        try:
            config['self_r'][tid] = int(val)
        except ValueError:
            pass

    def remove_type(tid):
        config['self_ship_list'].pop(tid, None)
        config['self_r'].pop(tid, None)
        config['ship_name'].pop(tid, None)
        config['ship_dic'].remove(tid)
        sync_ui_to_config()
        build_legend()
        build_grid([])

    def add_type(_):
        new_id = next_id(config['ship_dic'])
        config['ship_dic'].append(new_id)
        config['self_ship_list'][new_id] = 1
        config['self_r'][new_id] = 1
        config['ship_name'][new_id] = f'船只{new_id}'
        sync_ui_to_config()

    # ---------------- 生成 ----------------
    def on_generate(_):
        try:
            positions = calculate(deepcopy(config))
            print("返回坐标数:", len(positions))   # 看看到底有没有数据
            build_grid(positions)
            build_legend()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"错误：{ex}"))
            page.snack_bar.open = True
            page.update()

    def build_grid(positions):
        CELL = 50                # 单元格像素
        max_x, max_y = 10, 10    # 网格逻辑大小
        grid_size = max(max_x, max_y)

        # 1. 计算每个方格的填充颜色 / 文本 / 数量
        cell_color = [[ft.Colors.WHITE10] * grid_size for _ in range(grid_size)]
        cell_num = [[0] * grid_size for _ in range(grid_size)]

        for tid, x, y in positions:
            tid = str(tid)
            xi, yi = int(x / 5 + 5), int(y / 5 + 5)  # 向下取整
            if 0 <= xi < grid_size and 0 <= yi < grid_size:
                cell_color[yi][xi] = COLOR_MAP.get(tid, ft.Colors.WHITE10)
                cell_num[yi][xi] += 1

        # 2. 构造 Canvas 的绘图指令
        paint_stroke = ft.Paint(style=ft.PaintingStyle.STROKE, color=ft.Colors.BLACK)
        shapes = []

        # 先画所有矩形和边框
        for y in range(2, grid_size - 2):
            for x in range(2, grid_size - 2):
                left, top = x * CELL, y * CELL
                # 填充矩形
                shapes.append(
                    cv.Rect(
                        left, top, CELL, CELL,
                        paint=ft.Paint(color=cell_color[y][x], style=ft.PaintingStyle.FILL)
                    )
                )
                # 边框
                shapes.append(
                    cv.Rect(
                        left, top, CELL, CELL,
                        paint=paint_stroke
                    )
                )
                if cell_num[y][x] > 0:
                    # 居中绘制数字
                    shapes.append(
                            cv.Text(
                                x * CELL + CELL / 2,
                                y * CELL + CELL / 2,
                                f'{cell_num[y][x]}',
                                alignment=ft.alignment.center,
                                style=ft.TextStyle(size=14, color=ft.Colors.WHITE)
                            )
                        )

        # 在最外围绘制大网格 2*CELL
        for y in range(0, grid_size, 2):
            for x in range(0, grid_size, 2):
                # 在中间就跳过
                if 2 <= x < grid_size - 2 and 2 <= y < grid_size - 2:
                    continue
                left, top = x * CELL, y * CELL
                # 在四个小格中查找是否有cell_color不是白色的，并统计数量
                color = ft.Colors.WHITE10
                num = 0
                for dy in range(2):
                    for dx in range(2):
                        if y + dy < grid_size and x + dx < grid_size:
                            if cell_color[y + dy][x + dx] != ft.Colors.WHITE10:
                                color = cell_color[y + dy][x + dx]
                                num += cell_num[y + dy][x + dx]
                shapes.append(
                    cv.Rect(
                        left, top, CELL * 2, CELL * 2,
                        paint=ft.Paint(color=color, stroke_width=2)
                    )
                )
                shapes.append(
                    cv.Rect(
                        left, top, CELL * 2, CELL * 2,
                        paint=paint_stroke
                    )
                )
                if num > 0:
                    shapes.append(
                        cv.Text(
                            x * CELL + CELL, y * CELL + CELL,
                            f'{num}',
                            alignment=ft.alignment.center,
                            style=ft.TextStyle(size=16, color=ft.Colors.WHITE)
                        )
                    )
        
        # 绘制坐标轴
        for i in range(grid_size):
            if i % 2 == 0:
                # 横轴
                shapes.append(
                    cv.Text(
                        i * CELL, grid_size * CELL + 15,
                        f'{(i - 5) * 5}',
                        alignment=ft.alignment.center,
                        style=ft.TextStyle(size=12, color=ft.Colors.BLUE_100)
                    )
                )
                # 竖轴
                shapes.append(
                    cv.Text(
                        grid_size * CELL + 15, i * CELL,
                        f'{(grid_size - i - 5) * 5}',
                        alignment=ft.alignment.center,
                        style=ft.TextStyle(size=12, color=ft.Colors.BLUE_100)
                    )
                )
        
        # 绘制坐标轴线
        shapes.append(
            cv.Line(0, 5 * CELL, grid_size * CELL, 5 * CELL, paint=ft.Paint(color=ft.Colors.BLUE_200, stroke_width=1))
        )
        shapes.append(
            cv.Line(5 * CELL, 0, 5 * CELL, grid_size * CELL, paint=ft.Paint(color=ft.Colors.BLUE_200, stroke_width=1))
        )

        # 在右下角显示单位文字
        shapes.append(
            cv.Text(
                grid_size * CELL + 15, grid_size * CELL + 15,
                "海里",
                alignment=ft.alignment.center,
                style=ft.TextStyle(size=12, color=ft.Colors.BLUE_100)
            )
        )

        # 以12和24为半径画两个同心圆
        shapes.append(
            cv.Circle(
                5 * CELL, 5 * CELL, 12 * CELL / 5,
                paint=ft.Paint(color=ft.Colors.BLUE_100, stroke_width=1, style=ft.PaintingStyle.STROKE, blend_mode=ft.BlendMode.DARKEN)
            )
        )
        shapes.append(
            cv.Circle(
                5 * CELL, 5 * CELL, 24 * CELL / 5,
                paint=ft.Paint(color=ft.Colors.BLUE_100, stroke_width=1, style=ft.PaintingStyle.STROKE, blend_mode=ft.BlendMode.DARKEN)
            )
        )

        # 3. 把 Canvas 放进 grid_container
        grid_container.controls = [cv.Canvas(
            shapes,
            width=CELL * grid_size,
            height=CELL * grid_size,
        )]
        page.update()

    # ---------------- 图例 ----------------
    def build_legend():
        legend_container.controls.clear()
        for tid in config['ship_dic']:
            color = COLOR_MAP.get(str(tid), ft.Colors.GREY)   # 保险起见再转一次
            name = config['ship_name'][str(tid)]
            legend_container.controls.append(
                ft.Row([
                    ft.Container(width=20, height=20, bgcolor=color),
                    ft.Text(f"{tid} - {name}")
                ])
            )
        page.update()

    # ---------------- 初始化 ----------------
    sync_ui_to_config()
    build_legend()

    page.add(
        ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("船只配置", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row([ft.Text("ID", width=30, weight=ft.FontWeight.BOLD),
                            ft.Text("名称", width=100, weight=ft.FontWeight.BOLD),
                            ft.Text("数量", width=60, weight=ft.FontWeight.BOLD),
                            ft.Text("半径", width=60, weight=ft.FontWeight.BOLD)]),
                    config_column,
                    ft.Divider(),
                    text_box,
                    result
                ], spacing=10),
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY),
                width=400
            ),
            ft.Column([
                ft.Text("船只布势图", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column([grid_container], scroll=ft.ScrollMode.AUTO),
                    border=ft.border.all(1, ft.Colors.BLACK),
                    padding=10,
                    width=550,
                    height=550
                ),
                ft.Divider(),
                ft.ElevatedButton("生成布势图", on_click=on_generate)
            ]),
            ft.Column([
                ft.Text("图例", size=18, weight=ft.FontWeight.BOLD),
                legend_container
            ], expand=True)
        ], expand=True)
    )

ft.app(target=main)