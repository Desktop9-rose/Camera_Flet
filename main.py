import flet as ft
from datetime import datetime
import asyncio
import os
import traceback


# 必须环境: pip install flet==0.23.2

def main(page: ft.Page):
    # 错误捕获兜底，防止白屏
    try:
        # 1. 基础设置
        page.title = "Flet相机 (v0.23.2)"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.bgcolor = ft.colors.WHITE
        # 适配新版 API，防止警告
        page.window.width = 400
        page.window.height = 800

        # 2. 状态管理
        class AppState:
            camera = None

        state = AppState()

        # 3. UI 控件
        status_txt = ft.Text("初始化中...", color=ft.colors.BLUE_GREY_700, size=16)
        log_view = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=100)  # 屏幕日志区

        def log(msg):
            print(msg)
            status_txt.value = msg
            status_txt.update()
            log_view.controls.insert(0, ft.Text(f"{datetime.now().strftime('%H:%M:%S')}: {msg}", size=12))
            if len(log_view.controls) > 20:
                log_view.controls.pop()
            log_view.update()

        img_preview = ft.Image(visible=False, height=300, fit=ft.ImageFit.CONTAIN)

        # 相机容器
        camera_container = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.CAMERA_ALT, size=50, color=ft.colors.GREY_300),
                    ft.Text("准备就绪", color=ft.colors.GREY_400)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            height=300,
            bgcolor=ft.colors.BLACK12,
            border_radius=12,
            alignment=ft.alignment.center
        )

        # 4. 业务逻辑
        async def init_camera_task():
            log("正在连接相机...")
            await asyncio.sleep(0.5)

            try:
                # Flet 0.23.2 标准相机控件
                state.camera = ft.Camera(
                    expand=True,
                    fit=ft.ImageFit.COVER,
                    visible=True
                )

                camera_container.content = state.camera
                camera_container.update()

                log("✅ 相机控件已挂载")

                btn_main.text = "立即拍照"
                btn_main.icon = ft.icons.CAMERA
                btn_main.bgcolor = ft.colors.GREEN
                btn_main.on_click = take_picture_task
                btn_main.update()

            except Exception as e:
                log(f"相机初始化错误: {e}")

        async def take_picture_task(e):
            if not state.camera:
                log("错误: 相机未初始化")
                return

            log("📸 拍摄中...")

            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"IMG_{timestamp}.jpg"

                await state.camera.take_picture_async(filename)
                await asyncio.sleep(0.5)

                img_preview.src = filename
                img_preview.visible = True
                img_preview.src += f"?v={timestamp}"

                log(f"✅ 已保存: {filename}")
                page.update()

            except Exception as e:
                log(f"拍摄失败: {e}")
                page.update()

        # 5. 权限处理
        def on_permission(e):
            log(f"权限回调: {e.status}")
            # 兼容不同类型的返回值
            status_str = str(e.status).lower()
            if "granted" in status_str:
                asyncio.create_task(init_camera_task())
            else:
                log(f"❌ 权限被拒绝")

        # 稳健的权限处理器初始化
        try:
            perm_handler = ft.PermissionHandler()
            perm_handler.on_status_change = on_permission
            page.overlay.append(perm_handler)
            log("权限控件加载成功")
        except Exception as e:
            log(f"权限控件加载失败: {e}")

        def on_start_click(e):
            log("正在请求相机权限...")
            try:
                perm_handler.request_permission(ft.PermissionType.CAMERA)
            except Exception as e:
                log(f"请求失败: {e}")

        # 6. 界面布局
        btn_main = ft.ElevatedButton(
            text="启动相机",
            icon=ft.icons.POWER_SETTINGS_NEW,
            on_click=on_start_click,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            height=50,
            width=200
        )

        page.add(
            ft.Column(
                [
                    ft.Text("Flet 相机 (v0.23.2)", size=20, weight="bold"),
                    status_txt,
                    ft.Divider(),
                    camera_container,
                    ft.Container(height=20),
                    btn_main,
                    ft.Divider(),
                    ft.Text("运行日志:"),
                    ft.Container(content=log_view, height=100, bgcolor=ft.colors.GREY_100),
                    ft.Divider(),
                    img_preview
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO
            )
        )

    except Exception as e:
        # 致命错误全屏显示
        page.clean()
        page.add(ft.Text(f"CRITICAL ERROR:\n{traceback.format_exc()}", color="red", size=20))


if __name__ == "__main__":
    ft.app(target=main)