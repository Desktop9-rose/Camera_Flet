import flet as ft
from datetime import datetime
import asyncio
import os


# 本地环境: pip install flet==0.23.2

def main(page: ft.Page):
    # 1. 基础设置 (修复弃用警告)
    page.title = "Flet相机 (v0.23.2)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.bgcolor = ft.colors.WHITE

    # 新版写法: page.window.width
    page.window.width = 400
    page.window.height = 800

    # 2. 状态管理
    class AppState:
        camera = None

    state = AppState()

    # 3. UI 控件
    status_txt = ft.Text("系统就绪", color=ft.colors.BLUE_GREY_700)
    img_preview = ft.Image(visible=False, height=300, fit=ft.ImageFit.CONTAIN)

    # 相机容器
    camera_container = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.icons.CAMERA_ALT, size=50, color=ft.colors.GREY_300),
                ft.Text("点击下方按钮启动", color=ft.colors.GREY_400)
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
        status_txt.value = "正在连接相机..."
        status_txt.update()

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

            status_txt.value = "✅ 相机运行中"
            status_txt.update()

            btn_main.text = "立即拍照"
            btn_main.icon = ft.icons.CAMERA
            btn_main.bgcolor = ft.colors.GREEN
            btn_main.on_click = take_picture_task
            btn_main.update()

        except Exception as e:
            status_txt.value = f"相机初始化错误: {e}"
            status_txt.update()

    async def take_picture_task(e):
        if not state.camera:
            return

        status_txt.value = "📸 拍摄中..."
        status_txt.update()

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"IMG_{timestamp}.jpg"

            await state.camera.take_picture_async(filename)
            await asyncio.sleep(0.5)

            img_preview.src = filename
            img_preview.visible = True
            img_preview.src += f"?v={timestamp}"

            status_txt.value = f"✅ 已保存: {filename}"
            page.update()

        except Exception as e:
            status_txt.value = f"拍摄失败: {e}"
            page.update()

    # 5. 权限处理
    def on_permission(e):
        print(f"Permission Status: {e.status}")
        if e.status == "granted" or e.status == ft.PermissionStatus.GRANTED:
            asyncio.create_task(init_camera_task())
        else:
            status_txt.value = f"❌ 权限被拒绝: {e.status}"
            status_txt.update()

    # 【关键修复】使用属性赋值法，避免 TypeError
    # 这种写法在 0.21 - 0.24 版本中都是安全的
    try:
        perm_handler = ft.PermissionHandler()
        perm_handler.on_status_change = on_permission
        page.overlay.append(perm_handler)
    except AttributeError:
        # 如果本地版本实在太乱导致没有 PermissionHandler，提示用户
        status_txt.value = "错误: 您的 Flet 版本不支持权限控件，请安装 flet==0.23.2"
        page.update()
        return

    def on_start_click(e):
        status_txt.value = "请求权限中..."
        status_txt.update()
        # 直接调用实例的方法
        perm_handler.request_permission(ft.PermissionType.CAMERA)

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
                img_preview
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
        )
    )


if __name__ == "__main__":
    ft.app(target=main)