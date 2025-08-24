import flet as ft
import json
from disposition import calculate

# 船只类型颜色映射
COLOR_MAP = {
    '1': ft.Colors.BLUE,
    '2': ft.Colors.RED,
    '3': ft.Colors.GREEN,
    '4': ft.Colors.PURPLE
}

def main(page: ft.Page):
    page.title = "船只布势可视化"
    page.window_width = 800
    page.window_height = 700

    # 输入框默认值
    default_data = {
        'self_ship_list': {'1': 3, '2': 2, '3': 10, '4': 0},
        'self_r': {'1': 2, '2': 3, '3': 4, '4': 1},
        'ship_dic': ['1', '2', '3', '4']
    }

    # 输入框
    input_field = ft.TextField(
        multiline=True,
        value=json.dumps(default_data, indent=4),
        width=600,
        height=200
    )

    # 网格容器
    grid_container = ft.Column()

    # 图例容器
    legend_container = ft.Row(spacing=10)

    def build_legend(ship_dic):
        legend_container.controls.clear()
        for ship_type in ship_dic:
            color = COLOR_MAP.get(ship_type, ft.Colors.GREY)
            legend_container.controls.append(
                ft.Row([
                    ft.Container(width=20, height=20, bgcolor=color),
                    ft.Text(f"类型 {ship_type}")
                ])
            )
        page.update()

    def build_grid(positions, ship_dic):
        for pos in positions:
            pos[1] = pos[1] / 5 + 5  # x 坐标偏移和缩放
            pos[2] = pos[2] / 5 + 5  # y 坐标偏移和缩放
        max_x = 10
        max_y = 10
        print(positions)

        # max_x = max([int(round(pos[1])) for pos in positions]) if positions else 0
        # max_y = max([int(round(pos[2])) for pos in positions]) if positions else 0

        grid_size = max(max_x, max_y) + 1
        grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]

        for ship_type, x, y in positions:
            xi = int(round(x))
            yi = int(round(y))
            if 0 <= xi < grid_size and 0 <= yi < grid_size:
                grid[yi][xi] = ship_type

        grid_container.controls.clear()
        for row in reversed(grid):
            row_controls = []
            for cell in row:
                color = COLOR_MAP.get(cell, ft.Colors.WHITE)
                row_controls.append(
                    ft.Container(
                        width=30,
                        height=30,
                        bgcolor=color,
                        border=ft.border.all(1, ft.Colors.BLACK)
                    )
                )
            grid_container.controls.append(ft.Row(row_controls, spacing=-0))
        page.update()

    def on_generate(e):
        try:
            data = json.loads(input_field.value)
            result = calculate(data)
            build_grid(result, data['ship_dic'])
            build_legend(data['ship_dic'])
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"错误：{ex}"))
            page.snack_bar.open = True
            page.update()

    # 页面布局
    page.add(
        ft.Row([
            ft.Column([
                ft.Text("请输入船只数据（JSON格式）："),
                input_field,
                ft.ElevatedButton("生成", on_click=on_generate),
            ]),
            ft.Column([
                ft.Text("船只布势图："),
                ft.Container(
                    content=ft.Column([grid_container], scroll=ft.ScrollMode.AUTO),
                    border=ft.border.all(1, ft.Colors.BLACK),
                    padding=10
                ),
                ft.Divider(),
                ft.Text("图例："),
                legend_container
            ])
        ], expand=True),
    )

ft.app(target=main)