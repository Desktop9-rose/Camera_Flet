import flet as ft
from datetime import datetime
import asyncio
import traceback


def main(page: ft.Page):
    # 全局错误捕获：防止白屏
    try:
        # --- 1. 基础页面设置 ---
        page.title = "Flet相机"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.bgcolor = ft.Colors.WHITE
        # 强制竖屏布局
        page.window_width = 400
        page.window_height = 800

        # --- 2. 状态管理 ---
        class AppState:
            camera = None

        state = AppState()

        # UI 组件引用
        status_text = ft.Text("系统检查中...", size=16, color=ft.Colors.BLUE_GREY_700)
        preview_image = ft.Image(visible=False, height=200, fit=ft.ImageFit.CONTAIN)

        # --- 3. 核心功能函数 ---

        async def init_camera_task(e=None):
            """直接尝试启动相机，不使用 PermissionHandler"""
            status_text.value = "正在连接相机硬件..."
            status_text.update()

            await asyncio.sleep(0.5)

            try:
                # 创建相机控件
                # 在 Flet 新版中，只要 Manifest 权限正确，
                # 挂载 Camera 控件时系统底层会处理连接
                state.camera = ft.Camera(
                    expand=True,
                    fit=ft.ImageFit.COVER,
                    visible=True,
                    # 尝试强制指定后置摄像头
                    camera_id=0
                )

                camera_container.content = state.camera
                camera_container.update()

                # 更新按钮
                btn_start.visible = False
                btn_capture.disabled = False
                page.update()

                status_text.value = "✅ 相机运行中"
                status_text.update()

            except Exception as ex:
                status_text.value = f"相机启动异常: {ex}"
                status_text.update()

        async def capture_photo(e):
            if not state.camera:
                return

            status_text.value = "📸 正在处理图像..."
            status_text.update()

            try:
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"IMG_{timestamp}.jpg"

                # 拍照
                await state.camera.take_picture_async(filename)

                # 稍作等待
                await asyncio.sleep(0.5)

                # 更新预览
                preview_image.src = filename
                preview_image.visible = True
                preview_image.src += f"?v={timestamp}"  # 刷新缓存

                status_text.value = f"✅ 已保存: {filename}"
                page.update()

            except Exception as ex:
                status_text.value = f"❌ 拍摄错误: {ex}"
                page.update()

        # --- 4. UI 布局 ---

        camera_container = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.CAMERA_ALT, size=50, color=ft.Colors.GREY_300),
                    ft.Text("点击下方按钮启动", color=ft.Colors.GREY_400)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            height=300,
            bgcolor=ft.Colors.BLACK12,
            border_radius=12,
            alignment=ft.alignment.center,
        )

        # 按钮
        btn_start = ft.ElevatedButton(
            "启动相机",
            icon=ft.Icons.POWER_SETTINGS_NEW,
            on_click=init_camera_task,
            bgcolor=ft.Colors.BLUE,
            color=ft.Colors.WHITE,
            height=50,
            width=200
        )

        btn_capture = ft.ElevatedButton(
            "立即拍照",
            icon=ft.Icons.CAMERA,
            on_click=capture_photo,
            disabled=True,
            bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE,
            height=50,
            width=200
        )

        # 组装页面
        page.add(
            ft.Column([
                ft.Container(
                    content=ft.Text("Flet 极简相机", size=24, weight=ft.FontWeight.BOLD),
                    alignment=ft.alignment.center,
                    padding=10
                ),
                ft.Container(status_text, alignment=ft.alignment.center, padding=5),
                ft.Divider(),
                camera_container,
                ft.Container(height=20),  # 间距
                ft.Column([btn_start, btn_capture], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Divider(),
                ft.Text("照片预览:", weight=ft.FontWeight.BOLD),
                ft.Container(preview_image, alignment=ft.alignment.center, border_radius=8)
            ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO
            )
        )

    except Exception as e:
        # 致命错误兜底
        page.clean()
        page.add(
            ft.Text("❌ 严重错误", color=ft.Colors.RED, size=30),
            ft.Text(f"{traceback.format_exc()}", color=ft.Colors.RED_900)
        )
        page.update()


if __name__ == "__main__":
    ft.app(target=main)